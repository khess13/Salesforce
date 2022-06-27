import pandas as pd
import os
import re
import shutil
import datetime as dt
from tabula import read_pdf
from PyPDF2 import PdfFileWriter, PdfFileReader
import getpass
from pathlib import Path


def get_files_from_dir(filepath, ext='.pdf', switch='root') -> list:
    # gathers files in root directory and returns only pdf files
    filesindir = os.listdir(filepath)
    # tilda indicates open temp file, excluding these
    if switch == 'root':
        xlsxfiles = [root + f for f in filesindir if ext in f and '~' not in f]
    else:
        xlsxfiles = [f for f in filesindir if ext in f and '~' not in f]
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


def agycode_cleaner(agycode) -> str:
    # because some agycodes are numbers
    # if type(agycode) == float:
    try:
        agycode = float(agycode)
        # remove .0; 0 values after decimal f = float
        newCode = '{:0.0f}'.format(agycode)
        return newCode
    except:
        return str(agycode)


def copyFileMap(src, dest):
    # copy file mapping from SF folder to Desktop folder
    shutil.copyfile(src, dest)


# root = os.getcwd()
root = str(Path(os.getcwd()).parents[0]) + "\\"
#  dependent file
try:
    account_loc = root + '\\extract.csv'
except:
    print("extract.csv is missing from parent directory")

datestamp = str(dt.datetime.now().strftime('%m-%d-%Y'))
# see file_cutterv2 for comments
# pdfdrop = root + '\\PDFdrop\\'
currID = getpass.getuser()
outputpath = 'C:\\Users\\'+currID+'\\Desktop\\PDFDrop\\'
clear_destination_folder(outputpath)

# set up format of manifest for ContentVersion
contentVersion = pd.DataFrame(columns=['Title',
                                       'Description',
                                       'VersionData',
                                       'PathOnClient',
                                       'FirstPublishLocationId'])
# get account IDs by SCEIS code from Salesforce csv
accountids = pd.read_csv(account_loc)
# build dictionary because i don't know how to do this right
acctid_dict = {}
for index, row in accountids.iterrows():
    acctid_dict[row['SCEIS_CODE__C']] = row['ID']

print('Splitting PDF.')
# https://stackoverflow.com/questions/490195/split-a-multi-page-pdf-file-into-multiple-pdf-files-with-python
mainpdf = get_files_from_dir(root)
inputpdf = PdfFileReader(open(mainpdf[0], 'rb'))
# output = PdfFileWriter()
for i in range(inputpdf.numPages):
    # moving here to clear output
    output = PdfFileWriter()
    output.addPage(inputpdf.getPage(i))
    with open(outputpath + "\\document-page%s.pdf" % i, "wb") as outputStream:
        output.write(outputStream)

print('Gathering pdfs to parse.')
# get files to process
# Updated function to resuse without appending root
pdf_location = get_files_from_dir(outputpath, switch='other')
for p in pdf_location:
    # TODO -- cut the pdfs by page somehow?
    # read pdf and put in dataframe
    pdfpage = read_pdf(outputpath + p, pages='all')
    df = pdfpage[0]
    # remove nan rows
    df.dropna(subset=['Total'], how='all', inplace=True)

    # make files idenifiers
    # added float agycode for SCI
    agycode = agycode_cleaner(df.iloc[0, 0])
    pdate = df.iloc[0, 3].replace('/', '-')  # .strftime('%m-%d-%Y')
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
    gendate = datestamp
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
    idofaccount = acctid_dict[agycode]

    # generating ContentVersion manifest
    nextentry = pd.Series([titledate,
                          desc,
                          outputpath + filename,
                          outputpath + filename,
                          idofaccount],
                          index=contentVersion.columns)
    contentVersion = contentVersion.append(nextentry, ignore_index=True)

    print('Logging '
          + printfilename + ' '
          + invoiceno + ' - doc id - '
          + filename)

print('Creating manifest for ContentVersion')
contentVersion.to_csv(outputpath
                      + 'ContentVersion Generated On '
                      + datestamp
                      + '.csv',
                      index=False)
copyFileMap(root+'\\pdfimportmap.sdl', outputpath+'\\pdfimportmap.sdl')

print('Operation Complete!')
