"""Sends a copy of ECC billing data to the billing contact."""
from __future__ import annotations

import datetime as dt
import os

import outlook
from FileService import FileService

ROOT = os.getcwd()
EMAIL_ADDRESS = 'scott.broam@admin.sc.gov'


def get_month_name() -> str:
    """Return the current month name, with an override prompt if needed."""
    month_name = dt.datetime.now().strftime('%B')
    answer = input(f'Is the current month {month_name}? y/n: ')
    if answer.strip().lower() == 'n':
        month_name = input('Enter month name: ')
    return month_name


def main() -> None:
    fs = FileService(ROOT, ROOT)
    file_dict = fs.get_dependent_file_dict()
    attachment_path = file_dict['ECCInv']
    month_name = get_month_name()

    mailer = outlook.EmailMessage(
        subject=f'ECC Billing Data for {month_name}',
        email_body='Please see attached.',
        to_address=EMAIL_ADDRESS,
        attachment_path=attachment_path,
    )
    mailer.send()
    print('Email sent.')


if __name__ == '__main__':
    main()
