import json
import os
import boto3
import urllib.parse
import datetime
import logging
import base64
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")

ES_ENDPOINT = os.environ.get("ES_ENDPOINT")  # e.g. https://search-photos-xxxx.us-east-1.es.amazonaws.com
INDEX_NAME = "photos"
OS_USER = os.environ.get("OS_USER")
OS_PASS = os.environ.get("OS_PASS")

http = urllib3.PoolManager()


def get_custom_labels_from_metadata(bucket, key):
    """
    Reads x-amz-meta-customLabels from S3. In head_object() the user
    metadata key will appear as 'customlabels' (lowercased, without prefix).
    """
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        metadata = head.get("Metadata", {})
        logger.info(f"Metadata for {bucket}/{key}: {metadata}")
        custom_labels_str = metadata.get("customlabels")
        if not custom_labels_str:
            return []
        labels = [l.strip().lower() for l in custom_labels_str.split(",") if l.strip()]
        logger.info(f"Custom labels: {labels}")
        return labels
    except Exception as e:
        logger.error(f"Error reading metadata for {bucket}/{key}: {e}")
        return []


def get_rekognition_labels(bucket, key):
    try:
        resp = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=10,
            MinConfidence=70,
        )
        labels = [lbl["Name"].lower() for lbl in resp.get("Labels", [])]
        logger.info(f"Rekognition labels for {bucket}/{key}: {labels}")
        return labels
    except Exception as e:
        logger.error(f"Error calling Rekognition for {bucket}/{key}: {e}")
        return []


def index_document_to_es(doc):
    if not ES_ENDPOINT:
        logger.error("ES_ENDPOINT not set")
        return

    url = f"{ES_ENDPOINT}/{INDEX_NAME}/_doc"
    headers = {"Content-Type": "application/json"}

    if OS_USER and OS_PASS:
        token = base64.b64encode(f"{OS_USER}:{OS_PASS}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"

    body = json.dumps(doc)

    try:
        resp = http.request("POST", url, body=body, headers=headers)
        logger.info(f"ES status: {resp.status}, body: {resp.data[:300]}")
        if resp.status not in (200, 201):
            logger.error(f"Failed to index doc into ES: {resp.status} {resp.data}")
    except Exception as e:
        logger.error(f"Error indexing document to ES: {e}")


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        logger.info(f"Processing file: s3://{bucket}/{key}")

        rekog_labels = get_rekognition_labels(bucket, key)
        custom_labels = get_custom_labels_from_metadata(bucket, key)

        # de-duplicate, all lowercase
        all_labels = sorted(list({lbl for lbl in (rekog_labels + custom_labels)}))
        created_ts = datetime.datetime.utcnow().isoformat()

        doc = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": created_ts,
            "labels": all_labels,
        }

        logger.info(f"Document to index: {json.dumps(doc)}")
        index_document_to_es(doc)

    return {
        "statusCode": 200,
        "body": json.dumps("OK"),
    }
