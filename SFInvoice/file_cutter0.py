import os
import re
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
UPPER_COUNTY_LIST = [x.upper() for x in PROPER_COUNTY_LIST]
# exceptions for algo fail
EXCEPTION_COUNTY = {'CHESTER': 'CHETCO', 'CHESTERFIELD': 'CHEKCO',
                    'CHEROKEE': 'CHERCO', 'GREENVILLE': 'GREVCO',
                    'GREENWOOD': 'GREWCO'}
EXCEPTION_COUNTY_LIST = list(EXCEPTION_COUNTY.keys())
# TODO - may not need
COUNTY_EXCEPTION_WORD_LIST = ['POLICE', 'PUBLIC SAFETY','PUBLIC SFTY',
                              'GOOSE CREEK CC/911','CALHOUN FALLS HIGH',
                              'GREENWOOD COUNTY SCH.DIST. 50','SCHOOL',
                              'DISTRICT','SCH DIST']
# re pattern for xxxx co/county
RE_COUNTY = re.compile(r'^[A-Z]+\W{1}CO[A-Z]*')
# keyword in contract description for subset agencies
B_AGYS = {'E240B': 'EMERGENCY',
          'H630B': 'FIRST STEPS',
          'N200B': 'CRIMINAL JUSTICE'}


def clear_destination_folder(filepath: str):
    # clears destination folder
    print('Clearing old data.')
    try:
        rmtree(filepath)
        os.mkdir(filepath)
    except:
        os.mkdir(filepath)

def copy_file_map(src: str, dest: str):
    # moves file from a folder to another
    # moves SF file mapping to DESKTOP_PATH
    copyfile(src, dest)

def get_files_from_dir(filepath: str, ext='.XLSX') -> list:
    # gathers files in root directory and returns only xlsx files
    filesindir = os.listdir(filepath)
    # tilda indicates open temp file, excluding these
    xlsxfiles = [root + f for f in filesindir if ext in f and '~' not in f]
    if len(xlsxfiles) == 0:
        print('No files found, try checking the extension.')
        return list()
    elif len(xlsxfiles) > 1:
        # returns more than 1
        print('WARNING: Multiple files are being processed.')
        return xlsxfiles
    else:
        # returns 1 file
        return xlsxfiles

def create_acct_code(data: str) -> str:
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
        # supreme ct
        if customer_number[-2:] == '16':
            return customer_number
        else:
            # city of columbia
            return '2160000'

    # other numerical accounts
    if contract_desc in ['RIVERBANKS ZOO',
                        'SC INTERACTIVE',
                        'SC EDUCATION LOTTERY',
                        'SC BAR ASSOCIATION',
                        'SC BAR ASSOCIATION - NON-BILLABLE']:
        return customer_number

    # counties -- TODO this new logic should work
    if re.search(RE_COUNTY,contract_desc):
        if first_word in COUNTY_EXCEPTION_WORD_LIST:
            return EXCEPTION_COUNTY.get(first_word)
        else:
            return firstword[:4]+'CO'
    else:
        # unwanted data
        return 'zzz'

def material_translate(material: str) -> str:
    # summarizes what it is in less than 3 words
    pass

def create_content_manifest(**args) -> file:
    # generates manifest for SF
    pass

''' dependent files '''
# exported invoice file(s)
xlsx_files = get_files_from_dir(ROOT)
# SF account IDs
try:
    sf_acct_ids = pd.read_csv(SF_ACCT_INFO)
except FileNotFoundError:
    print('extract.csv is missing from parent directory')


''' prepare aux data and outputs '''
# build dictionary because i don't know how to do this right
acctid_dict = {}
for index, row in accountids.iterrows():
    acctid_dict[row['SCEIS_CODE__C']] = row['ID']
# to convert float into currency string
float_format = "${:,.2f}".format
# create output file shape
content_version = pd.DataFrame(columns=['Title',
                                        'Description',
                                        'VersionData',
                                        'PathOnClient',
                                        'FirstPublishLocationId'])

''' process new files '''
clear_destination_folder(DESKTOP_PATH)

print('Gathering S&D outputs to parse.')

for x in xlsx_files:
    xdf = pd.read_excel(x)
    ''' data wrangling '''
    # convert customer number to str
    xdf['Customer'] = xdf['Customer'].apply(lambda x: str(x))
    xdf.dropna(subset=['Customer Name'], inplace=True)
    agy = xdf.copy()

    # create agycode if state agy number
    agy['AgyCode'] = agy.apply(create_AgyCode, axis=1)
    agy.drop(agy[agy['AgyCode'] == 'zzz'].index, inplace=True)
    # labeling OTCs
    agy.loc[(agy['Document Desc.'].isnull()),
            'Document Desc..'] = 'One Time Charge'


    # create list of agy/cust codes
    agycodes = agy['AgyCode'].drop_duplicates().tolist()

    for key, value in BAgys.items():
        # mark B agencies
        agy['AgyCode'].loc[agy['Document Desc.'].str.contains(value)] = key
        # to prevent sending empty dataframes for B agencies
        if not agy[agy['AgyCode'] == key].empty:
            agycodes.append(key)

    # loop through agycodes
    for agyc in agycodes:
        # create subset of original data
        subdf = agy[agy['AgyCode'] == agyc].copy()
        # get all contract numbers in agy
        sales_document_no_list = subdf['Sales Document #'].drop_duplicates()\
                                                          .tolist()
        # determine total number of invoice dates in agy
        invoice_dates_list = subdf['Invoice Date'].drop_duplicates().tolist()
