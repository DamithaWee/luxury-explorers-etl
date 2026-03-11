import pandas as pd
from sqlalchemy import create_engine, text
import logging

logger = logging.getLogger(__name__)

def get_db_connection(user, password, host, port, db_name):
    """Creates a SQLAlchemy engine for PostgreSQL."""
    engine_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    try:
        engine = create_engine(engine_url)
        logger.info(f"Successfully connected to PostgreSQL at {host}:{port}")
        return engine
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def load_raw_staging(df, engine):
    """Loads the untouched raw DataFrame into the staging layer."""
    logger.info("Loading raw data into transformation.nyc_inspections_staging...")
    # if_exists='replace' ensures we get a fresh staging table every time the pipeline runs
    df.to_sql('nyc_inspections_staging', engine, schema='transformation', if_exists='replace', index=False)
    logger.info("Raw staging load complete.")

def load_star_schema(clean_df, engine):
    """Splits the clean DataFrame and loads it into the presentation Star Schema."""
    logger.info("Loading cleaned data into the presentation Star Schema...")
    
    with engine.begin() as conn:
        # --- 1. Load dim_restaurant ---
        # Get unique restaurants
        dim_restaurant = clean_df[['restaurant_id', 'name', 'category']].drop_duplicates(subset=['restaurant_id'])
        dim_restaurant.to_sql('temp_dim_restaurant', conn, schema='presentation', if_exists='replace', index=False)
        
        # Merge temp table into actual dimension, updating names/categories if they changed
        conn.execute(text("""
            INSERT INTO presentation.dim_restaurant (restaurant_id, name, category)
            SELECT restaurant_id, name, category FROM presentation.temp_dim_restaurant
            ON CONFLICT (restaurant_id) DO UPDATE SET 
                name = EXCLUDED.name, 
                category = EXCLUDED.category;
        """))
        conn.execute(text("DROP TABLE presentation.temp_dim_restaurant;"))
        logger.info(f"Loaded {len(dim_restaurant)} unique restaurants into dim_restaurant.")

        # --- 2. Load dim_location ---
        # Get unique borough/zipcode combinations
        dim_location = clean_df[['borough', 'zipcode']].drop_duplicates()
        dim_location.to_sql('temp_dim_location', conn, schema='presentation', if_exists='replace', index=False)
        
        # Insert only new locations (ignore duplicates)
        conn.execute(text("""
            INSERT INTO presentation.dim_location (borough, zipcode)
            SELECT borough, zipcode FROM presentation.temp_dim_location
            ON CONFLICT (borough, zipcode) DO NOTHING;
        """))
        conn.execute(text("DROP TABLE presentation.temp_dim_location;"))
        
        # Fetch the database-generated location_ids back into Pandas
        mapped_locations = pd.read_sql("SELECT location_id, borough, zipcode FROM presentation.dim_location", conn)
        logger.info(f"Synchronized locations with dim_location.")
        
        # --- 3. Build and Load fact_inspection ---
        # Merge the generated location_id back into our main cleaned dataframe
        fact_df = clean_df.merge(mapped_locations, on=['borough', 'zipcode'], how='left')
        
        # Select only the exact columns needed for the fact table
        fact_inspection = fact_df[[
            'restaurant_id', 'location_id', 'inspection_date', 'score', 
            'grade', 'violation_description', 'critical_flag'
        ]]
        
        # Append all facts (history of inspections)
        fact_inspection.to_sql('fact_inspection', conn, schema='presentation', if_exists='append', index=False)
        logger.info(f"Loaded {len(fact_inspection)} inspection events into fact_inspection.")