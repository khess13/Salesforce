"""
Generates file to update headcount stat in SF
"""
import os
import datetime as dt
import pandas as pd
from FileService import FileService

ROOT = os.getcwd()
OUTPUTPATH = ROOT + '\\Headcount\\'
fs = FileService(ROOT,OUTPUTPATH)
FS_ACCT_DICT = fs.get_dependent_file_dict()
DATESTAMP = str(dt.datetime.now().strftime('%m-%d-%Y'))
TARGET_FIELD = 'NUMBEROFEMPLOYEES'

#  dependent files
SF_ACCT_DICT = pd.read_csv(FS_ACCT_DICT.get('SFAcct'))

# get all xlsx in root
XLSX = fs.get_files_from_dir(ext='xlsx')
fs.clear_destination_folder()
xdf = pd.read_excel(FS_ACCT_DICT.get('HR'))


#build dictionary because i don't know how to do this right
acctid_dict = {}
for index, row in SF_ACCT_DICT.iterrows():
    acctid_dict[row['SCEIS_CODE__C']] = row['ID']

filename = 'Headcount - Created on ' + DATESTAMP + '.csv'
for index, row in xdf.iterrows():
    try:
        xdf.loc[index, 'SalesforceAcctID'] = acctid_dict[row['Personnel Area - Key']]
    except Exception:
        continue
#drop personnel areas without SalesforceAcctID
xdf.dropna(subset=['SalesforceAcctID'], inplace=True)
xdf.to_csv(OUTPUTPATH+filename, index=False)

fs.copy_file('hc.sdl')

print('Ops complete!')
