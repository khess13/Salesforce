"""
Generates agency-managed services and contract updates for Salesforce.
Produces exportAgencyServices.csv and exportContracts.csv.
"""
from __future__ import annotations

import os
from typing import Dict, List

import numpy as np
import pandas as pd
from FileService import FileService

ROOT = os.getcwd()
OUTPUTPATH = os.path.join(ROOT, 'Services')

# ---------------------------------------------------------------------------
# Survey data — agency codes per service category
# Last updated dates noted inline; refresh from ARM/DIS surveys as needed.
# ---------------------------------------------------------------------------

# updated 3-2021, ARM Survey
MS_EXCHANGE = [
    'E200', 'L460', 'N200', 'D500', 'H790', 'P320', 'N040', 'H630',
    'R360', 'J120', 'R400', 'P240', 'N080', 'R440', 'U120', 'P120',
    'B040', 'A170', 'P360', 'F500', 'E190', 'H670', 'D100', 'H750',
    'L040', 'H730', 'P260',
]

# updated 4-2021, ARM Survey
SELF_MANAGED_VPN = [
    'P280', 'J020', 'R360', 'J120', 'J160', 'N040', 'E200', 'P320',
    'R450', 'H790', 'N080',
]

# updated 5-2021, ARM Survey
SELF_MANAGED_FIREWALL = [
    'A200', 'c0002160016', 'C050', 'D100', 'E080', 'E190', 'E200',
    'E240', 'E240B', 'E500', 'F500', 'H590', 'H630', 'H670', 'H710',
    'H730', 'H750', 'H790', 'H870', 'H950', 'J020', 'J040', 'J120',
    'J160', 'K050', 'L040', 'L060', 'L120', 'L320', 'N040', 'N080',
    'N120', 'N200', 'P120', 'P240', 'P260', 'P280', 'P320', 'P450',
    'R120', 'R200', 'R360', 'R400', 'R440', 'R600', 'U120', 'U150',
    'P260',
]

# updated 5-2021 / 3-2023, ARM Survey (added more 11-2022)
NON_DTO_INTERNET = [
    'A010', 'A050', 'A150', 'A170', 'A200', 'B040', 'E190', 'E240B',
    'H530', 'H590', 'H640', 'H650', 'H750', 'J040', 'L120', 'N120',
    'P260', 'P360', 'P450', 'U150', 'U200', 'Y140', 'R600', '3599957',
    'P280', 'H730', 'J160', 'L320', 'E260', 'L080', 'P240', 'U120',
    '4002072', 'D100', 'J020', 'R200',
]

# updated 6-2021, DIS Survey
AGY_O365_EMAIL = [
    'D100', 'D250', 'D300', 'D500', 'E080', 'E120', 'E190', 'E200',
    'E240', 'E240B', 'E260', 'F500', 'H630', 'H670', 'H870', 'H950',
    'J020', 'J040', 'J120', 'J160', 'J200', 'K050', 'L040', 'L060',
    'L080', 'L120', 'L360', 'N040', 'N080', 'N120', 'N200', 'P160',
    'P240', 'P280', 'P320', 'P360', 'P450', 'R040', 'R060', 'R080',
    'R120', 'R200', 'R360', 'R400', 'R600', 'U120', 'H590', 'E500',
]

AGY_ONE_DRIVE = [
    'D100', 'E190', 'E200', 'E240B', 'H630', 'H670', 'J020', 'J120',
    'L040', 'L120', 'P280', 'P320', 'P450', 'R080', 'R200', 'R400',
    'R600',
]

AGY_SHAREPOINT = [
    'E190', 'E240B', 'H670', 'J020', 'J120', 'L040', 'N120', 'P280',
    'P320', 'P450', 'R600', 'U120',
]

# updated 10-2021
VOIP_ATT = ['GA', 'N080', 'R600', 'H590', 'E240B', 'R360']

VOIP_NWN = [
    'J040', 'U120', 'F500', 'R080', 'H710', 'P160', 'R440', 'T360',
    'H650', 'H640', 'H470', 'L040', 'K050',
]

VOIP_SEGRA = [
    'c0004002072', 'A200', 'A850', 'C050', 'D050', 'D100', 'D170',
    'D200', 'D250', 'E040', 'E080', 'E120', 'E160', 'E190', 'E200',
    'E210', 'E230', 'E240', 'E280', 'E500', 'E550', 'D500', 'D300',
    'H960', 'F270', 'BARNCO', 'CHETCO', 'DARLCO', 'H030', 'H060',
    'H090', 'H120', 'H150', 'H170', 'H270', 'H510', 'H590', 'H630B',
    'H630', 'H670', 'T200', 'T220', 'T260', 'T100', 'T140', 'T160',
    'T120', 'H730', 'H750', 'H790', 'H870', 'H910', 'H950', 'J020',
    'J040', 'J120', 'J160', 'J200', 'K050', 'L040', 'L240', 'L320',
    'L360', 'L400', 'L460', 'L080', 'N040', 'N080', 'N120', 'N200',
    'P120', 'P240', 'P260', 'P280', 'P320', 'P400', 'R040', 'R060',
    'R120', 'R200', 'R230', 'R230B', 'R280', 'R360', 'R400', 'R440',
    'R520', 'S600', 'U300', 'U120', 'c0003599957',
]

ADMIN_SERVICE_TYPES = ['Administrative']


# ---------------------------------------------------------------------------
# Processing functions
# ---------------------------------------------------------------------------

def build_ancillary_services(agy_code_list: List[str]) -> Dict[str, str]:
    """
    Build {agycode: service_string} for all known ancillary services
    using the survey membership lists above.
    """
    results = {}
    for agy in agy_code_list:
        services = []
        if agy in VOIP_ATT:
            services.append('AT&T VoIP')
        if agy in SELF_MANAGED_FIREWALL:
            services.append('Firewall')
        if agy in NON_DTO_INTERNET:
            services.append('Internet')
        if agy in MS_EXCHANGE:
            services.append('On-prem MS Exchange')
        if agy in AGY_O365_EMAIL:
            services.append('O365 Email')
        if agy in AGY_ONE_DRIVE:
            services.append('O365 OneDrive')
        if agy in AGY_SHAREPOINT:
            services.append('O365 SharePoint')
        if agy in VOIP_NWN:
            services.append('NWN VoIP')
        if agy in SELF_MANAGED_VPN:
            services.append('Pulse VPN')
        if agy in VOIP_SEGRA:
            services.append('Segra VoIP')

        results[agy] = '\n'.join(services) if services else ' '

    return results


def build_contract_services(contracts_df: pd.DataFrame) -> Dict[str, str]:
    """
    Build {salesforce_id: service_string} for administrative contract services.
    """
    admin_contracts = (
        contracts_df[['ACCOUNTID', 'CONTRACT_TYPE__C', 'ADMINISTRATIVE_SERVICES__C']]
        .drop_duplicates()
        .loc[lambda df: df['CONTRACT_TYPE__C'].isin(ADMIN_SERVICE_TYPES)]
        .dropna(subset=['ADMINISTRATIVE_SERVICES__C'])
    )

    contract_dict: Dict[str, str] = {}
    for sf_id, group in admin_contracts.groupby('ACCOUNTID'):
        services = group['ADMINISTRATIVE_SERVICES__C'].tolist()
        # Flatten any semicolon-delimited entries and deduplicate
        flat = set()
        for entry in services:
            for part in str(entry).split(';'):
                flat.add(part.strip())
        contract_dict[str(sf_id)] = '\n'.join(flat)

    return contract_dict


def build_export_df(
    results: Dict[str, str],
    sf_id_lookup: Dict[str, str],
) -> pd.DataFrame:
    """
    Convert a {code: service_string} dict into a DataFrame with both
    AgyCode and SalesforceAcctID columns. Adds null rows for accounts
    without data. The key type determines which column is the index:
    18-char keys are Salesforce IDs; shorter keys are agency codes.
    """
    sample_key = next(iter(results))
    is_sf_id = len(sample_key) == 18
    index_col = 'SalesforceAcctID' if is_sf_id else 'AgyCode'
    other_col = 'AgyCode' if is_sf_id else 'SalesforceAcctID'

    df = pd.DataFrame.from_dict(results, orient='index', columns=['Service'])
    df.index.name = index_col
    df.reset_index(inplace=True)

    df.replace('', np.nan, inplace=True)
    df.dropna(subset=['Service'], inplace=True)

    # Fill in the cross-reference column and add null rows for missing accounts
    reverse_lookup = {v: k for k, v in sf_id_lookup.items()}
    for agy, sf_id in sf_id_lookup.items():
        if is_sf_id:
            df.loc[df[index_col] == sf_id, other_col] = agy
        else:
            df.loc[df[index_col] == agy, other_col] = sf_id

        if df.loc[df['AgyCode'] == agy].empty:
            df.loc[len(df), ['AgyCode', 'SalesforceAcctID', 'Service']] = (
                agy, sf_id, ''
            )

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    fs = FileService(ROOT, OUTPUTPATH)
    file_dict = fs.get_dependent_file_dict()
    fs.clear_destination_folder()

    pd.set_option('display.max_colwidth', None)

    contracts_df = pd.read_csv(file_dict['Contracts'], encoding='iso-8859-1')
    sf_acct_df = pd.read_csv(file_dict['SFAcct'])
    sf_acct_df.dropna(subset=['SCEIS_CODE__C'], inplace=True)

    sf_id_lookup: Dict[str, str] = (
        sf_acct_df
        .set_index('SCEIS_CODE__C')['ID']
        .to_dict()
    )
    agy_code_list = sf_acct_df['SCEIS_CODE__C'].drop_duplicates().tolist()

    # Build service dicts
    ancillary = build_ancillary_services(agy_code_list)
    contracts = build_contract_services(contracts_df)

    if len(set(ancillary.values())) == 1:
        print('WARNING: No ancillary services found — check input data.')

    exports = [
        (ancillary, 'exportAgencyServices.csv'),
        (contracts, 'exportContracts.csv'),
    ]

    for results, filename in exports:
        if not results:
            continue
        print(f'Building {filename}')
        df = build_export_df(results, sf_id_lookup)
        df.to_csv(os.path.join(OUTPUTPATH, filename), index=False)

    fs.copy_file('contract_services.sdl')
    fs.copy_file('agencyservices.sdl')
    print('Done.')


if __name__ == '__main__':
    main()
