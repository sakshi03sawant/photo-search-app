import os
import json
import logging
import base64
import re

import boto3
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- OpenSearch / ES config ---
ES_ENDPOINT = os.environ.get("ES_ENDPOINT")  # e.g. https://search-photos-xxxx.es.amazonaws.com
INDEX_NAME = "photos"
OS_USER = os.environ.get("OS_USER")
OS_PASS = os.environ.get("OS_PASS")

http = urllib3.PoolManager()

# --- Lex config ---
LEX_BOT_ID = os.environ.get("LEX_BOT_ID")
LEX_BOT_ALIAS_ID = os.environ.get("LEX_BOT_ALIAS_ID")
LEX_LOCALE_ID = os.environ.get("LEX_LOCALE_ID", "en_US")

lex_runtime = boto3.client("lexv2-runtime")


def call_lex_disambiguate(q: str, session_id: str):
    """
    Send the raw query text to Lex and try to extract the `keywords` slot.
    Returns a list of normalized keyword strings (lowercase).
    """
    if not (LEX_BOT_ID and LEX_BOT_ALIAS_ID and LEX_LOCALE_ID):
        logger.warning("Lex env vars not set, skipping Lex disambiguation")
        return []

    try:
        resp = lex_runtime.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId=LEX_LOCALE_ID,
            sessionId=session_id,
            text=q
        )
        logger.info("Lex response: %s", json.dumps(resp))

        interpretations = resp.get("interpretations", [])
        if not interpretations:
            return []

        # Take top interpretation
        top = interpretations[0]
        intent = top.get("intent", {})
        slots = intent.get("slots") or {}

        # Slot name might be "keywords" or "Keywords" depending on how you named it
        kw_slot = slots.get("keywords") or slots.get("Keywords")
        if not kw_slot:
            return []

        value_info = kw_slot.get("value") or {}
        raw_text = (
            value_info.get("interpretedValue")
            or value_info.get("originalValue")
        )

        if not raw_text:
            return []

        # split on spaces and commas into individual labels
        tokens = [
            t.strip().lower()
            for t in re.split(r"[,\s]+", raw_text)
            if t.strip()
        ]
        return tokens

    except Exception as e:
        logger.error("Error calling Lex: %s", e, exc_info=True)
        return []


def search_es_by_labels(labels):
    """
    Query the OpenSearch index for any photo that has at least one of the labels.
    """
    if not labels:
        return []

    # Bool.should terms query on labels array
    query = {
        "size": 50,
        "query": {
            "bool": {
                "should": [
                    {"terms": {"labels.keyword": labels}},
                    {"terms": {"labels": labels}}
                ],
                "minimum_should_match": 1
            }
        }
    }

    url = f"{ES_ENDPOINT}/{INDEX_NAME}/_search"
    body = json.dumps(query)
    headers = {"Content-Type": "application/json"}

    if OS_USER and OS_PASS:
        token = base64.b64encode(f"{OS_USER}:{OS_PASS}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"

    logger.info("OpenSearch request: %s", body)

    resp = http.request("GET", url, body=body, headers=headers)
    logger.info("OpenSearch status: %s, body: %s", resp.status, resp.data[:300])

    if resp.status != 200:
        logger.error("Search failed: %s %s", resp.status, resp.data)
        return []

    data = json.loads(resp.data.decode("utf-8"))
    hits = data.get("hits", {}).get("hits", [])

    results = []
    for h in hits:
        src = h.get("_source", {})
        results.append(
            {
                "objectKey": src.get("objectKey"),
                "bucket": src.get("bucket"),
                "createdTimestamp": src.get("createdTimestamp"),
                "labels": src.get("labels", []),
            }
        )
    return results


def extract_query_from_event(event):
    """
    Handle both API Gateway (GET /search?q=...) and a possible
    direct test event where you pass {"q": "..."}.
    """
    q = None

    # API Gateway HTTP
    qs = event.get("queryStringParameters") or {}
    if "q" in qs:
        q = qs.get("q")

    # Direct test payload
    if not q:
        q = event.get("q")

    # Lex direct invocation (if you ever wire Lambda to Lex as fulfillment)
    if not q and "inputTranscript" in event:
        q = event.get("inputTranscript")

    return (q or "").strip()


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    q = extract_query_from_event(event)
    if not q:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"results": [], "error": "Missing query 'q'"}),
        }

    # 1) Ask Lex to extract keywords
    session_id = getattr(context, "aws_request_id", "web-session")
    labels = call_lex_disambiguate(q, session_id=session_id)

    # 2) Fallback: if Lex didn’t give us anything, just split the raw query
    if not labels:
        labels = [
            t.strip().lower()
            for t in re.split(r"[,\s]+", q)
            if t.strip()
        ]

    # 3) Search ES
    results = search_es_by_labels(labels)

    # 4) Return API Gateway style response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"results": results}),
    }

