import requests
import csv
import random
import logging
from datetime import datetime
import io
import boto3

logger = logging.getLogger(__name__)

def fetch_live_data(api_url, target_records, batch_size):
    """Fetches paginated data from the NYC Open Data API."""
    logger.info(f"Fetching {target_records} records from API...")
    raw_data = []
    offset = 0

    while len(raw_data) < target_records:
        params = {
            "$limit": batch_size,
            "$offset": offset,
            "$select": "camis,dba,boro,zipcode,cuisine_description,inspection_date,score,grade,violation_description,critical_flag"
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            raw_data.extend(batch)
            logger.info(f"Retrieved {len(raw_data)} records...")
            offset += batch_size
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            break

    return raw_data[:target_records]

def corrupt_and_upload_to_s3(api_data, s3_bucket, s3_key, aws_access, aws_secret, aws_region):
    """Injects dirt and streams directly to AWS S3 from memory."""
    logger.info("Injecting dirty data and preparing in-memory CSV...")
    
    processed_data = []
    headers = [
        "restaurant_id", "name", "borough", "zipcode", "category", 
        "inspection_date", "score", "grade", "violation_description", "critical_flag"
    ]

    for row in api_data:
        r_id = row.get("camis", "")
        name = row.get("dba", "Unknown")
        boro = row.get("boro", "Unknown")
        zipcode = row.get("zipcode", "")
        category = row.get("cuisine_description", "General")
        date_str = row.get("inspection_date", "2023-01-01T00:00:00.000")
        score = row.get("score", "")
        grade = row.get("grade", "")
        violation = row.get("violation_description", "None")
        critical = row.get("critical_flag", "Not Applicable")

        # Inject Dirt
        if random.random() < 0.1: name = name.lower()
        elif random.random() < 0.1: name = name.upper()
        if random.random() < 0.05: category = ""
        if random.random() < 0.05: zipcode = ""
        if random.random() < 0.08: score = ""
        if random.random() < 0.1: grade = ""

        try:
            dt_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
            format_choice = random.random()
            if format_choice < 0.6: final_date = dt_obj.strftime("%Y-%m-%d")
            elif format_choice < 0.8: final_date = dt_obj.strftime("%d/%m/%Y")
            else: final_date = dt_obj.strftime("%m-%d-%Y")
        except ValueError:
            final_date = date_str 

        processed_data.append([
            r_id, name, boro, zipcode, category, 
            final_date, score, grade, violation, critical
        ])

    # Inject Duplicates
    if processed_data:
        duplicates = random.choices(processed_data, k=400)
        processed_data.extend(duplicates)
        random.shuffle(processed_data)

    # Write to in-memory string buffer
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(headers)
    writer.writerows(processed_data)

    # Upload directly to S3
    logger.info(f"Connecting to AWS S3 to upload to bucket: {s3_bucket}")
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access,
            aws_secret_access_key=aws_secret,
            region_name=aws_region
        )
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=csv_buffer.getvalue()
        )
        logger.info(f"Successfully uploaded dataset to s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")