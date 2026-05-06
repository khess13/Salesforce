"""
Entry point — runs all pipeline scripts in sequence.
Headcount runs on a separate day from the others.
"""
import subprocess

def run_data_refresh_pipline( ) -> None:
    """Run the data refresh pipeline."""
    print('Refreshing data from Salesforce')
    subprocess.run(['python', 'SFDataRetrieve.py'], check=False)

def run_standard_pipeline() -> None:
    """Run the standard daily billing pipeline."""
    scripts = ['xlsx_split.py', 'pdf_split.py', 'services.py', 'emailer.py']
    for script in scripts:
        print(f'Running {script}...')
        subprocess.run(['python', script], check=False)


def run_headcount_pipeline() -> None:
    """Run the headcount update pipeline."""
    print('Running headcount.py...')
    subprocess.run(['python', 'headcount.py'], check=False)


def main() -> None:
    answer = input('Run Headcount? y/n: ').strip().lower()
    if answer == 'y':
        run_headcount_pipeline()
    else:
        run_data_refresh_pipline()
        run_standard_pipeline()


if __name__ == '__main__':
    main()
