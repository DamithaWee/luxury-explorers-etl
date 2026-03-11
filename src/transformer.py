import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_data(df):
    """Applies data quality rules to clean the raw DataFrame."""
    logger.info("Starting Pandas data transformation...")
    
    initial_rows = len(df)

    # 1. Remove Duplicates
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_rows - len(df)} duplicate records.")

    # 2. Standardize Text & Casing
    df['name'] = df['name'].astype(str).str.title()
    df['category'] = df['category'].astype(str).str.title()
    df['borough'] = df['borough'].astype(str).str.title()

    # 3. Handle Missing Values (Null Imputation)
    df['category'] = df['category'].replace(["", "Nan", "None"], "Unknown").fillna("Unknown")
    df['zipcode'] = df['zipcode'].fillna("00000").astype(str).str.replace(".0", "", regex=False)
    df['grade'] = df['grade'].fillna("N/A")
    df['violation_description'] = df['violation_description'].fillna("No violation recorded")
    
    # 4. Clean Numeric Fields
    # Convert score to numeric, turning bad data into NaN, then fill with 0
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    # Ensure no negative scores (enforcing the DB constraint early)
    df.loc[df['score'] < 0, 'score'] = 0 

    # 5. Standardize Mixed Date Formats to ISO (YYYY-MM-DD)
    # format='mixed' is a Pandas superpower that automatically resolves US, UK, and ISO formats
    df['inspection_date'] = pd.to_datetime(df['inspection_date'], format='mixed', errors='coerce')
    
    # Drop rows where the date was so corrupted it couldn't be parsed
    before_date_drop = len(df)
    df = df.dropna(subset=['inspection_date'])
    df['inspection_date'] = df['inspection_date'].dt.strftime('%Y-%m-%d')
    if before_date_drop - len(df) > 0:
        logger.warning(f"Dropped {before_date_drop - len(df)} rows due to unparseable dates.")

    logger.info(f"Transformation complete. {len(df)} pristine records ready for the database.")
    return df