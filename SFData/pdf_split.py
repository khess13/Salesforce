"""
Splits pdfs into individual files for upload
Creates ContentVersion for SF Dataloader
"""
import os
import re
import getpass
import datetime as dt
import pandas as pd
from tabula import read_pdf
from PyPDF2 import PdfReader, PdfWriter
from FileService import FileService

#2024-12-02 PdfFileReader deprecated -> PdfReader
#2024-12-02 PdfFileWriter deprecated -> PdfWriter
#2024-12-02 .numPage dep -> len(.pages)
#2024-12-02 .getPage(pageNumber) -> reader.pages[page_number]

ROOT = os.getcwd()
DATESTAMP = str(dt.datetime.now().strftime('%m-%d-%Y'))
CURR_ID = getpass.getuser()
# formerly to user desktop, avoid onedrive nagging
OUTPUTPATH = 'C:\\Users\\'+CURR_ID+'\\PDFDrop\\'

# helper functions
def agycode_cleaner(agy_code) -> str:
    """ because some agycodes are numbers in report"""
    try:
        agy_code = float(agy_code)
        # remove .0; 0 values after decimal f = float
        newCode = '{:0.0f}'.format(agy_code)
        return newCode
    except Exception:
        return str(agy_code)


# Load dependent files
fs = FileService(ROOT,OUTPUTPATH)
FS_FILE_DICT = fs.get_dependent_file_dict()
SF_ACCT_INFO = pd.read_csv(FS_FILE_DICT.get('SFAcct'))

# build dictionary because i don't know how to do this right
SF_ACCT_INFO_DICT = {}
for index, row in SF_ACCT_INFO.iterrows():
    SF_ACCT_INFO_DICT[row['SCEIS_CODE__C']] = row['ID']


# Create/clear destination folder
fs.clear_destination_folder()

# set up ContentVersion
contentVersion = pd.DataFrame(columns=['Title',
                                       'Description',
                                       'VersionData',
                                       'PathOnClient',
                                       'FirstPublishLocationId'])

# split PDF to destination
input_pdf = PdfReader(open(FS_FILE_DICT.get('BOInv'), 'rb'))
for i in range(len(input_pdf.pages)):
    # moving here to clear writer
    output = PdfWriter()
    #output.addPage(input_pdf.getPage(i))
    output.add_page(input_pdf.pages[i])
    with open(f'{OUTPUTPATH}document-page{i}.pdf', 'wb') as outputStream:
        output.write(outputStream)

# gather split files for read
pdfs_to_parse = fs.get_files_from_dir(altpath=OUTPUTPATH)
for loop_count, p in enumerate(pdfs_to_parse):
    # TODO - something is wrong
    pdfpage = read_pdf(p, pages='all')
    df = pdfpage[0]
    df.dropna(subset=['Total'], how='all', inplace=True)

    # clean up agycode, SCI code was float
    agycode = agycode_cleaner(df.iloc[0, 0])
    # changes date slash to dash
    pdate = df.iloc[0, 3].replace('/', '-')
    # had to remove random characters like I
    pdate = re.sub(r'[A-z]*', '', pdate)
    # because assumed datatype was float
    invoiceno = str(df.iloc[0, 4])[:-2]
    invoiceamt = str(df.iloc[len(df)-1, 10])
    # rebuild date for sort
    tdate = '20'\
            + pdate[-2:] + '-'\
            + pdate[:2] + '-'\
            + pdate[3:5]
    gendate = DATESTAMP
    filename = p

    # outputpath = pdfdrop
    customername = str(df.iloc[0, 2])
    titledate = tdate + ' - ' +\
        invoiceamt + ' - '\
        + customername\
        + ' - Invoice '\
        + invoiceno +\
        ' - Shared Services'
    printfilename = agycode\
        + ' Invoice Date '\
        + pdate
    desc = 'S&D Billing for services on '\
        + pdate\
        + '. Generated on '\
        + gendate

    # gets Salesforce ID for account
    idofaccount = SF_ACCT_INFO_DICT[agycode]

    # generating ContentVersion manifest
    contentVersion.loc[loop_count] = [titledate,
                                      desc,
                                      filename,
                                      filename,
                                      idofaccount]
    print('Logging '
          + printfilename
          + ' '
          + invoiceno
          + ' - '
          + filename)

print('Creating manifest for ContentVersion')
contentVersion.to_csv(OUTPUTPATH
                      + 'ContentVersion Generated On '
                      + DATESTAMP
                      + '.csv',
                      index=False)
fs.copy_file('pdfimportmap.sdl')

print('Operation Complete!')
