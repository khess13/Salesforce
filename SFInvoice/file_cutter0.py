import os
import re
import numpy as np
import pandas as pd
import datetime as dt
from pathlib import Path
from shutil import rmtree, copyfile
from getpass import getuser

# sets root one dir higher for dependent files
ROOT = str(Path(os.getcwd()).parents[0]) + '\\'
# dependencies
SD_MAP = ROOT + '\\SFInvoice\\SDMap.xlsx'
SF_ACCT_INFO = ROOT + '\\extract.csv'
# dep check
try:
    sd_map_df = pd.read_excel(SD_MAP)
# TODO - throws silence error
except FileNotFoundError:
    print('SD_Map.xlsx is missing')
try:
    sf_acct_ids = pd.read_csv(SF_ACCT_INFO)
    # because NA values
    sf_acct_ids.dropna(subset=['SCEIS_CODE__C'], inplace=True)
except FileNotFoundError:
    print('extract.csv is missing from parent directory')


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
                    'GREENWOOD': 'GREWCO', 'CHAS':'CHARCO', 'LEE': 'LEE CO'}
EXCEPTION_COUNTY_LIST = list(EXCEPTION_COUNTY.keys())
REMOVE_SCHOOL = ['SCHOOL','DISTRICT','SCH DIST']

# re pattern for xxxx co/county
RE_COUNTY = r'^[A-Z]+\W{1}CO[A-Z]*'
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
    xlsxfiles = [ROOT + f for f in filesindir if ext in f and '~' not in f]
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
    first_word = contract_desc[:contract_desc.find(' ')]

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
        # city of columbia
        return '2160000'
    #because gov school is being charged to 2 diff acct numbers
    if customer_number == '4003840':
        return 'H650'
    # other numerical accounts
    if contract_desc in ['RIVERBANKS ZOO',
                        'SC INTERACTIVE',
                        'SC EDUCATION LOTTERY',
                        'SC BAR ASSOCIATION',
                        'SC BAR ASSOCIATION - NON-BILLABLE']:
        return customer_number

    # counties
    if first_word in UPPER_COUNTY_LIST:
        #to filter out county school districts
        if re.search(RE_COUNTY, contract_desc):
            if first_word in EXCEPTION_COUNTY_LIST:
                return EXCEPTION_COUNTY.get(first_word)
            elif contract_desc in REMOVE_SCHOOL:
                return 'zzz'
            return first_word[:4]+'CO'
    else:
        # unwanted data
        return 'zzz'

# TODO -- finish this one? -- prob have a translation file
# have items that didn't translate as output?
def material_translate_create(sd=sd_map_df) -> dict:
    # summarizes what it is in less than 3 words
    material_trans_dict = {}
    unmatched = sd[sd['MaterialTranslate'].isna()].count()['Material']
    # unmatched entries check
    print(f'There are {unmatched} entries. Baseline is 36')
    #clear nans
    sd_map_df.dropna(subset=['MaterialTranslate'], inplace=True)
    # so inefficient...
    print('Building material dictionary')
    for index, row in sd_map_df.iterrows():
        material_trans_dict[row['Material']] = row['MaterialTranslate']
    return material_trans_dict

def material_trans_df(x) -> str:
    # supplement apply function to translate materials
    material = x['Material Desc.']
    try:
        return mat_trans_dict.get(material)
    except:
        return ''

''' dependent files '''
# exported invoice file(s)
xlsx_files = get_files_from_dir(ROOT)

''' prepare aux data and outputs '''
# build dictionary because i don't know how to do this right
acctid_dict = {}
for index, row in sf_acct_ids.iterrows():
    acctid_dict[row['SCEIS_CODE__C']] = row['ID']
# to convert float into currency string
float_format = "${:,.2f}".format
# create output file shape
content_version = pd.DataFrame(columns=['Title',
                                        'Description',
                                        'VersionData',
                                        'PathOnClient',
                                        'FirstPublishLocationId'])
mat_trans_dict = material_translate_create()

''' process new files '''
clear_destination_folder(DESKTOP_PATH)

print('Gathering S&D outputs to parse.')

agy_results_dict = {}
for x in xlsx_files:
    xdf = pd.read_excel(x)
    # get invoice date for file to fill in for nonbillable
    invoice_date_file = xdf.iloc[0,4]
    ''' data wrangling '''
    # convert customer number to str
    xdf['Customer'] = xdf['Customer'].apply(lambda x: str(x))
    # xdf.dropna(subset=['Document Desc.'], inplace=True)
    # labeling OTCs
    xdf.loc[(xdf['Document Desc.'].isnull()),
            'Document Desc.'] = 'One Time Charge'
    # because there are / in this field
    xdf['Document Desc.'] = xdf['Document Desc.']\
                                .apply(lambda x: x.replace('/','-'))
    # remove unnecessary columns
    xdf.drop(['Exception','Plant','Commitment Item','Fund',
              'FI Function Area','Grant','Cost_center','G/L Account'],
              axis=1, inplace=True)
    agy = xdf.copy()

    # fill in a date for nonbillable, picks up date from first instance
    # agy.loc[(agy['Invoice Date'].isnull()),
    #        'Invoice Date'] = agy.iloc[0,4]
    agy.loc[(agy['Invoice Date'].isnull()),
                 'Invoice Date'] = invoice_date_file
    # create agycode if state agy number
    agy['AgyCode'] = agy.apply(create_acct_code, axis=1)
    agy.drop(agy[agy['AgyCode'] == 'zzz'].index, inplace=True)
    # translate material
    agy['MaterialTranslate'] = agy.apply(material_trans_df, axis=1)
    # create list of agy/cust codes
    agycodes = agy['AgyCode'].drop_duplicates().tolist()

    for key, value in B_AGYS.items():
        # mark B agencies
        agy['AgyCode'].loc[agy['Document Desc.'].str.contains(value)] = key
        # to prevent sending empty dataframes for B agencies
        if not agy[agy['AgyCode'] == key].empty:
            agycodes.append(key)

    loop_count = 0
    # loop through agycodes
    for agyc in agycodes:
        # create subset of original data
        subdf = agy[agy['AgyCode'] == agyc].copy()
        # get all contract numbers in agy
        sales_document_no_list = subdf['Sales Document #'].drop_duplicates()\
                                                          .tolist()
        # determine total number of invoice dates in agy
        invoice_dates_list = subdf['Invoice Date'].drop_duplicates().tolist()

        # make shared services list/dict
        # subset frame to remove null/none values; then designate col tolist()
        serv_list = subdf[subdf['MaterialTranslate'].notnull()]\
                               ['MaterialTranslate'].drop_duplicates().tolist()
        # added sorted() to make a-z
        serv_string = '\n'.join(sorted(serv_list))
        agy_results_dict[agyc] = serv_string

        # loop through invoice dates
        # because they didn't include invoice number....?
        # TODO - get this to show an error for no invoice no
        if type(invoice_dates_list) == float:
            print('No Invoice Date')
        for inv in invoice_dates_list:
            sub2df = subdf[subdf['Invoice Date'] == inv].copy()
            if sub2df.empty:
                continue

            for sales in sales_document_no_list:
                sub3df = sub2df[sub2df['Sales Document #'] == sales].copy()
                if sub3df.empty:
                    continue
                # file variables
                agycode = agyc
                pdate = inv.strftime('%m-%d-%Y')
                gendate = TODAY_DATESTAMP
                desc = 'S&D billing for services on '\
                        + pdate\
                        + '. Generated on '\
                        + gendate
                sales_doc_no = str(int(sales))

                # pick first not null customer name
                # sales_contract_desc = sub2df.iloc[0,1]
                sales_contract_desc_list = sub3df['Document Desc.']\
                                                    .drop_duplicates()\
                                                    .tolist()

                if sub3df.iloc[0,3] == 'One Time Charge':
                    customername = sales_contract_desc_list[1]
                else:
                    customername = sales_contract_desc_list[0]

                # file identifiers
                invoiceamt = float_format(round(sub3df['Net Value'].sum(), 2))
                tdate = '20'+pdate[-2:]\
                        + '-' + pdate[:2]\
                        + '-' + pdate[3:5]

                filename = tdate + ' - '\
                    + invoiceamt + ' - '\
                    + customername\
                    + ' - Sales Doc ' + sales_doc_no\
                    + ' - Shared Services.xlsx'
                titledate = filename[:-5]
                printfilename = agycode\
                    +' Invoice Date '\
                    + pdate + ' '\
                    + customername

                # gets Salesforce ID for account
                idofaccount = acctid_dict[agycode]

                # generating ContentVersion manifest
                content_version.loc[loop_count] = [titledate,
                                                desc,
                                                DESKTOP_PATH + filename,
                                                DESKTOP_PATH + filename,
                                                idofaccount]
                loop_count +=1

                # drop identifier columns
                sub3df.drop(['AgyCode','MaterialTranslate'], axis=1,
                             inplace=True)
                # export file to excel file and save
                with pd.ExcelWriter(DESKTOP_PATH + filename) as writer:
                    sub3df.to_excel(writer, index=False)
                print('Creating ' + filename)

print('Creating manifest for ContentVersion')
content_version.to_csv(DESKTOP_PATH
                      + 'ContentVersion Generated On '
                      + TODAY_DATESTAMP
                      + '.csv', index=False)

# adding null values for accounts w/o billing
for agy in acctid_dict.keys():
    if agy not in agy_results_dict.keys():
        agy_results_dict[agy] = ' '

print('Creating shared services list')
shared_services_df = pd.DataFrame.from_dict(agy_results_dict, orient='index',
                                            columns=['Service'])
shared_services_df.reset_index(level=0, inplace=True)
#add agycode column
shared_services_df.columns = ['AgyCode','Service']
shared_services_df.replace('', np.nan, inplace=True)
shared_services_df.dropna(subset=['Service'], inplace=True)
#add Salesforce IDs
for agy, sfid in acctid_dict.items():
    shared_services_df.loc[shared_services_df['AgyCode'] == agy,\
                                        'SalesforceAcctID'] = sfid
shared_services_df.to_csv(DESKTOP_PATH+'exportSharedServices.csv', index=False)

copy_file_map(ROOT+'\\pdfimportmap.sdl', DESKTOP_PATH+'\\pdfimportmap.sdl')
copy_file_map(ROOT+'DTO Services\\dtoservices.sdl',\
              DESKTOP_PATH+'\\dtoservices.sdl')


print('Operation Complete!')
