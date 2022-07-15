import os
import pandas as pd
import datetime as dt
import pathlib import Path
from shutil import rmtree, copyfile
from getpass import getuser

# sets root one dir higher for dependent files
ROOT = str(Path(os.getcwd()).parents[0]) + '\\'
SF_ACCT_INFO = ROOT + '\\extract.csv'
TODAY_DATESTAMP = str(dt.datetime.now().strftime('%m-%d-%Y'))
# for windows10 users, getuser returns current user
DESKTOP_PATH = 'C:\\Users\\'+getuser()+'\\Desktop\\FileDrop\\'

# global data sets
PROPER_COUNTY_LIST = ['Abbeville', 'Aiken', 'Allendale', 'Anderson', 'Bamberg',
                 'Barnwell', 'Beaufort', 'Berkeley', 'Calhoun', 'Charleston',
                 'Cherokee', 'Chester', 'Chesterfield', 'Clarendon', 'Colleton',
                 'Darlington', 'Dillon', 'Dorchester', 'Edgefield', 'Fairfield',
                 'Florence', 'Georgetown', 'Greenville', 'Greenwood', 'Hampton',
                 'Horry', 'Jasper', 'Kershaw', 'Lancaster', 'Laurens', 'Lee',
                 'Lexington', 'Marion', 'Marlboro', 'McCormick', 'Newberry',
                 'Oconee', 'Orangeburg', 'Pickens', 'Richland', 'Saluda',
                 'Spartanburg', 'Sumter', 'Union', 'Williamsburg', 'York']
UPPER_COUNTY_LIST = [x.upper() for x in PROPER_COUNTY]
# exceptions for algo fail
EXCEPTION_COUNTY = {'CHESTER': 'CHETCO', 'CHESTERFIELD': 'CHEKCO',
                    'CHEROKEE': 'CHERCO', 'GREENVILLE': 'GREVCO',
                    'GREENWOOD': 'GREWCO'}
EXCEPTION_COUNTY_LIST = list(EXCEPTION_COUNTY.keys())
COUNTY_EXCEPTION_WORD_LIST = ['POLICE', 'PUBLIC SAFETY','PUBLIC SFTY',
                              'GOOSE CREEK CC/911','CALHOUN FALLS HIGH',
                              'GREENWOOD COUNTY SCH.DIST. 50','SCHOOL',
                              'DISTRICT','SCH DIST']
# keyword in contract description for subset agencies
B_AGYS = {'E240': 'EMERGENCY',
          'H630': 'FIRST STEPS',
          'N200': 'CRIMINAL JUSTICE'}


def clear_destination_folder(filepath):
    # clears destination folder
    print('Clearing old data.')
    try:
        rmtree(filepath)
        os.mkdir(filepath)
    except:
        os.mkdir(filepath)

def copy_file_map(src, dest):
    # moves file from a folder to another
    # moves SF file mapping to DESKTOP_PATH
    copyfile(src, dest)

def get_files_from_dir(filepath, ext='.XLSX') -> list:
    # gathers files in root directory and returns only xlsx files
    filesindir = os.listdir(filepath)
    # tilda indicates open temp file, excluding these
    xlsxfiles = [root + f for f in filesindir if ext in f and '~' not in f]
    if len(xlsxfiles) == 0:
        print('No files found, try checking the extension.')
    elif len(xlsxfiles) > 1:
        print('Found more than 1 excel file. Check directory.')
    else:
        return xlsxfiles

def create_acct_code(data) -> str:
    # does easy and complicated mapping for SF acct codes
    contract_desc = data['Document Desc.']
    customer_number = data['Customer']
    customer_number_first_four = customer_number[:4]
    customer_number_len = len(customer_number)
    sceis_agy_code = None
    first_word = contract_desc[:customer.find(' ')]

    # make all the acct codes same length
    if customer_number_len == 10:
        customer_number = customer_number[3:]
        customer_number_first_four = customer_number[:4]
        customer_number_len = len(customer_number)

    # because BOFI is same and different
    if customer_number_first_four == 'R230':
        if customer_number == 'R230001':
            # consumer finance division
            return 'R230B'
        else:
            # bank examining division
            return 'R230'

    # return A000 pattern if first value is alpha
    if customer_number[:1].isalpha():
        return customer_number_first_four

    # city of columbia acct and supreme court have the same sequence
    if customer_number_first_four == '2160':
        if customer_number[-2:] == '16':
            return customer_number
        else:
            return '2160000'

    # other numerical accounts
    if customer in ['RIVERBANKS ZOO',
                    'SC INTERACTIVE',
                    'SC EDUCATION LOTTERY',
                    'SC BAR ASSOCIATION',
                    'SC BAR ASSOCIATION - NON-BILLABLE']:
        return customer_number

    if first_word in UPPER_COUNTY_LIST:
        # TODO - finish logic for county exceptions 

def material_translate(material) -> str:
    # summarizes what it is in less than 3 words
    pass

def create_content_manifest(**args) -> file:
    # generates manifest for SF
    pass
