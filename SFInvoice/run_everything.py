import os
import arrow
from pathlib import Path

root = str(Path(os.getcwd()).parents[0]) + "\\"


def checkTargetFileDates(susFile):
    if 'extract' in susFile:
        noOfDays = arrow.now().shift(days=-90)
    else:
        noOfDays = arrow.now().shift(days=-7)
    if arrow.get(os.stat(susFile).st_mtime) > noOfDays:
        return True
    else:
        return False


def get_files_from_dir(filepath, ext=['.XLSX', '.pdf', 'extract.csv']):
    filesindir = os.listdir(filepath)
    # tilda indicates open temp file, excluding these
    # root + file name if file has extension and no tilda
    targetFiles = [filepath + f for f in filesindir if
                   [f for e in ext if e in f] and '~' not in f]
    if len(targetFiles) < 3:
        print('Files missing for processing, check the folder')
        return False
    elif len(targetFiles) > 3:
        print('Too many files')
        return False
    else:
        ans = [checkTargetFileDates(f) for f in targetFiles]
        if False in ans:
            print('Files are not fresh')
            for f, t in zip(ans, targetFiles):
                print(f'{t}:{f}')
            return False
        else:
            print('Files are current, good job')
            return True


good2go = get_files_from_dir(root)
if good2go is True:
    import file_cutter0
    import pdf_cutter
    print('So fresh and clean!')
else:
    print('Processing stopped')
