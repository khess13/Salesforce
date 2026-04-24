"""
Splits a BO invoice PDF into per-page files for SF Dataloader upload.
Creates a ContentVersion manifest CSV.
"""
from __future__ import annotations

import datetime as dt
import getpass
import os
import re
from typing import Dict

import pandas as pd
from tabula import read_pdf
from PyPDF2 import PdfReader, PdfWriter

from FileService import FileService

ROOT = os.getcwd()
DATESTAMP = dt.datetime.now().strftime('%m-%d-%Y')
OUTPUTPATH = os.path.join('C:\\', 'Users', getpass.getuser(), 'PDFDrop')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_agycode(agy_code: str) -> str:
    """
    Normalise agency codes that were stored as floats in the source report
    (e.g. '123.0' -> '123').
    """
    try:
        return '{:0.0f}'.format(float(agy_code))
    except (ValueError, TypeError):
        return str(agy_code)


def build_title(
    inv_date_iso: str,
    invoice_amt: str,
    customer_name: str,
    invoice_no: str,
) -> str:
    """Construct the standard ContentVersion title string."""
    return (
        f'{inv_date_iso} - {invoice_amt} - {customer_name}'
        f' - Invoice {invoice_no} - Shared Services'
    )


def parse_pdf_page(page_path: str) -> dict:
    """
    Extract invoice fields from a single-page PDF.
    Returns a dict with agycode, invoice date, number, amount, customer name.
    """
    pdfpage = read_pdf(page_path, pages='all')
    df = pdfpage[0]
    df.dropna(subset=['Total'], how='all', inplace=True)

    agycode = clean_agycode(df.iloc[0, 0])

    # Normalise date: replace slashes, strip stray alpha chars
    raw_date = df.iloc[0, 3].replace('/', '-')
    pdate = re.sub(r'[A-Za-z]*', '', raw_date)

    invoice_no = str(df.iloc[0, 4])[:-2]
    invoice_amt = str(df.iloc[len(df) - 1, 10])
    customer_name = str(df.iloc[0, 2])

    # Rebuild date as YYYY-MM-DD for sort-friendly filenames
    inv_date_iso = '20' + pdate[-2:] + '-' + pdate[:2] + '-' + pdate[3:5]

    return {
        'agycode': agycode,
        'pdate': pdate,
        'inv_date_iso': inv_date_iso,
        'invoice_no': invoice_no,
        'invoice_amt': invoice_amt,
        'customer_name': customer_name,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    fs = FileService(ROOT, OUTPUTPATH)
    file_dict = fs.get_dependent_file_dict()
    fs.clear_destination_folder()

    sf_acct_df = pd.read_csv(file_dict['SFAcct'])
    sf_id_lookup: Dict[str, str] = (
        sf_acct_df
        .dropna(subset=['SCEIS_CODE__C'])
        .set_index('SCEIS_CODE__C')['ID']
        .to_dict()
    )

    # Split source PDF into individual page files
    reader = PdfReader(open(file_dict['BOInv'], 'rb'))
    for i in range(len(reader.pages)):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        page_path = os.path.join(OUTPUTPATH, f'document-page{i}.pdf')
        with open(page_path, 'wb') as out_stream:
            writer.write(out_stream)

    # Parse each page and build ContentVersion manifest
    cv_rows = []
    split_pages = fs.get_files_from_dir(altpath=OUTPUTPATH)

    for page_path in split_pages:
        fields = parse_pdf_page(page_path)

        title = build_title(
            fields['inv_date_iso'],
            fields['invoice_amt'],
            fields['customer_name'],
            fields['invoice_no'],
        )
        desc = (
            f"S&D Billing for services on {fields['pdate']}."
            f' Generated on {DATESTAMP}'
        )
        sf_id = sf_id_lookup[fields['agycode']]

        cv_rows.append({
            'Title': title,
            'Description': desc,
            'VersionData': page_path,
            'PathOnClient': page_path,
            'FirstPublishLocationId': sf_id,
        })

        print(
            f"Logging {fields['agycode']} Invoice Date {fields['pdate']}"
            f" {fields['invoice_no']} - {page_path}"
        )

    print('Creating manifest for ContentVersion')
    content_version_df = pd.DataFrame(cv_rows)
    content_version_df.to_csv(
        os.path.join(OUTPUTPATH, f'ContentVersion Generated On {DATESTAMP}.csv'),
        index=False,
    )

    fs.copy_file('pdfimportmap.sdl')
    print('Operation complete.')


if __name__ == '__main__':
    main()
