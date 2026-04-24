"""
Generates a file to update the headcount statistic in Salesforce.
"""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd
from FileService import FileService

ROOT = os.getcwd()
OUTPUTPATH = os.path.join(ROOT, 'Headcount')
DATESTAMP = dt.datetime.now().strftime('%m-%d-%Y')


def main() -> None:
    fs = FileService(ROOT, OUTPUTPATH)
    file_dict = fs.get_dependent_file_dict()
    fs.clear_destination_folder()

    sf_acct_df = pd.read_csv(file_dict['SFAcct'])
    headcount_df: pd.DataFrame = pd.read_excel(file_dict['HR'])  # type: ignore[assignment]

    # Build {SCEIS_CODE: SalesforceID} lookup
    acctid_lookup = (
        sf_acct_df
        .dropna(subset=['SCEIS_CODE__C'])
        .set_index('SCEIS_CODE__C')['ID']
        .to_dict()
    )

    # Map Salesforce IDs onto headcount rows; unmatched rows get NaN
    headcount_df['SalesforceAcctID'] = (
        headcount_df['Personnel Area - Key'].map(acctid_lookup)
    )
    headcount_df.dropna(subset=['SalesforceAcctID'], inplace=True)

    filename = f'Headcount - Created on {DATESTAMP}.csv'
    headcount_df.to_csv(os.path.join(OUTPUTPATH, filename), index=False)

    fs.copy_file('hc.sdl')
    print('Operation complete.')


if __name__ == '__main__':
    main()
