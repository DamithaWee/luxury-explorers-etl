import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import our ETL modules
from src.generator import fetch_live_data, corrupt_and_upload_to_s3
from src.extractor import extract_from_s3
from src.transformer import clean_data
from src.loader import get_db_connection, load_raw_staging, load_star_schema

# --- Setup Global Logging ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Main")

def run_ingestion():
    load_dotenv()
    api_url = os.getenv("API_URL")
    target_records = int(os.getenv("TARGET_RECORDS", 100)) # Note: Set low for testing, increase to 10500 later!
    batch_size = int(os.getenv("BATCH_SIZE", 1000))
    
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    aws_access = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    
    base_output = os.getenv("OUTPUT_FILE", "raw_restaurant_data.csv")
    filename = os.path.basename(base_output)
    name, ext = os.path.splitext(filename)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"raw/{name}_{timestamp}{ext}"

    logger.info("--- Starting Ingestion Pipeline ---")
    live_data = fetch_live_data(api_url, target_records, batch_size)
    
    if live_data:
        corrupt_and_upload_to_s3(
            api_data=live_data, s3_bucket=s3_bucket, s3_key=s3_key,
            aws_access=aws_access, aws_secret=aws_secret, aws_region=aws_region
        )
        logger.info("--- Ingestion Pipeline Completed Successfully ---")
        return s3_key  # <-- WE RETURN THE DYNAMIC KEY HERE
    else:
        logger.error("Failed to fetch data. Pipeline aborted.")
        return None

def run_etl_pipeline(dynamic_s3_key):
    load_dotenv()
    logger.info("=== Starting Data Engineering ETL Pipeline ===")

    s3_bucket = os.getenv("S3_BUCKET_NAME")
    aws_access = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")

    db_user = os.getenv("POSTGRES_USER")
    db_pass = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")

    # 2. Extract using the exact key we just generated
    raw_df = extract_from_s3(s3_bucket, dynamic_s3_key, aws_access, aws_secret, aws_region)
    if raw_df is None or raw_df.empty:
        logger.error("Extraction failed or returned empty data. Aborting pipeline.")
        sys.exit(1)

    # 3. Connect to Database
    engine = get_db_connection(db_user, db_pass, db_host, db_port, db_name)
    if not engine:
        sys.exit(1)

    # 4. Load (Staging / Bronze Zone)
    load_raw_staging(raw_df, engine)

    # 5. Transform
    clean_df = clean_data(raw_df)

    # 6. Load (Presentation / Gold Zone)
    load_star_schema(clean_df, engine)

    logger.info("=== ETL Pipeline Completed Successfully ===")

if __name__ == "__main__":
    # Step 1: Run Ingestion and capture the filename
    latest_s3_key = run_ingestion()
    
    # Step 2: If ingestion worked, immediately run the ETL using that exact filename
    if latest_s3_key:
        run_etl_pipeline(latest_s3_key)
    else:
        logger.error("Pipeline halted due to ingestion failure.")