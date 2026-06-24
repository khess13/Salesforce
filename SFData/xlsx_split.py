from __future__ import annotations
"""
Splits xlsx into individual files for upload
Creates ContentVersion for SF Dataloader
Fills in missing data and dates from ECC
Aligns account numbers for SF consumption
Creates services recap for each account -- for billable and nonbillable
"""
import os
import re
import datetime as dt
from getpass import getuser
import numpy as np
import pandas as pd
from FileService import FileService
from jinja2 import Template
from weasyprint import HTML

ROOT = os.getcwd()
DATESTAMP = str(dt.datetime.now().strftime('%m-%d-%Y'))
CURR_ID = getuser()
# formerly to user desktop, avoid onedrive nagging
OUTPUTPATH = 'C:\\Users\\'+CURR_ID+'\\XLSDrop\\'
TODAY_DATESTAMP = str(dt.datetime.now().strftime('%m-%d-%Y'))

# Load dependent files
fs = FileService(ROOT, OUTPUTPATH)
FS_FILE_DICT = fs.get_dependent_file_dict()
SF_ACCT_INFO = pd.read_csv(FS_FILE_DICT.get('SFAcct'))
SD_MAP_DF = pd.read_excel(FS_FILE_DICT.get('SDMap'))

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
# to convert float into currency string
float_format = "${:,.2f}".format
UPPER_COUNTY_LIST = [x.upper() for x in PROPER_COUNTY_LIST]
# exceptions for algo fail
EXCEPTION_COUNTY = {'CHESTER': 'CHETCO', 'CHESTERFIELD': 'CHEKCO',
                    'CHEROKEE': 'CHERCO', 'GREENVILLE': 'GREVCO',
                    'GREENWOOD': 'GREWCO', 'CHAS': 'CHARCO', 'LEE': 'LEE CO'}
EXCEPTION_COUNTY_LIST = list(EXCEPTION_COUNTY.keys())
REMOVE_SCHOOL = ['SCHOOL', 'DISTRICT', 'SCH DIST']

# re pattern for xxxx co/county
RE_COUNTY = r'^[A-Z]+\W{1}CO[A-Z]*'
# keyword in contract description for subset agencies
B_AGYS = {'E240B': 'EMERGENCY',
          # 'H630B': 'FIRST STEPS', became own agency
          'N200B': 'CRIMINAL JUSTICE'}

# load the template once
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "recap_template.html")
with open(_TEMPLATE_PATH, encoding="utf-8") as _f:
    RECAP_TEMPLATE = Template(_f.read())

def service_id_update(costing_df, invoice_df) -> pd.DataFrame:
    """Fill blank invoice Service IDs from costing 'External Text',
    matched on Customer + Material."""
    invoice_df = invoice_df.copy()

    def key(series):
        # normalize so 1000 / "1000" / "1000.0" all match
        return (series.astype(str).str.strip()
                      .str.replace(r'\.0+$', '', regex=True))

    # composite match key on both sides (doesn't touch the original columns)
    invoice_df['_k'] = key(invoice_df['Customer']) + '|' + key(invoice_df['Material'])

    fill = costing_df.copy()
    fill['_k'] = key(fill['Customer']) + '|' + key(fill['Material'])
    fill = (fill.dropna(subset=['External Text'])
                .drop_duplicates(subset='_k')[['_k', 'External Text']])

    merged = invoice_df.merge(fill, on='_k', how='left')

    # fill ONLY where Service ID is blank
    blank = merged['Service ID'].isna() | \
            (merged['Service ID'].astype(str).str.strip() == '')
    merged.loc[blank, 'Service ID'] = merged.loc[blank, 'External Text']

    return merged.drop(columns=['_k', 'External Text'])

def collapse_invoice_lines(dirty_df):
    """Collapse invoice lines that share all of these fields except Quantity and Item Breakup."""
    group_keys = ['Customer', 'Contract Desc.', 'Invoice', 'Invoiced On',
              'Material', 'Mat. Description','Service ID']
    agg_map = {c: 'first' for c in dirty_df.columns if c not in group_keys}
    agg_map['Quantity'] = 'sum'
    agg_map['Item Breakup'] = 'sum'
    clean_df = dirty_df.groupby(group_keys, as_index=False, dropna=False).agg(agg_map)
    return clean_df

def make_recap_pdf(line_items, header, out_path):
    """Group one account's lines by material group and write a PDF."""
    line_items = line_items.copy()
    #fallback = "Account-wide"
    fallback = header["customer_name"]
    fallback_for_UoM = "EA"
    line_items["Department Name"] = line_items["Department Name"].apply(
        lambda v: fallback if (pd.isna(v) or str(v).strip() == "") else v
    )
    line_items["Service ID"] = line_items["Service ID"].apply(
        lambda v: fallback if (pd.isna(v) or str(v).strip() == "") else v
    )
    line_items["UoM"] = line_items["UoM"].apply(
        lambda v: fallback_for_UoM if (pd.isna(v) or str(v).strip() == "") else v
    )
    line_items["Material Group"] = line_items["Material Group"].apply(
        lambda v: "Other" if (pd.isna(v) or str(v).strip() == "") else v
    )

    # roll up lines that share material AND service id (within a department);
    # different service ids on the same material stay on separate lines
    line_items = (line_items
        .groupby(["Department Name", "Material Group", "Mat. Description", "Service ID"],
                 sort=False, as_index=False)
        .agg({"UoM": "first",
              "Quantity": "sum",
              "Item Breakup": "sum"}))

    # group by material group across the whole invoice, sorted A-Z (case-insensitive)
    groups = []
    for mg_name, mg_df in line_items.groupby("Material Group", sort=False):
        mg_df = mg_df.sort_values(["Mat. Description", "Service ID"],
                                  key=lambda c: c.str.lower())
        groups.append({
            "material_group": mg_name,
            "items": mg_df.to_dict(orient="records"),
            "subtotal": float_format(round(mg_df["Item Breakup"].sum(), 2)),
        })
    groups.sort(key=lambda x: str(x["material_group"]).lower())

    html_str = RECAP_TEMPLATE.render(groups=groups, **header)
    HTML(string=html_str).write_pdf(out_path)


# helper functions
def create_acct_code(data: str) -> str:
    """does easy and complicated mapping for SF acct codes"""
    # contract_desc = data['Document Desc.'] -- changed 6/2026
    contract_desc = data['Contract Desc.']
    customer_number = data['Customer']
    customer_number_first_four = customer_number[:4]
    customer_number_last_four = customer_number[-4:]
    customer_number_len = len(customer_number)
    # sceis_agy_code = None
    first_word = contract_desc[:contract_desc.find(' ')]

    # make all the acct codes same length
    if customer_number_len == 10:
        customer_number = customer_number[3:]
        customer_number_first_four = customer_number[:4]
        customer_number_len = len(customer_number)

    # PASCAL is apart of CHE with same account number
    if customer_number_first_four == 'H030' and contract_desc == "PASCAL IT BILLING":
        return 'H030B'

    # because BOFI is same and different
    if customer_number_first_four == 'R230':
        if customer_number == 'R230001':
            # consumer finance division
            return 'R230B'
        else:
            # bank examining division
            return 'R230'

    # divisions of Admin
    if customer_number_first_four == 'D500':
        # Division of Facilities Mgmt & Prop Srv
        if customer_number_last_four in ['0009',
                                         '0012',
                                         '0039']:
            return 'D500FMPS'
        # Program Mgmt Office
        if customer_number_last_four in ['0017']:
            return 'D500PMO'
        # Division of State Agy Support Srvs
        # State Fleet & Surplus Prop
        if customer_number_last_four in ['0013',
                                         '0012']:
            return 'D500SASS'
        # Division of State HR
        # TODO -- might be wrong?
        if customer_number_last_four in ['0008']:
            return 'D500DSHR'
        # Exec Budget Office
        if customer_number_last_four in ['0007']:
            return 'D500EBO'
        # Govt Affairs and Economic Opportunity
        if customer_number_last_four in ['0035',
                                         '0036']:
            return 'D500GAEO'
        # Office of Exec Policy & Programs
        if customer_number_last_four in ['0025',
                                         '0033',
                                         '0034']:
            return 'D500OEPP'
        # SC Enterprise Info System
        if customer_number_last_four in ['0014']:
            return 'D500SCEIS'
        # Office of Technology and Info Srvs
        if customer_number_last_four in ['0017']:
            return 'D500OTIS'
        # Office of Administrative Services
        if customer_number_last_four in ['0003']:
            return 'D500OAS'
        # Division of Info Sec?
        # Enterprise Privacy?

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
    # include other numerical accounts by name
    if contract_desc in ['RIVERBANKS ZOO',
                         'SC INTERACTIVE',
                         'SC EDUCATION LOTTERY',
                         'SC BAR ASSOCIATION',
                         'SC BAR ASSOCIATION - NON-BILLABLE',
                         'ESTILL, TOWN OF']:
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


def material_translate_create(sd=SD_MAP_DF) -> dict:
    """summarizes what it is in less than 3 words"""
    material_trans_dict = {}
    unmatched = sd[sd['MaterialTranslate'].isna()].count()['Material']
    # unmatched entries check
    print(f'There are {unmatched} entries. Baseline is 36')
    #clear nans
    sd_map_trans = SD_MAP_DF.copy()
    sd_map_trans.dropna(subset=['MaterialTranslate'], inplace=True)
    # so inefficient...
    print('Building material dictionary')
    for ix, rw in sd_map_trans.iterrows():
        material_trans_dict[rw['Material']] = rw['MaterialTranslate']
    return material_trans_dict


def material_trans_df(dfx) -> str:
    """supplement apply function to translate materials"""
    material = dfx['Mat. Description']
    try:
        return MAT_TRANS_DICT.get(material)
    except Exception:
        return ''
    
def material_group_create(sd=SD_MAP_DF) -> dict:
    """creates material group"""
    material_cat_dict = {}
    #clear nans
    sd_map_cat = SD_MAP_DF.copy()
    sd_map_cat.dropna(subset=['Material - Key'], inplace=True)
    # so inefficient...
    print('Building material group dictionary')
    for ix, rw in sd_map_cat.iterrows():
        material_cat_dict[norm_material(rw['Material - Key'])] = rw['Material group']
    return material_cat_dict

def norm_material(value):
    """1000 / 1000.0 / '1000' all -> '1000'; non-numeric codes pass through trimmed"""
    num = pd.to_numeric(value, errors='coerce')
    return str(int(round(num))) if pd.notna(num) else str(value).strip()

# Create/clear destination folder
fs.clear_destination_folder()
# Get dependent files
xlsx_file = FS_FILE_DICT.get('ECCInv')
costing_file = FS_FILE_DICT.get('Costing')
xdf = pd.read_excel(xlsx_file, dtype={'Material': str})
costing_df = pd.read_excel(costing_file, dtype={'Material': str})
SF_ACCT_INFO = pd.read_csv(FS_FILE_DICT.get('SFAcct'))
MAT_TRANS_DICT = material_translate_create()
MAT_GROUP_DICT = material_group_create()

# build dictionary because i don't know how to do this right
SF_ACCT_INFO_DICT = {}
for index, row in SF_ACCT_INFO.iterrows():
    SF_ACCT_INFO_DICT[row['SCEIS_CODE__C']] = row['ID']

# set up ContentVersion
content_version = pd.DataFrame(columns=['Title',
                                       'Description',
                                       'VersionData',
                                       'PathOnClient',
                                       'FirstPublishLocationId'])

agy_results_dict = {}
#### Note: removed loop since now targeting 1 file instead of many ###
# xdf = pd.read_excel(xlsx_file)
# get invoice date for file to fill in for nonbillable
invoice_date_file = xdf['Invoiced On'].iloc[0]

''' data wrangling '''
# convert customer number to str
xdf['Customer'] = xdf['Customer'].apply(lambda x: str(x))
# labeling OTCs
xdf.loc[(xdf['Contract Desc.'].isnull()),
        'Contract Desc.'] = 'One Time Charge'
# because there are / in this field
xdf['Contract Desc.'] = xdf['Contract Desc.']\
                        .apply(lambda x: x.replace('/', '-'))
# add category
xdf['Material Group'] = xdf['Material']\
                        .apply(lambda x: MAT_GROUP_DICT.get(norm_material(x)))

#sum values to remove duplicate material per customer
xdf = collapse_invoice_lines(xdf)
# fill in missing Service IDs with External Text from costing file
xdf = service_id_update(costing_df, xdf)

agy = xdf.copy()

# fill in a date for nonbillable, picks up date from first instance
# agy.loc[(agy['Invoice Date'].isnull()),
#        'Invoice Date'] = agy.iloc[0,4]
# Invoice Date became Invoiced on 6/2026
agy.loc[(agy['Invoiced On'].isnull()),
        'Invoiced On'] = invoice_date_file
# create agycode if state agy number
agy['AgyCode'] = agy.apply(create_acct_code, axis=1)
agy.drop(agy[agy['AgyCode'] == 'zzz'].index, inplace=True)
# translate material
agy['MaterialTranslate'] = agy.apply(material_trans_df, axis=1)
# create list of agy/cust codes
agycodes = agy['AgyCode'].drop_duplicates().tolist()

for key, value in B_AGYS.items():
    # mark B agencies
    agy['AgyCode'].loc[agy['Contract Desc.'].str.contains(value)] = key
    # to prevent sending empty dataframes for B agencies
    if not agy[agy['AgyCode'] == key].empty:
        agycodes.append(key)

# loop through agycodes
loop_count = 0
for agyc in agycodes:
    # create subset of original data
    subdf = agy[agy['AgyCode'] == agyc].copy()
    # get all contract numbers in agy
    invoice_no_list = subdf['Invoice'].drop_duplicates().tolist()
    # determine total number of invoice dates in agy
    invoice_dates_list = subdf['Invoiced On'].drop_duplicates().tolist()

    # make shared services list/dict
    # subset frame to remove null/none values; then designate col tolist()
    serv_list = subdf[subdf['MaterialTranslate'].notnull()]['MaterialTranslate']\
                .drop_duplicates()\
                .tolist()
    # added sorted() to make a-z
    serv_string = '\n'.join(sorted(serv_list))
    agy_results_dict[agyc] = serv_string

    # loop through invoice dates
    # because they didn't include invoice number....?
    # TODO - get this to show an error for no invoice no
    if isinstance(invoice_dates_list, float):
        print('No Invoice Date')
    for inv in invoice_dates_list:
        sub2df = subdf[subdf['Invoiced On'] == inv].copy()
        if sub2df.empty:
            continue

        for invoice in invoice_no_list:
            sub3df = sub2df[sub2df['Invoice'] == invoice].copy()
            # drop $0 service lines (imperfect data)
            sub3df = sub3df[sub3df['Item Breakup'].fillna(0).round(2) != 0].copy()
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
            #sales_doc_no = str(int(sales))
            invoice_doc_no = str(int(invoice))

            # pick first not null customer name
            # sales_contract_desc = sub2df.iloc[0,1]

            # there's so much missing data now multiple columns  6/2026
            # reinstating line 300, have to replace /'s b/c line breaks
            customername = sub2df['Customer Name'].iloc[0]
            customername = customername.replace("/", "")
            
            # file identifiers
            invoiceamt = float_format(round(sub3df['Item Breakup'].sum(), 2))
            tdate = '20'+pdate[-2:]\
                    + '-' + pdate[:2]\
                    + '-' + pdate[3:5]

            filename = tdate + ' - '\
                + invoiceamt + ' - '\
                + customername\
                + ' - Invoice No ' + invoice_doc_no\
                + ' - Shared Services.xlsx'
            titledate = filename[:-5]
            pdf_name = filename.replace(".xlsx", ".pdf")
            printfilename = agycode\
                + ' Invoiced On '\
                + pdate + ' '\
                + customername

            # gets Salesforce ID for account
            idofaccount = SF_ACCT_INFO_DICT[agycode]

            # generating ContentVersion manifest
            content_version.loc[loop_count] = [titledate, desc,
                                    OUTPUTPATH + pdf_name,
                                    OUTPUTPATH + pdf_name,
                                    idofaccount]
            # drop identifier columns
            sub3df.drop(['AgyCode', 'MaterialTranslate'], axis=1,
                        inplace=True)
            # export file to excel file and save
            '''
            with pd.ExcelWriter(OUTPUTPATH+filename) as writer: # pylint: disable=abstract-class-instantiated
                sub3df.to_excel(writer, index=False)
            print('Creating ' + filename)
            '''
            head = sub3df.iloc[0]
            header = {
                "customer_name": customername,
                "customer": head["Customer"],
                "contract_desc": head["Contract Desc."],
                #"sales_doc": sales_doc_no,
                "invoice_no": head["Invoice"],
                "invoiced_on": pdate,
                "generated_on": gendate,
                "total": invoiceamt,
            }
            make_recap_pdf(sub3df, header, OUTPUTPATH + pdf_name)
            print("Creating " + pdf_name)

            loop_count += 1

print('Creating manifest for ContentVersion')
content_version.to_csv(OUTPUTPATH
                       + 'ContentVersion Generated On '
                       + TODAY_DATESTAMP
                       + '.csv', index=False)

# adding null values for accounts w/o billing
for agy in SF_ACCT_INFO_DICT.keys():
    if agy not in agy_results_dict.keys():
        agy_results_dict[agy] = ' '

print('Creating shared services list')
shared_services_df = pd.DataFrame.from_dict(agy_results_dict, orient='index',
                                            columns=['Service'])
shared_services_df.reset_index(level=0, inplace=True)
#add agycode column
shared_services_df.columns = ['AgyCode', 'Service']
shared_services_df.replace('', np.nan, inplace=True)
shared_services_df.dropna(subset=['Service'], inplace=True)
#add Salesforce IDs
for agy, sfid in SF_ACCT_INFO_DICT.items():
    shared_services_df.loc[shared_services_df['AgyCode'] == agy,
                           'SalesforceAcctID'] = sfid
shared_services_df.to_csv(OUTPUTPATH+'exportSharedServices.csv', index=False)

# places mapping file for SF in output directory
fs.copy_file('pdfimportmap.sdl')
fs.copy_file('dtoservices.sdl')

print('Operation Complete!')
