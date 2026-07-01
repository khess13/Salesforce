"""Retrieves Salesforce data and writes CSVs to Data\\ for pipeline consumption"""
from __future__ import annotations

import os
import pandas as pd
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()

ROOT = os.getcwd()
DATA_DIR = os.path.join(ROOT, 'Data')

QUERIES = {
    'extract': (os.environ['EXTRACT_QUERY_LIST']),
    'contract': (os.environ['EXTRACT_CONTRACT_QUERY_LIST']),
}

OUTPUT_FILES = {
    'extract': 'extract.csv',
    'contract': 'contract.csv',
}


def get_connection() -> Salesforce:
    """Authenticates against Salesforce using .env credentials"""
    return Salesforce(
        username=os.environ['SF_USERNAME'],
        password=os.environ['SF_PASSWORD'],
        security_token=os.environ['SF_SECURITY_TOKEN'],
    )


def run_query(sf: Salesforce, query_name: str) -> pd.DataFrame:
    """Runs a named SOQL query and returns a DataFrame"""
    soql = QUERIES[query_name]
    results = sf.query_all(soql)
    records = results['records']
    df = pd.DataFrame(records).drop(columns='attributes', errors='ignore')
    return df


def write_csv(df: pd.DataFrame, query_name: str) -> None:
    """Writes DataFrame to Data\\ subfolder"""
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, OUTPUT_FILES[query_name])
    df.to_csv(out_path, index=False)
    print(f'Wrote {out_path}')


def main() -> None:
    sf = get_connection()
    for query_name in QUERIES:
        df = run_query(sf, query_name)
        write_csv(df, query_name)
    print('SF data retrieval complete!')


if __name__ == '__main__':
    main()