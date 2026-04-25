import json
import duckdb
import os
from engine import engine

def get_demo_targets():
    """Find the top 3 outlier providers for a common code to use in our demo PDF."""
    code_to_test = '99213'  # Office Visit, commonly abused code
    
    query = f"""
    WITH NationalStats AS (
        SELECT 
            AVG(TOTAL_PAID) as avg_paid,
            STDDEV(TOTAL_PAID) as stddev_paid
        FROM read_parquet('{engine.file_path}')
        WHERE HCPCS_CODE = '{code_to_test}'
    )
    SELECT 
        SERVICING_PROVIDER_NPI_NUM as npi,
        SUM(TOTAL_PAID) as provider_total,
        (SUM(TOTAL_PAID) - (SELECT avg_paid FROM NationalStats)) / (SELECT stddev_paid FROM NationalStats) as z_score
    FROM read_parquet('{engine.file_path}')
    WHERE HCPCS_CODE = '{code_to_test}'
      AND SERVICING_PROVIDER_NPI_NUM IS NOT NULL
      AND SERVICING_PROVIDER_NPI_NUM != ''
    GROUP BY SERVICING_PROVIDER_NPI_NUM
    ORDER BY provider_total DESC
    LIMIT 3;
    """
    
    print("Finding top 3 anomalous providers for code 99213 (Demo Targets)...")
    try:
        with duckdb.connect() as con:
            res = con.execute(query).fetchdf()
            print("\n--- DEMO TARGETS ---")
            print(res.to_string())
            print("\nCreate a fake PDF using one of these NPIs and code 99213 to demo the app.")
    except Exception as e:
        print(f"Error finding demo targets: {e}")

if __name__ == "__main__":
    get_demo_targets()
