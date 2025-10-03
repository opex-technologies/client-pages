#!/usr/bin/env python3
"""
Data Verification Script

This script verifies the integrity of the backloaded SASE RFI data in BigQuery.
"""

import logging
from datetime import datetime
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize BigQuery client
client = bigquery.Client()

# Constants
DATASET_ID = "opex_dev"
TABLE_ID = "network_security_survey"

def verify_data_integrity():
    """Verify the integrity of backloaded data."""
    logger.info("Starting data integrity verification...")
    
    try:
        # Get table reference
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)
        
        logger.info(f"Table: {table.project}.{table.dataset_id}.{table.table_id}")
        logger.info(f"Total rows: {table.num_rows}")
        
        # Query backloaded vendor data
        query = f"""
        SELECT 
            source,
            company_name,
            COUNT(*) as record_count,
            MAX(inserted_at) as latest_insert
        FROM `{DATASET_ID}.{TABLE_ID}`
        WHERE source = 'sase-rfi-backload'
        GROUP BY source, company_name
        ORDER BY company_name
        """
        
        results = client.query(query).result()
        
        logger.info("Backloaded vendor data:")
        vendor_count = 0
        for row in results:
            logger.info(f"  {row.company_name}: {row.record_count} records (inserted: {row.latest_insert})")
            vendor_count += 1
        
        logger.info(f"Total backloaded vendors: {vendor_count}")
        
        # Query sample data for each vendor
        sample_query = f"""
        SELECT 
            company_name,
            year_founded,
            headquarters,
            do_you_offer_circuit_procurement,
            can_you_shift_traffic_mid_session,
            do_you_provide_content_filtering
        FROM `{DATASET_ID}.{TABLE_ID}`
        WHERE source = 'sase-rfi-backload'
        ORDER BY company_name
        LIMIT 5
        """
        
        sample_results = client.query(sample_query).result()
        
        logger.info("\nSample data verification:")
        for row in sample_results:
            logger.info(f"  {row.company_name}:")
            logger.info(f"    Founded: {row.year_founded}")
            logger.info(f"    HQ: {row.headquarters}")
            logger.info(f"    Circuit procurement: {row.do_you_offer_circuit_procurement}")
            logger.info(f"    Mid-session shift: {row.can_you_shift_traffic_mid_session}")
            logger.info(f"    Content filtering: {row.do_you_provide_content_filtering}")
        
        # Check field coverage
        coverage_query = f"""
        SELECT 
            company_name,
            COUNTIF(company_name IS NOT NULL) as company_name_filled,
            COUNTIF(year_founded IS NOT NULL) as year_founded_filled,
            COUNTIF(headquarters IS NOT NULL) as headquarters_filled,
            COUNTIF(do_you_offer_circuit_procurement IS NOT NULL) as circuit_procurement_filled,
            COUNTIF(can_you_shift_traffic_mid_session IS NOT NULL) as mid_session_shift_filled,
            COUNTIF(do_you_provide_content_filtering IS NOT NULL) as content_filtering_filled
        FROM `{DATASET_ID}.{TABLE_ID}`
        WHERE source = 'sase-rfi-backload'
        GROUP BY company_name
        ORDER BY company_name
        """
        
        coverage_results = client.query(coverage_query).result()
        
        logger.info("\nField coverage analysis:")
        for row in coverage_results:
            logger.info(f"  {row.company_name}:")
            logger.info(f"    Company: {row.company_name_filled}/1, Founded: {row.year_founded_filled}/1")
            logger.info(f"    HQ: {row.headquarters_filled}/1, Circuit: {row.circuit_procurement_filled}/1")
            logger.info(f"    Mid-session: {row.mid_session_shift_filled}/1, Filtering: {row.content_filtering_filled}/1")
        
        logger.info("Data integrity verification completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    verify_data_integrity()