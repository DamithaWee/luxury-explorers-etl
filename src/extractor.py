import pandas as pd
import boto3
import io
import logging

logger = logging.getLogger(__name__)

def extract_from_s3(s3_bucket, s3_key, aws_access, aws_secret, aws_region):
    """Downloads a CSV from S3 directly into a Pandas DataFrame."""
    logger.info(f"Connecting to S3 to extract s3://{s3_bucket}/{s3_key}")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access,
            aws_secret_access_key=aws_secret,
            region_name=aws_region
        )
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        
        # Read the body of the file into a Pandas DataFrame
        csv_content = response['Body'].read()
        df = pd.read_csv(io.BytesIO(csv_content))
        
        logger.info(f"Successfully extracted {len(df)} rows from S3.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to extract file from S3: {e}")
        return None