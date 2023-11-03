"""
Generates updates for Admin Srvs and Agy-mgmed fields
"""
import os
import numpy as np
import pandas as pd
from FileService import FileService

ROOT = os.getcwd()
OUTPUTPATH = ROOT + '\\Services\\'
fs = FileService(ROOT,OUTPUTPATH)
FS_FILES_DICT = fs.get_dependent_file_dict()
fs.clear_destination_folder()

# caused '...' from long strings on output without setting
pd.set_option('display.max_colwidth', None)

# load dependent files
contracts_file = pd.read_csv(FS_FILES_DICT.get('Contracts'),
                             encoding='iso-8859-1') #bc excel
sf_acct_info = pd.read_csv(FS_FILES_DICT.get('SFAcct'))
# update if scope creeps
ADMIN_SRVS = ['Administrative']
SF_ACCT_DICT = {}
for index, row in sf_acct_info.iterrows():
    SF_ACCT_DICT[row['SCEIS_CODE__C']] = row['ID']

# clean up SF acct data
sf_acct_info.dropna(subset=['SCEIS_CODE__C'], inplace=True)
AGY_CODE_LIST = sf_acct_info['SCEIS_CODE__C'].drop_duplicates().tolist()

# survey data TODO - move this somewhere?
#updated 3-2021 -- ARM Survey
msExchange = ['E200', 'L460', 'N200', 'D500', 'H790', 'P320', 'N040', 'H630',
              'R360', 'J120', 'R400', 'P240', 'N080', 'R440', 'U120', 'P120',
              'B040', 'A170','P360', 'F500', 'E190', 'H670', 'D100', 'H750', 
              'L040', 'H730','P260']

#updated 4-2021 -- ARM Survey
selfManagedVPN = ['P280', 'J020', 'R360', 'J120', 'J160', 'N040', 'E200', 'P320',
                  'R450', 'H790', 'N080']

#updated 5-2021 -- ARM Survey
selfManagedFirewall = ['A200', 'c0002160016', 'C050', 'D100', 'E080', 'E190', 
                       'E200','E240', 'E240B', 'E500', 'F500', 'H590', 'H630', 
                       'H670','H710', 'H730', 'H750', 'H790','H870', 'H950',
                       'J020', 'J040', 'J120', 'J160', 'K050', 'L040', 'L060', 
                       'L120','L320','N040', 'N080', 'N120', 'N200', 'P120', 
                       'P240','P260', 'P280', 'P320', 'P450', 'R120','R200', 
                       'R360','R400', 'R440', 'R600', 'U120', 'U150', 'P260']

#updated 5-2021, 3-2023 -- ARM Survey --- added more 11/2022
nonDTOInternet = ['A010', 'A050', 'A150', 'A170', 'A200', 'B040', 'E190', 
                  'E240B','H530', 'H590', 'H640', 'H650', 'H750', 'J040', 
                  'L120', 'N120', 'P260', 'P360', 'P450','U150', 'U200', 
                  'Y140', 'R600', '3599957', 'P280', 'H730', 'J160', 'L320', 
                  'E260', 'L080','P240', 'U120', '4002072', 'D100', 'J020', 
                  'R200']

#updated 6-2021 -- DIS survey
agyO365Email = ['D100', 'D250', 'D300', 'D500', 'E080', 'E120', 'E190', 'E200', 
                'E240','E240B', 'E260', 'F500', 'H630', 'H670', 'H870', 'H950', 
                'J020', 'J040', 'J120', 'J160','J200', 'K050', 'L040', 'L060', 
                'L080', 'L120', 'L360', 'N040', 'N080', 'N120', 'N200','P160', 
                'P240', 'P280', 'P320', 'P360', 'P450', 'R040', 'R060', 
                'R080', 'R120','R200', 'R360', 'R400', 'R600', 'U120','H590',
                'E500']

agyOneDrive = ['D100', 'E190', 'E200', 'E240B', 'H630', 'H670', 'J020', 'J120', 
               'L040','L120', 'P280', 'P320', 'P450', 'R080', 'R200', 'R400', 
               'R600']

agySharepoint = ['E190', 'E240B', 'H670', 'J020', 'J120', 'L040', 'N120', 'P280',
                 'P320', 'P450', 'R600', 'U120']

#updated 10-2021
voipATT = ['GA', 'N080', 'R600', 'H590', 'E240B', 'R360']

voipNWN = ['J040', 'U120', 'F500', 'R080', 'H710', 'P160', 'R440', 'T360', 
           'H650','H640', 'H470', 'L040', 'K050']

voipSegra = ['c0004002072', 'A200', 'A850', 'C050', 'D050', 'D100', 'D170', 
             'D200','D250', 'E040', 'E080', 'E120', 'E160', 'E190', 'E200', 
             'E210', 'E230', 'E240', 'E280','E500', 'E550', 'D500', 'D300', 
             'H960', 'F270', 'BARNCO', 'CHETCO', 'DARLCO', 'H030','H060', 
             'H090', 'H120', 'H150', 'H170', 'H270', 'H510', 'H590', 'H630B', 
             'H630', 'H670','T200', 'T220', 'T260', 'T100', 'T140', 'T160', 
             'T120', 'H730', 'H750', 'H790', 'H870','H910', 'H950', 'J020', 
             'J040', 'J120', 'J160', 'J200', 'K050', 'L040', 'L240', 'L320',
             'L360', 'L400', 'L460', 'L080', 'N040', 'N080', 'N120', 'N200', 
             'P120', 'P240', 'P260','P280', 'P320', 'P400', 'R040', 'R060', 
             'R120', 'R200', 'R230', 'R230B', 'R280', 'R360',
             'R400', 'R440', 'R520', 'S600', 'U300', 'U120', 'c0003599957']



# contracts processing
id_and_contract = contracts_file[['ACCOUNTID', 'CONTRACT_TYPE__C',
                                  'ADMINISTRATIVE_SERVICES__C']]\
                                  .drop_duplicates()
contract_update = id_and_contract[id_and_contract['CONTRACT_TYPE__C']
                                  .isin(ADMIN_SRVS)]\
                                  .dropna(subset=['ADMINISTRATIVE_SERVICES__C'])\
                                  .copy()
contract_update = contract_update.rename(columns={'ACCOUNTID': 'SalesforceAcctID',
                                                  'CONTRACT_TYPE__C': 'CService',
                                                  'ADMINISTRATIVE_SERVICES__C': 'Service'})
contract_sfid_list = contract_update['SalesforceAcctID']\
                                     .drop_duplicates()\
                                     .tolist()
CONTRACT_DICT = {}
for sfid in contract_sfid_list:
    # clear frame
    contract_df = pd.DataFrame()
    contract_df = contract_update[contract_update['SalesforceAcctID'] == sfid]\
                                  .copy()
    # toss empty frames
    if contract_df.empty:
        continue

    contract_list = []
    # some contracts have overlap with functions, /n is result of to_string for rows
    contract_list = contract_df['Service'].to_string(index=False)\
                                          .replace('\n', ';')\
                                          .split(';')
    # remove whitespace and condense contract types -- b/c overlap
    contract_list_clean = set([c.strip() for c in contract_list])

    CONTRACT_DICT[sfid] = '\n'.join(contract_list_clean)

# creating service files
# agy_results = {}
ancillaryServices = {}
#wrapped in quotes on csv should make line breaks
for agy in AGY_CODE_LIST:
    anSrv = []
    #removed file since output is only contracts and agymgmt srvs
    #subset on agycode
    '''
    og_df = excel_file[excel_file['AgyCode'] == agy]
    serv_list = og_df['Service'].tolist()
    '''
    # keep alpha order
    if agy in voipATT:
        anSrv.append('AT&T VoIP')
    if agy in selfManagedFirewall:
        anSrv.append('Firewall')
    if agy in nonDTOInternet:
        anSrv.append('Internet')
    if agy in msExchange:
        anSrv.append('On-prem MS Exchange')
    if agy in agyO365Email:
        anSrv.append('O365 Email')
    if agy in agyOneDrive:
        anSrv.append('O365 OneDrive')
    if agy in agySharepoint:
        anSrv.append('O365 SharePoint')
    if agy in voipNWN:
        anSrv.append('NWN VoIP')
    if agy in selfManagedVPN:
        anSrv.append('Pulse VPN')
    if agy in voipSegra:
        anSrv.append('Segra VoIP')
    else:
        anSrv.append(' ')

    #format service into 1 line with formula line breaks
    # removed since getting services in other script
    # serv_string = '\n'.join(serv_list)
    an_string = '\n'.join(anSrv)

    # agy_results[agy] = serv_string
    ancillaryServices[agy] = an_string

    #resultsList = [agy_results, ancillaryServices]
    resultsList = [ancillaryServices]

# add contract data if avail
if len(CONTRACT_DICT) > 0:
    resultsList.append(CONTRACT_DICT)

# check services returned
if len(set(resultsList[0].values())) == 1:
    print('WARNING: No services found in file')

print('Mashing Results')
for result in resultsList:
    CODE_TYPE = 'AgyCode'

    # pick first key to sample length of key string
    # 18 char == SF Id
    if len(list(result.keys())[0]) == 18:
        CODE_TYPE = 'SalesforceAcctID'
    finished = pd.DataFrame.from_dict(result, 
                                      orient='index', 
                                      columns=['Service'])
    finished.reset_index(level=0, inplace=True)
    finished.columns = [CODE_TYPE, 'Service']
    #drop blank services
    finished.replace('', np.nan, inplace=True)
    finished.dropna(subset=['Service'], inplace=True)

    #add Salesforce IDs
    for agy, sfid in SF_ACCT_DICT.items():
        # switch between available ids to fill in missing data 
        if CODE_TYPE == 'SalesforceAcctID':
            finished.loc[finished['SalesforceAcctID'] == sfid, 'AgyCode'] = agy
        else:
            finished.loc[finished['AgyCode'] == agy, 'SalesforceAcctID'] = sfid
        # add null accounts
        if finished[finished['AgyCode'] == agy].empty:
            finished.loc[finished.shape[0]+1, ['AgyCode',
                                               'SalesforceAcctID', 
                                               'Service']] = agy, sfid, ''

    #if resultsList.index(result) == 0:
    #    EXPORT_NAME = 'DNUexportSharedServices.csv'
    if resultsList.index(result) == 0:
        EXPORT_NAME = 'exportAgencyServices.csv'
    else:
        EXPORT_NAME = 'exportContracts.csv'

    print('Exporting to CSV')
    finished.to_csv(OUTPUTPATH+EXPORT_NAME, index=False)

    #move sdls
    fs.copy_file('contract_services.sdl')
    fs.copy_file('agencyservices.sdl')

print('Done!')
