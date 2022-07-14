import pandas as pd
import datetime as dt
import os
import shutil
import getpass
from pathlib import Path


def copyFileMap(src, dest):
    # copy map from SF to Desktop file folder
    shutil.copyfile(src, dest)


def get_files_from_dir(filepath, ext='.XLSX') -> list:
    # gathers files in root directory and returns only xlsx files
    filesindir = os.listdir(filepath)
    # tilda indicates open temp file, excluding these
    xlsxfiles = [root + f for f in filesindir if ext in f and '~' not in f]
    if len(xlsxfiles) == 0:
        print('No files found, try checking the extension.')
    else:
        return xlsxfiles


def clear_destination_folder(filepath):
    # clears destination folder
    print('Clearing old data.')
    try:
        shutil.rmtree(filepath)
        os.mkdir(filepath)
    except:
        os.mkdir(filepath)

# TODO -- remove logic for C+
def create_AgyCode(data) -> str:
    # logic for coding county entries
    # groups counties, skips changing cities/towns (leaves customer no alone)
    # creates matching SCEIS code for list
    customer = data['Customer Name']
    # custno = '000' + data['Customer']
    custno = data['Customer']
    firstwordpos = customer.find(' ')
    firstword = customer[:firstwordpos]
    x = None
    sc = None

    # because BOFI is acct names are the same and different
    if custno[:4] == 'R230':
        # Consumer Finance Division
        if customer == 'STATE BOARD OF FINANCIAL INSTITUTIO':
            return 'R230B'
        else:
            # Bank Examining Division
            return 'R230'
    # checks first letter is alpha
    # returns SCEIS code
    elif custno[:1].isalpha():
        sc = custno[:4]
        return sc
    # city of columbia variations
    elif 'CITY OF COLUMBIA' in customer:
        return '2160000'  # because there's multiple acct numbers
    # return numerical acct number for these non-SCEIS accts
    elif customer in ['SUPREME COURT COMMISSION ON CLE',
                      'RIVERBANKS ZOO & GARDEN',
                      'SOUTH CAROLINA INTERACTIVE',
                      'SC EDUCATION LOTTERY COMM']:
        # trim off beginning 000
        return str(custno)[3:]
    # other cities and towns
    elif customer.startswith('CITY OF') or customer.startswith('TOWN OF'):
        return 'zzz'  # 'c'+custno
    # trash for now
    # city police depts, explicit list
    elif 'POLICE' in customer or\
         'PUBLIC SAFETY' in customer or\
         'PUBLIC SFTY' in customer:
        return 'zzz'
    # Goose Creek 911, etc
    elif customer in ['GOOSE CREEK CC/911',
                      'COLUMBIA-RICHLAND 911 COMMUNICATION',
                      'CALHOUN FALLS HIGH', 'GREENWOOD COUNTY SCH.DIST. 50']:
        return 'zzz'  # 'c'+custno
    # remove school districts
    elif 'SCHOOL' in customer or\
         'DISTRICT' in customer or\
         'SCH DIST' in customer:
        return 'zzz'
    # counties that are the same shortned, had to make them different
    elif firstword in countywhylist:
        x = countywhy.get(firstword)
        return x
    # county operations
    elif 'COUNTY' in customer or '911' in customer or 'SHERIFF' in customer:
        x = customer[:4]+'CO'
        return x
    # otherwise if it's a county
    elif firstword in counties:
        x = firstword[:4]+'CO'
        return x
    else:
        # don't care/don't want
        return 'zzz'


# additional county stuff
counties = ['Abbeville', 'Aiken', 'Allendale', 'Anderson', 'Bamberg',
            'Barnwell', 'Beaufort', 'Berkeley', 'Calhoun', 'Charleston',
            'Cherokee', 'Chester', 'Chesterfield', 'Clarendon', 'Colleton',
            'Darlington', 'Dillon', 'Dorchester', 'Edgefield', 'Fairfield',
            'Florence', 'Georgetown', 'Greenville', 'Greenwood', 'Hampton',
            'Horry', 'Jasper', 'Kershaw', 'Lancaster', 'Laurens', 'Lee',
            'Lexington', 'Marion', 'Marlboro', 'McCormick', 'Newberry',
            'Oconee', 'Orangeburg', 'Pickens', 'Richland', 'Saluda',
            'Spartanburg', 'Sumter', 'Union', 'Williamsburg', 'York']
counties = [x.upper() for x in counties]
countywhy = {'CHESTER': 'CHETCO', 'CHESTERFIELD': 'CHEKCO',
             'CHEROKEE': 'CHERCO', 'GREENVILLE': 'GREVCO',
             'GREENWOOD': 'GREWCO'}
countywhylist = list(countywhy.keys())

# logic to update for B SCEIS codes
# target agy : keyword in contract desc to signal B agency
BAgys = {'E240': 'EMERGENCY',
         'H630': 'FIRST STEPS',
         'N200': 'CRIMINAL JUSTICE'}
# 'R230' : 'CONSUMER FINANCE' because everything is different for this

# root will get current working directory
root = str(Path(os.getcwd()).parents[0]) + "\\"
#  dependent files
account_loc = root + '\\extract.csv'
datestamp = str(dt.datetime.now().strftime('%m-%d-%Y'))

# outputpath = root + '\\Cut Files\\'
# because the cloud is fucking with my vibes
# gets current userId, hope you have a Desktop
currID = getpass.getuser()
outputpath = 'C:\\Users\\'+currID+'\\Desktop\\FileDrop\\'
clear_destination_folder(outputpath)

# get all xlsx in root
xlsx = get_files_from_dir(root)
# set up format of manifest for ContentVersion
contentVersion = pd.DataFrame(columns=['Title', 'Description', 'VersionData',
                                       'PathOnClient',
                                       'FirstPublishLocationId'])

# get account IDs by SCEIS code from Salesforce csv
try:
    accountids = pd.read_csv(account_loc)
except:
    print('extract.csv is missing from parent directory')

# build dictionary because i don't know how to do this right
acctid_dict = {}
for index, row in accountids.iterrows():
    acctid_dict[row['SCEIS_CODE__C']] = row['ID']
# to convert float into currency string
float_format = "${:,.2f}".format

print('Gathering S&D outputs to parse.')
for x in xlsx:
    # open file, put in DataFrame
    xdf = pd.read_excel(x)

    # change customer field to str

    xdf['Customer'] = xdf['Customer'].apply(lambda x: str(x))
    xdf.dropna(subset=['Customer Name'], inplace=True)
    agy = xdf.copy()

    # create agycode if state agy number
    # fix this so i can choose which column i want
    agy['AgyCode'] = agy.apply(create_AgyCode, axis=1)

    # drop customers zzz
    agy.drop(agy[agy['AgyCode'] == 'zzz'].index,
             inplace=True)  # figure out how to drop

    # create list of agy/cust codes
    agycodes = agy['AgyCode'].drop_duplicates().tolist()

    # labeling blank lines to mark one time charges
    agy.loc[(agy['Contract Desc.'].isnull()),
            'Contract Desc.'] = 'One Time Charge'

    for key, value in BAgys.items():
        bkey = key + 'B'
        # agy['AgyCode'].loc[agy['Contract Desc.'].str.contains(value)] = bkey
        agy['AgyCode'].loc[agy['Customer Name'].str.contains(value)] = bkey
        # wiring['AgyCode'].loc[agy['Contract Desc.'].str.contains(value,
        # na=False)] = bkey
        # to prevent sending empty dataframes for B agencies
        if not agy[agy['AgyCode'] == bkey].empty:
            agycodes.append(bkey)
    # debug
    # agy.to_csv(outputpath + 'debug.csv')

    # cut spreadsheets by agycode
    for agyc in agycodes:
        # testing
        # if agyc != 'R230B':
        #     continue

        # create subset of original data
        subdf = agy[agy['AgyCode'] == agyc].copy()
        # get all contract numbers in agy
        salescontract = subdf['Sales Contract#'].drop_duplicates().tolist()
        # determine total number of posting dates in agy
        postingdaterange = subdf['Posting Date'].drop_duplicates().tolist()

        for cont in salescontract:
            sub2df = subdf[subdf['Sales Contract#'] == cont].copy()
            if sub2df.empty:
                continue
            for date in postingdaterange:
                # sub on date
                sub3df = sub2df[sub2df['Posting Date'] == date].copy()
                if sub3df.empty:
                    continue

                # make files idenifiers
                agycode = agyc
                pdate = date.strftime('%m-%d-%Y')
                gendate = datestamp
                desc = 'S&D billing for services on ' + pdate +\
                       '. Generated on ' +\
                       gendate
                # pick first not null customer name
                customername = sub3df.iloc[0, 1]

                contractdesclist = sub3df['Contract Desc.'].drop_duplicates(
                ).tolist()
                # because some have a number with no other info
                if len(contractdesclist) == 0:
                    # [] column // [[]] rows
                    desc = sub3df.iloc[0, 1]
                else:
                    # avoid one time charge as label
                    if contractdesclist[0] == 'One Time Charge':
                        try:
                            desc = contractdesclist[1]
                        except:
                            desc = contractdesclist[0]
                    else:
                        desc = contractdesclist[0]

                # file identifiers
                invoiceno = str(sub3df.iloc[0, 4])[:-2]  # remove .0
                invoiceamt = float_format(round(sub3df['Net Value'].sum(), 2))
                tdate = '20'+pdate[-2:]\
                        + '-' + pdate[:2]\
                        + '-' + pdate[3:5]

                filename = tdate + ' - '\
                    + invoiceamt + ' - '\
                    + str(cont)\
                    + ' - Shared Services.xlsx'
                titledate = tdate + ' - '\
                    + invoiceamt + ' - '\
                    + desc\
                    + ' - Shared Services'
                printfilename = agycode +\
                    ' Invoice Date ' +\
                    pdate + ' ' +\
                    desc

                # gets Salesforce ID for account
                idofaccount = acctid_dict[agycode]
                # generating ContentVersion manifest
                nextentry = pd.Series([titledate,
                                       desc,
                                       outputpath + filename,
                                       outputpath + filename,
                                       idofaccount],
                                      index=contentVersion.columns)
                contentVersion = contentVersion.append(
                                                nextentry,
                                                ignore_index=True)

                # export file to excel file and save
                with pd.ExcelWriter(outputpath + filename) as writer:
                    sub3df.to_excel(writer, index=False)
                print('Creating ' + filename)

print('Creating manifest for ContentVersion')
contentVersion.to_csv(outputpath
                      + 'ContentVersion Generated On '
                      + datestamp
                      + '.csv', index=False)

copyFileMap(root+'\\pdfimportmap.sdl', outputpath+'\\pdfimportmap.sdl')

print('Operation Complete!')
