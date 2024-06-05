"""Sends copy of ECC data to Scott"""
import outlook
from FileService import FileService

ROOT = os.getcwd()
OUTPUTPATH = ROOT

fs = FileService(ROOT,OUTPUTPATH)
attachment_location = FS_FILE_DICT.get('ECCInv')
