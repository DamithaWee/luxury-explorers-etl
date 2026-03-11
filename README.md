# NYC Restaurant Health Inspections: ETL Pipeline

## Project Overview
This project is a fully automated, cloud-integrated Data Engineering ETL pipeline. It extracts live operational data from the NYC Department of Health Open Data API, intentionally introduces real-world data anomalies (for robust testing), streams the raw data to AWS S3, and processes it into a normalized Star Schema in a Dockerized PostgreSQL data warehouse.

The pipeline is built on the **Medallion Architecture (Bronze, Silver, Gold)**, ensuring data lineage, fault tolerance, and high-performance analytical querying.



## Tech Stack & Tools
* **Orchestration & ETL:** Python 3.10+ (`pandas`, `boto3`, `sqlalchemy`)
* **Cloud Storage:** Amazon Web Services (AWS S3)
* **Database:** PostgreSQL (Dockerized)
* **Containerization:** Docker & Docker Compose
* **Environment Management:** `python-dotenv`

## Data Architecture 

1. **Raw Layer (AWS S3):** * Data is extracted from the NYC Open Data API via pagination.
   * To simulate real-world conditions, the ingestion service injects "dirty" data (mixed date formats, nulls, duplicates, inconsistent casing).
   * The raw payload is streamed directly from memory into an AWS S3 bucket with a dynamic timestamp.
2. **Transformation Layer (PostgreSQL Staging):**
   * The pipeline pulls the raw CSV from S3.
   * Untouched data is loaded into a permissive staging schema (`transformation.nyc_inspections_staging`) in Postgres to preserve history.
   * Python Pandas cleans the data: handling null imputation, duplicate removal, enforcing numeric types, and standardizing ISO 8601 dates.
3. **Presentation Layer (PostgreSQL Persentation):**
   * The pristine data is upserted into a 3NF Star Schema optimized for BI tools.
   * **Fact Table:** `fact_inspection`
   * **Dimension Tables:** `dim_restaurant`, `dim_location`



## Setup & Installation

### 1. Prerequisites
* **Docker Desktop** installed and running.
* **Python 3.x** installed.
* An **AWS Account** with an S3 Bucket and IAM User (Least Privilege setup for S3 access).

### 2. Clone the Repository
```bash
git clone [https://github.com/yourusername/nyc-restaurant-etl.git](https://github.com/yourusername/nyc-restaurant-etl.git)
cd nyc-restaurant-etl
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your AWS credentials:
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your_s3_bucket_name

# Database Configuration
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=etl_password
POSTGRES_DB=nyc_health_data
DB_HOST=localhost
DB_PORT=5432

# API Configuration
API_URL="[https://data.cityofnewyork.us/resource/43nn-pn8j.json](https://data.cityofnewyork.us/resource/43nn-pn8j.json)"
TARGET_RECORDS=10500
BATCH_SIZE=1000
```

### 4. Start the PostgreSQL Database
```bash
docker-compose up -d
```

### 5. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 6. Start the Pipeline
Run the main ETL Pipeline script:
```bash
python main.py
```
Check the logs/ directory or the terminal output to monitor the pipeline's progress through extraction, S3 upload, transformation, and database loading

## Project Structure
```
nyc-restaurant-etl/
├── sql/                     # SQL schema and analytics queries
├── src/
│   ├── generator.py         # API extraction and S3 streaming
│   ├── transformation.py    # Pandas cleaning and staging
│   ├── loader.py            # Star Schema upsert logic
│   └── extractor.py         # AWS S3 extraction
├── .env                     # Environment variables
├── docker-compose.yml       # Docker setup for PostgreSQL
└── main.py                  # Pipeline orchestration
```

## Testing

The pipeline includes built-in data quality checks:
- **Duplicate Detection:** Prevents duplicate records in the staging area.
- **Type Enforcement:** Ensures numeric scores and valid dates.
- **Referential Integrity:** Validates foreign key relationships.

## Cloud Integration

All raw data is securely stored in AWS S3 with proper IAM least-privilege access. The data is organized by date, allowing for incremental backups and disaster recovery.

## Business Value

This pipeline provides:
- **Real-time Insights:** Monitor restaurant health trends as they happen.
- **Data Quality Assurance:** Clean, reliable data for decision-making.
- **Scalability:** Ready to handle millions of records with cloud infrastructure.
- **Historical Tracking:** Complete audit trail of all inspections.
