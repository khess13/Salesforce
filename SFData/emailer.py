"""Sends copy of ECC data to Scott"""
import datetime as dt
from os import getcwd
import outlook
from FileService import FileService

ROOT = getcwd()
OUTPUTPATH = ROOT
EMAIL_ADD = 'scott.broam@admin.sc.gov'
TODAY_DATE = dt.datetime.now()
MONTH_NAME = TODAY_DATE.strftime("%B")

fs = FileService(ROOT,OUTPUTPATH)
FS_FILE_DICT = fs.get_dependent_file_dict()
attachment_location = FS_FILE_DICT.get('ECCInv')

ans = input(f'Is the current month {MONTH_NAME}? y/n')
if ans == 'n':
    MONTH_NAME = input('Enter month name:')

mailer = outlook.emailMessage(subject=f'ECC Billing Data for {MONTH_NAME}',
                              emailbody = 'Please see attached.', 
                              toAddress = EMAIL_ADD,
                              attachmentPath = attachment_location)
mailer.send()