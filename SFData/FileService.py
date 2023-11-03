"""
Supports recurring file operations
"""
import os
import shutil
import arrow

class FileService:
    """Provides directory clearing for dump directories"""
    def __init__(self, file_source_dir, destination_dir):
        self.file_source_dir = file_source_dir
        self.data_directory = file_source_dir + "\\Data\\"
        self.destination_dir = destination_dir

    ## directory ops##
    def get_files_from_dir(self, ext=None, altpath=None) -> list:
        """gathers files from target directory by file type"""
        if altpath is None:
            temp_path = self.data_directory
        else:
            temp_path = altpath
        
        files_in_dir = os.listdir(temp_path)
        # tilda indicates open temp file, excluding these
        if not ext is None:
            target_files = [temp_path + f for f in files_in_dir
                            if ext in f and '~' not in f]
        else:
            target_files = [temp_path + f for f in files_in_dir
                            if '~' not in f]
            
        if len(target_files) == 0:
            raise ValueError('No files found, try checking extension')
    
        return target_files

    def clear_destination_folder(self) -> None:
        """clears destination folder"""
        print('Clearing old data.')
        try:
            shutil.rmtree(self.destination_dir)
            os.mkdir(self.destination_dir)
        except Exception:
            os.mkdir(self.destination_dir)
    
    def copy_file(self, file_name) -> None:
        """Copy files from data folder to destination"""
        shutil.copyfile(self.data_directory + file_name, 
                        self.destination_dir + file_name)

    ## dependent files ##
    def get_dependent_file_dict(self) -> dict:
        """Gets dependent files from checkers"""
        dep_files = self.__check_dependent_files()
        return dep_files
            
    def __check_dependent_files(self) -> dict:
        """Are all files accounted for and returns file location"""
        # SFexport - contract.csv
        # SFexport - extract.csv
        # BOexport - S&D Salesforce - DTO Services.xlsx <-- removing?
        # BOexport - headcount.xlsx --- run at different time, rm?
        # BOexport - S&D Salesforce - Scheduled.pdf
        # BOexport - SDMap.xlsx
        # ECCexport - EXPORT.xlsx
        # SF map for dataloader - agencyservices.sdl
        # SF map for dataloader - hc.sdl
        # SF map for dataloader - contract_services.sdl
        # SF map for dataloader - pdfimportmap.sdl
        # SF map for dataloader - dtoservices.sdl
        files_from_data = self.get_files_from_dir()
        files_labeled_from_data = {}
        if len(files_from_data) == 11:
            for file in files_from_data:
                if self.__file_date_checker(file) is False:
                    raise Exception(f'{file} is stale')
                if 'extract' in file:
                    files_labeled_from_data['SFAcct'] = file
                elif 'EXPORT' in file:
                    files_labeled_from_data['ECCInv'] = file
                elif 'Headcount' in file:
                    files_labeled_from_data['HR'] = file
                # be careful of other files with similiar names
                elif 'contract.csv' in file:
                    files_labeled_from_data['Contracts'] = file
                elif 'Scheduled' in file:
                    files_labeled_from_data['BOInv'] = file
                elif 'SDMap' in file:
                    files_labeled_from_data['SDMap'] = file
                '''
                elif 'AgencyServices' in file:
                    files_labeled_from_data['AgencyServices'] = file
                elif 'agencyservices.sdl' == file:
                    files_labeled_from_data['agyservSDL'] = file
                elif 'hc.sdl' == file:
                    files_labeled_from_data['hcSDL'] = file
                elif 'contract_services.sdl' == file:
                    files_labeled_from_data['contractSDL'] = file
                elif 'pdfimportmap.sdl' == file:
                    files_labeled_from_data['pdfimportSDL'] = file
                elif 'dtoservices.sdl' == file:
                    files_labeled_from_data['dtoSDL'] = file
                '''
        else:
            raise ValueError(
                f'Check Data folder. Count is {str(len(files_from_data))}')
        return files_labeled_from_data
    
    def __file_date_checker(self, sus_file) -> bool:
        """Check staleness of file"""
        if sus_file[-3:] == 'sdl':
            # skip checking these files
            return True
        elif 'extract' in sus_file or 'SDMap' in sus_file:
            no_of_days = arrow.now().shift(days=-200) #s/b 90
        else:
            no_of_days = arrow.now().shift(days=-90) #s/b 7
        if arrow.get(os.stat(sus_file).st_mtime) > no_of_days:
            return True
        return False
