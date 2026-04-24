"""
Supports recurring file operations.
"""
import os
import shutil
from typing import Dict, List, Optional

import arrow


class FileService:
    """Manages source and destination directories for data pipeline files."""

    def __init__(self, file_source_dir: str, destination_dir: str) -> None:
        self.file_source_dir = file_source_dir
        self.data_directory = os.path.join(file_source_dir, 'Data')
        self.destination_dir = destination_dir

    # ---------------------------------------------------------------------------
    # Directory operations
    # ---------------------------------------------------------------------------

    def get_files_from_dir(
        self,
        ext: Optional[str] = None,
        altpath: Optional[str] = None,
    ) -> List[str]:
        """
        Return full paths of files in the data directory (or altpath).
        Skips temp files indicated by a tilde in the filename.
        Optionally filters by file extension substring.
        """
        target_dir = altpath if altpath is not None else self.data_directory
        files_in_dir = os.listdir(target_dir)

        target_files = [
            os.path.join(target_dir, f) for f in files_in_dir
            if '~' not in f and (ext is None or ext in f)
        ]

        if not target_files:
            raise ValueError(
                f'No files found in {target_dir}. Check extension filter: {ext}'
            )

        return target_files

    def clear_destination_folder(self) -> None:
        """Delete and recreate the destination folder."""
        print('Clearing old data.')
        if os.path.exists(self.destination_dir):
            shutil.rmtree(self.destination_dir)
        os.makedirs(self.destination_dir, exist_ok=True)

    def copy_file(self, file_name: str) -> None:
        """Copy a file from the data directory to the destination directory."""
        src = os.path.join(self.data_directory, file_name)
        dst = os.path.join(self.destination_dir, file_name)
        shutil.copyfile(src, dst)

    # ---------------------------------------------------------------------------
    # Dependent file resolution
    # ---------------------------------------------------------------------------

    def get_dependent_file_dict(self) -> Dict[str, str]:
        """Locate and label all required input files. Raises if any are missing or stale."""
        return self._check_dependent_files()

    def _check_dependent_files(self) -> Dict[str, str]:
        """
        Verify the expected 11 files are present and not stale.
        Returns a dict mapping logical file keys to their full paths.

        Expected files:
            SFAcct    — SFexport extract.csv (Account Object)
            Contracts — SFexport contract.csv (Contract Object)
            ECCInv    — ECCexport EXPORT.xlsx (ECC invoice data)
            HR        — BOexport Headcount.xlsx
            BOInv     — BOexport S_D Salesforce Scheduled.pdf (BO invoices)
            SDMap     — BOexport SDMap.xlsx (material mapping)
            + 5 SDL dataloader map files (not date-checked)
        """
        files_from_data = self.get_files_from_dir()

        if len(files_from_data) != 11:
            raise ValueError(
                f'Expected 11 files in Data folder, found {len(files_from_data)}.'
            )

        labeled: Dict[str, str] = {}
        for file in files_from_data:
            if not self._file_date_checker(file):
                raise ValueError(f'Stale file: {file}')

            if 'extract' in file:
                labeled['SFAcct'] = file
            elif 'EXPORT' in file:
                labeled['ECCInv'] = file
            elif 'Headcount' in file:
                labeled['HR'] = file
            elif 'contract.csv' in file:
                labeled['Contracts'] = file  # note: similar names — be careful
            elif 'S_D Salesforce' in file:
                labeled['BOInv'] = file
            elif 'SDMap' in file:
                labeled['SDMap'] = file

        return labeled

    def _file_date_checker(self, filepath: str) -> bool:
        """
        Return False if a file is considered stale.
        SDL files are excluded from the check.
        extract and SDMap files have a 200-day window (TODO: restore to 90).
        All other files have a 90-day window (TODO: restore to 7).
        """
        _, ext = os.path.splitext(filepath)
        if ext == '.sdl':
            return True

        if 'extract' in filepath or 'SDMap' in filepath:
            cutoff = arrow.now().shift(days=-200)  # TODO: restore to -90
        else:
            cutoff = arrow.now().shift(days=-90)   # TODO: restore to -7

        return arrow.get(os.stat(filepath).st_mtime) > cutoff
