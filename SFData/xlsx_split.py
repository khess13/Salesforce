"""
Splits xlsx into individual files for SF Dataloader upload.
Creates ContentVersion manifest, shared services list,
and per-agency billing files.
"""
from __future__ import annotations

import os
import re
import datetime as dt
from getpass import getuser
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from FileService import FileService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROOT = os.getcwd()
DATESTAMP = dt.datetime.now().strftime('%m-%d-%Y')
OUTPUTPATH = f'C:\\Users\\{getuser()}\\XLSDrop\\'

COLS_TO_DROP = [
    'Exception', 'Plant', 'Commitment Item', 'Fund',
    'FI Function Area', 'Grant', 'Cost_center', 'G/L Account',
]

PROPER_COUNTY_LIST = [
    'Abbeville', 'Aiken', 'Allendale', 'Anderson', 'Bamberg',
    'Barnwell', 'Beaufort', 'Berkeley', 'Calhoun', 'Charleston',
    'Cherokee', 'Chester', 'Chesterfield', 'Clarendon', 'Colleton',
    'Darlington', 'Dillon', 'Dorchester', 'Edgefield', 'Fairfield',
    'Florence', 'Georgetown', 'Greenville', 'Greenwood', 'Hampton',
    'Horry', 'Jasper', 'Kershaw', 'Lancaster', 'Laurens', 'Lee',
    'Lexington', 'Marion', 'Marlboro', 'McCormick', 'Newberry',
    'Oconee', 'Orangeburg', 'Pickens', 'Richland', 'Saluda',
    'Spartanburg', 'Sumter', 'Union', 'Williamsburg', 'York',
]
UPPER_COUNTY_LIST = [c.upper() for c in PROPER_COUNTY_LIST]

# Counties whose first-four letters don't match the standard XXXXCO pattern
EXCEPTION_COUNTY = {
    'CHESTER': 'CHETCO',
    'CHESTERFIELD': 'CHEKCO',
    'CHEROKEE': 'CHERCO',
    'GREENVILLE': 'GREVCO',
    'GREENWOOD': 'GREWCO',
    'CHAS': 'CHARCO',
    'LEE': 'LEE CO',
}

REMOVE_SCHOOL_TERMS = ['SCHOOL', 'DISTRICT', 'SCH DIST']
RE_COUNTY = re.compile(r'^[A-Z]+\W{1}CO[A-Z]*')

# Sub-agencies identified by keyword in contract description
B_AGENCIES = {
    'E240B': 'EMERGENCY',
    # 'H630B': 'FIRST STEPS',  # became its own agency
    'N200B': 'CRIMINAL JUSTICE',
}

# D500 (Admin) sub-division mapping: last-four account suffix -> agency code
D500_SUFFIX_MAP = {
    '0009': 'D500FMPS',   # Facilities Mgmt & Prop Srv
    '0012': 'D500FMPS',
    '0039': 'D500FMPS',
    '0017': 'D500PMO',    # Program Mgmt Office (NOTE: also maps to OTIS - verify)
    '0013': 'D500SASS',   # State Agy Support Srvs
    '0008': 'D500DSHR',   # Division of State HR  # TODO: confirm correct
    '0007': 'D500EBO',    # Exec Budget Office
    '0035': 'D500GAEO',   # Govt Affairs and Economic Opportunity
    '0036': 'D500GAEO',
    '0025': 'D500OEPP',   # Office of Exec Policy & Programs
    '0033': 'D500OEPP',
    '0034': 'D500OEPP',
    '0014': 'D500SCEIS',  # SC Enterprise Info System
    '0003': 'D500OAS',    # Office of Administrative Services
}

# Numerical customer numbers included by contract description name
NAMED_NUMERIC_ACCOUNTS = {
    'RIVERBANKS ZOO',
    'SC INTERACTIVE',
    'SC EDUCATION LOTTERY',
    'SC BAR ASSOCIATION',
    'SC BAR ASSOCIATION - NON-BILLABLE',
    'ESTILL, TOWN OF',
}

format_currency = '${:,.2f}'.format


# ---------------------------------------------------------------------------
# Account code resolution
# ---------------------------------------------------------------------------

def _resolve_d500(last_four: str) -> str:
    """Map a D500 sub-account suffix to its agency code, or fall back to D500."""
    return D500_SUFFIX_MAP.get(last_four, 'D500')


def _resolve_county(first_word: str, contract_desc: str) -> str:
    """Return county agency code, or 'zzz' if this row should be dropped."""
    if not RE_COUNTY.search(contract_desc):
        return 'zzz'
    if any(term in contract_desc for term in REMOVE_SCHOOL_TERMS):
        return 'zzz'
    if first_word in EXCEPTION_COUNTY:
        # key confirmed present above, use [] not .get()
        return EXCEPTION_COUNTY[first_word]
    return first_word[:4] + 'CO'


def create_acct_code(row: pd.Series) -> str:
    """
    Map a raw ECC row to a Salesforce agency code.
    Returns 'zzz' for rows that should be excluded.
    """
    contract_desc: str = row['Document Desc.']
    customer_number: str = row['Customer']

    # Normalise 10-char numbers by stripping leading 3 chars
    if len(customer_number) == 10:
        customer_number = customer_number[3:]

    first_four = customer_number[:4]
    last_four = customer_number[-4:]
    first_word = contract_desc[:contract_desc.find(' ')]

    # --- Special cases (hardcoded overrides) ---
    if first_four == 'H030' and contract_desc == 'PASCAL IT BILLING':
        return 'H030B'

    if first_four == 'R230':
        return 'R230B' if customer_number == 'R230001' else 'R230'

    if first_four == 'D500':
        return _resolve_d500(last_four)

    # --- Alpha-leading customer numbers: use first four chars ---
    if customer_number[0].isalpha():
        return first_four

    # --- Numeric special cases ---
    if first_four == '2160':
        return customer_number if customer_number.endswith('16') else '2160000'

    if customer_number == '4003840':
        return 'H650'

    if contract_desc in NAMED_NUMERIC_ACCOUNTS:
        return customer_number

    # --- County matching ---
    if first_word in UPPER_COUNTY_LIST:
        return _resolve_county(first_word, contract_desc)

    return 'zzz'


# ---------------------------------------------------------------------------
# Material translation
# ---------------------------------------------------------------------------

def build_material_translation(sd_map_df: pd.DataFrame) -> Dict[str, str]:
    """Build {material_description: short_label} lookup from the SD map file."""
    unmatched = sd_map_df['MaterialTranslate'].isna().sum()
    print(f'Unmatched material entries: {unmatched} (baseline is 36)')
    return (
        sd_map_df
        .dropna(subset=['MaterialTranslate'])
        .set_index('Material')['MaterialTranslate']
        .to_dict()
    )


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def prepare_ecc_data(
    xlsx_path: str,
    mat_trans_dict: Dict[str, str],
) -> pd.DataFrame:
    """Load, clean, and annotate the raw ECC export."""
    df: pd.DataFrame = pd.read_excel(xlsx_path)  # type: ignore[assignment]
    invoice_date_fallback = df.iloc[0, 4]

    df['Customer'] = df['Customer'].astype(str)
    df['Document Desc.'] = df['Document Desc.'].fillna('One Time Charge')
    df['Document Desc.'] = df['Document Desc.'].str.replace(
        '/', '-', regex=False
    )
    df.drop(columns=COLS_TO_DROP, inplace=True)

    df['Invoice Date'] = df['Invoice Date'].fillna(invoice_date_fallback)
    df['AgyCode'] = df.apply(create_acct_code, axis=1)
    df = df.loc[df['AgyCode'] != 'zzz'].copy()  # type: ignore[assignment]

    df['MaterialTranslate'] = df['Material Desc.'].map(mat_trans_dict)
    return df


def tag_b_agencies(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Reassign AgyCode for B sub-agencies and return the updated frame
    plus the list of B agency codes that actually have rows.
    """
    new_b_codes = []
    for code, keyword in B_AGENCIES.items():
        mask = df['Document Desc.'].str.contains(keyword, na=False)
        df.loc[mask, 'AgyCode'] = code
        if mask.any():
            new_b_codes.append(code)
    return df, new_b_codes


# ---------------------------------------------------------------------------
# File generation
# ---------------------------------------------------------------------------

def build_filename(
    agycode: str,
    inv_date: str,
    invoice_amt: str,
    customer_name: str,
    sales_doc_no: str,
) -> str:
    """Construct the standard output filename for a billing xlsx."""
    iso_date = (
        '20' + inv_date[-2:]
        + '-' + inv_date[:2]
        + '-' + inv_date[3:5]
    )
    return (
        f'{iso_date} - {invoice_amt} - {customer_name}'
        f' - Sales Doc {sales_doc_no} - Shared Services.xlsx'
    )


def write_billing_file(subset_df: pd.DataFrame, filepath: str) -> None:
    """Write a single agency billing subset to an xlsx file."""
    export_df = subset_df.drop(
        columns=['AgyCode', 'MaterialTranslate'], errors='ignore'
    )
    with pd.ExcelWriter(filepath) as writer:  # pylint: disable=abstract-class-instantiated
        export_df.to_excel(writer, index=False)


def process_agency(
    agyc: str,
    subdf: pd.DataFrame,
    sf_id_lookup: Dict[str, str],
    output_path: str,
) -> Tuple[str, List[dict]]:
    """
    Process all invoices for a single agency.

    Returns:
        services_string: newline-joined sorted material translations
        cv_rows: list of ContentVersion manifest row dicts
    """
    services_string = '\n'.join(sorted(
        subdf['MaterialTranslate'].dropna().drop_duplicates().tolist()
    ))
    cv_rows: List[dict] = []
    sf_id = sf_id_lookup[agyc]

    invoice_dates = subdf['Invoice Date'].drop_duplicates().tolist()
    sales_docs = subdf['Sales Document #'].drop_duplicates().tolist()

    for inv_date in invoice_dates:
        date_df = subdf.loc[subdf['Invoice Date'] == inv_date]
        if date_df.empty:
            continue

        for sales_doc in sales_docs:
            sale_df = date_df.loc[
                date_df['Sales Document #'] == sales_doc
            ].copy()
            if sale_df.empty:
                continue

            pdate = inv_date.strftime('%m-%d-%Y')
            sales_doc_no = str(int(sales_doc))
            invoice_amt = format_currency(
                round(sale_df['Net Value'].sum(), 2)
            )

            desc_list = sale_df['Document Desc.'].drop_duplicates().tolist()
            is_otc = sale_df.iloc[0, 3] == 'One Time Charge'
            customer_name = desc_list[1] if is_otc else desc_list[0]

            filename = build_filename(
                agyc, pdate, invoice_amt, customer_name, sales_doc_no
            )
            filepath = output_path + filename

            write_billing_file(sale_df, filepath)
            print(f'Creating {filename}')

            cv_rows.append({
                'Title': filename[:-5],
                'Description': (
                    f'S&D billing for services on {pdate}.'
                    f' Generated on {DATESTAMP}'
                ),
                'VersionData': filepath,
                'PathOnClient': filepath,
                'FirstPublishLocationId': sf_id,
            })

    return services_string, cv_rows


# ---------------------------------------------------------------------------
# Output assembly
# ---------------------------------------------------------------------------

def build_shared_services_df(
    agy_results: Dict[str, str],
    sf_id_lookup: Dict[str, str],
) -> pd.DataFrame:
    """
    Convert the {agycode: services_string} dict into a DataFrame with SF IDs.
    Accounts with no billing get a blank service entry.
    """
    all_results = {agy: agy_results.get(agy, ' ') for agy in sf_id_lookup}

    df = pd.DataFrame.from_dict(
        all_results, orient='index', columns=['Service']
    )
    df.index.name = 'AgyCode'
    df.reset_index(inplace=True)
    df.replace('', np.nan, inplace=True)
    df.dropna(subset=['Service'], inplace=True)
    df['SalesforceAcctID'] = df['AgyCode'].map(sf_id_lookup)
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    fs = FileService(ROOT, OUTPUTPATH)
    file_dict = fs.get_dependent_file_dict()
    fs.clear_destination_folder()

    # Load reference data
    sf_acct_df = pd.read_csv(file_dict['SFAcct'])
    sd_map_df = pd.read_excel(file_dict['SDMap'])

    sf_id_lookup: Dict[str, str] = (
        sf_acct_df
        .dropna(subset=['SCEIS_CODE__C'])
        .set_index('SCEIS_CODE__C')['ID']
        .to_dict()
    )
    mat_trans_dict = build_material_translation(sd_map_df)

    # Prepare ECC data
    ecc_df = prepare_ecc_data(file_dict['ECCInv'], mat_trans_dict)
    ecc_df, new_b_codes = tag_b_agencies(ecc_df)

    agycodes = ecc_df['AgyCode'].drop_duplicates().tolist() + new_b_codes

    # Process each agency
    agy_services: Dict[str, str] = {}
    all_cv_rows: List[dict] = []

    for agyc in agycodes:
        subdf = ecc_df.loc[ecc_df['AgyCode'] == agyc].copy()
        services_string, cv_rows = process_agency(
            agyc, subdf, sf_id_lookup, OUTPUTPATH
        )
        agy_services[agyc] = services_string
        all_cv_rows.extend(cv_rows)

    # Write ContentVersion manifest
    print('Creating manifest for ContentVersion')
    content_version_df = pd.DataFrame(all_cv_rows)
    content_version_df.to_csv(
        f'{OUTPUTPATH}ContentVersion Generated On {DATESTAMP}.csv',
        index=False,
    )

    # Write shared services export
    print('Creating shared services list')
    shared_services_df = build_shared_services_df(agy_services, sf_id_lookup)
    shared_services_df.to_csv(
        f'{OUTPUTPATH}exportSharedServices.csv', index=False
    )

    # Copy SDL mapping files
    fs.copy_file('pdfimportmap.sdl')
    fs.copy_file('dtoservices.sdl')

    print('Operation Complete!')


if __name__ == '__main__':
    main()
