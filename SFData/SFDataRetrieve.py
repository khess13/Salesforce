"""
Retrieves Account and Contract objects from Salesforce
and writes them to the Data folder for downstream scripts.

Replaces manual CSV exports of extract.csv and contract.csv.

Requires: pip install simple-salesforce
"""

import os
import pandas as pd
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

# --- credentials ---
# Move these to environment variables or a config file.
# Never commit credentials to source control.
SF_USERNAME = os.environ.get('SF_USERNAME', '')
SF_PASSWORD = os.environ.get('SF_PASSWORD', '')
SF_TOKEN    = os.environ.get('SF_TOKEN', '')    # security token, not a session token
SF_DOMAIN   = 'login'                           # use 'test' for sandbox

# --- output ---
ROOT     = os.getcwd()
DATA_DIR = ROOT + '\\Data\\'

QUERIES = {
    'extract.csv': "SELECT Id, SCEIS_CODE__C FROM Account",
    'contract.csv': (
        "SELECT AccountId, Contract_Type__C, Administrative_Services__C "
        "FROM Contract"
    ),
}


def main():
    if not all([SF_USERNAME, SF_PASSWORD, SF_TOKEN]):
        raise EnvironmentError(
            'SF_USERNAME, SF_PASSWORD, and SF_TOKEN must be set '
            'as environment variables before running this script.'
        )

    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(
            f'Data directory not found: {DATA_DIR}\n'
            'Expected the standard project layout with a Data\\ subfolder.'
        )

    try:
        sf = Salesforce(
            username=SF_USERNAME,
            password=SF_PASSWORD,
            security_token=SF_TOKEN,
            domain=SF_DOMAIN,
        )
        print('Connected to Salesforce.\n')
    except SalesforceAuthenticationFailed as e:
        raise SystemExit(f'Authentication failed: {e}') from e

    for filename, query in QUERIES.items():
        object_name = query.split('FROM ')[-1]
        print(f'Querying {object_name}...')
        results = sf.query_all(query)
        records = results['records']
        df = pd.DataFrame.from_records(
            [{k: v for k, v in r.items() if k != 'attributes'} for r in records]
        )
        print(f'  {len(df)} records retrieved.')
        out_path = DATA_DIR + filename
        df.to_csv(out_path, index=False)
        print(f'  Saved to {out_path}\n')

    print('Done. Data folder is up to date.')


if __name__ == '__main__':
    main()
