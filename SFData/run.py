"""
Run all scripts at once. Headcount is on off day from others.
"""
import subprocess

# TODO - would make sense to check files once here? would this make all
# scripts need to be classes?

RUN_HEADCOUNT = input('Run Headcount? y/n')

if RUN_HEADCOUNT != 'y':
    subprocess.run(['python','xlsx_split.py'], check=False)
    subprocess.run(['python','pdf_split.py'], check=False)
    subprocess.run(['python','services.py'], check=False)
    subprocess.run(['python','emailer.py'], check=False)
else:
    subprocess.run(['python','headcount.py'], check=False)