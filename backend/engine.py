import duckdb
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the parquet file
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PARQUET_FILE = DATA_DIR / "medicaid-provider-spending.parquet"

class DataEngine:
    def __init__(self):
        self.file_path = str(PARQUET_FILE)
        if not os.path.exists(self.file_path):
            logger.warning(f"Data file not found at {self.file_path}. Queries will fail.")

    def get_provider_stats(self, npi: str, hcpcs_code: str):
        """
        Get the provider's billing stats compared to the national average for a specific code.
        """
        query = f"""
        WITH NationalStats AS (
            SELECT 
                HCPCS_CODE,
                AVG(TOTAL_PAID) as avg_paid,
                STDDEV(TOTAL_PAID) as stddev_paid,
                AVG(TOTAL_CLAIM_LINES) as avg_lines,
                STDDEV(TOTAL_CLAIM_LINES) as stddev_lines
            FROM read_parquet('{self.file_path}')
            WHERE HCPCS_CODE = '{hcpcs_code}'
            GROUP BY HCPCS_CODE
        ),
        ProviderStats AS (
            SELECT
                SERVICING_PROVIDER_NPI_NUM as npi,
                HCPCS_CODE,
                SUM(TOTAL_PAID) as provider_total_paid,
                SUM(TOTAL_CLAIM_LINES) as provider_total_lines
            FROM read_parquet('{self.file_path}')
            WHERE SERVICING_PROVIDER_NPI_NUM = '{npi}' 
              AND HCPCS_CODE = '{hcpcs_code}'
            GROUP BY SERVICING_PROVIDER_NPI_NUM, HCPCS_CODE
        )
        SELECT 
            p.npi,
            p.HCPCS_CODE,
            p.provider_total_paid,
            n.avg_paid as national_avg_paid,
            p.provider_total_lines,
            n.avg_lines as national_avg_lines,
            (p.provider_total_paid - n.avg_paid) / NULLIF(n.stddev_paid, 0) as z_score_paid
        FROM ProviderStats p
        JOIN NationalStats n ON p.HCPCS_CODE = n.HCPCS_CODE;
        """
        
        try:
            with duckdb.connect() as con:
                result = con.execute(query).fetchdf()
                if result.empty:
                    return None
                return result.to_dict(orient="records")[0]
        except Exception as e:
            logger.error(f"DB Error: {e}")
            return None

engine = DataEngine()
