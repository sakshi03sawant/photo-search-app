// === CONFIG ===
// Use your deployed stage (you are using "prod2")
const API_BASE = "https://xsn3m3hlk2.execute-api.us-east-1.amazonaws.com/prod2";

// Your API key for the PhotoSearchPlan usage plan
// (this is the same key you used successfully with curl)
const API_KEY = "bhMocdaGLT1hLg2QZsw001o7eCAqG4El8aZirINe";

// === SEARCH LOGIC ===
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const resultsContainer = document.getElementById("results");
const resultsHeader = document.getElementById("results-header");
const errorMsg = document.getElementById("error-msg");

async function performSearch() {
  const q = (searchInput.value || "").trim();
  errorMsg.textContent = "";

  if (!q) {
    resultsHeader.textContent = "Please enter a query.";
    resultsContainer.innerHTML = "";
    return;
  }

  resultsHeader.textContent = `Searching for “${q}”…`;
  resultsContainer.innerHTML = "";

  try {
    const headers = {};
    if (API_KEY) headers["x-api-key"] = API_KEY;

    const resp = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`, {
      method: "GET",
      headers
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error("Search error:", resp.status, text);
      resultsHeader.textContent = "Search failed.";
      errorMsg.textContent = `Search failed (${resp.status}). See console for details.`;
      return;
    }

    const data = await resp.json();
    const results = data.results || [];

    if (!results.length) {
      resultsHeader.textContent = `No photos found for “${q}”.`;
      resultsContainer.innerHTML = "";
      return;
    }

    resultsHeader.textContent = `Found ${results.length} photo(s) for “${q}”.`;
    renderResults(results);
  } catch (err) {
    console.error(err);
    resultsHeader.textContent = "Search error.";
    errorMsg.textContent = "Search error – check browser console.";
  }
}

function renderResults(items) {
  resultsContainer.innerHTML = "";

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "photo-card";

    const row = document.createElement("div");
    row.className = "photo-row";

    const img = document.createElement("img");
    img.className = "photo-thumb";

    // Basic S3 object URL – works if bucket/object is public
    if (item.bucket && item.objectKey) {
      img.src = `https://${item.bucket}.s3.amazonaws.com/${encodeURIComponent(
        item.objectKey
      )}`;
      img.alt = item.objectKey;
    }

    const meta = document.createElement("div");
    meta.className = "photo-meta";

    const name = document.createElement("div");
    name.innerHTML = `<span class="label">Key:</span> ${item.objectKey || "-"}`;

    const bucket = document.createElement("div");
    bucket.innerHTML = `<span class="label">Bucket:</span> ${item.bucket || "-"}`;

    const created = document.createElement("div");
    created.innerHTML = `<span class="label">Created:</span> ${
      item.createdTimestamp || "-"
    }`;

    const labelsRow = document.createElement("div");
    labelsRow.className = "tags-row";

    (item.labels || []).forEach((l) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = l;
      labelsRow.appendChild(tag);
    });

    meta.appendChild(name);
    meta.appendChild(bucket);
    meta.appendChild(created);
    meta.appendChild(labelsRow);

    row.appendChild(img);
    row.appendChild(meta);

    card.appendChild(row);
    resultsContainer.appendChild(card);
  });
}

// Wire up search events
if (searchBtn) {
  searchBtn.addEventListener("click", (e) => {
    e.preventDefault();
    performSearch();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      performSearch();
    }
  });
}

// === UPLOAD LOGIC ===
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const customLabelsInput = document.getElementById("custom-labels");
const uploadStatus = document.getElementById("upload-status");

if (uploadForm) {
  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMsg.textContent = "";
    uploadStatus.textContent = "";

    if (!fileInput.files.length) {
      uploadStatus.textContent = "Please choose an image file.";
      return;
    }

    const file = fileInput.files[0];
    const objectKey = encodeURIComponent(file.name);
    const customLabels = (customLabelsInput.value || "").trim();

    uploadStatus.textContent = "Uploading…";

    try {
      const headers = {
        "Content-Type": file.type || "image/jpeg",
        "x-amz-meta-customLabels": customLabels
      };

      if (API_KEY) {
        headers["x-api-key"] = API_KEY;
      }

      const resp = await fetch(
        `${API_BASE}/photos?objectKey=${objectKey}`,
        {
          method: "PUT",
          headers,
          body: file
        }
      );

      if (!resp.ok) {
        const text = await resp.text();
        console.error("Upload failed:", resp.status, text);
        uploadStatus.textContent = `Upload failed (${resp.status}).`;
        errorMsg.textContent = "Upload failed – see console for details.";
        return;
      }

      uploadStatus.textContent =
        "Uploaded! Wait a few seconds, then try searching using one of your labels.";
      fileInput.value = "";
      customLabelsInput.value = "";
    } catch (err) {
      console.error(err);
      uploadStatus.textContent = "Upload error – see console.";
      errorMsg.textContent = "Upload error – check browser console.";
    }
  });
}

// Optional: focus search box on load
if (searchInput) {
  searchInput.focus();
}
