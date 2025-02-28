"""Updates table docs, updates new data"""
import argparse
from simple_salesforce import Salesforce
import pandas as pd
from auth import *


# https://atrisaxena.github.io/tutorial/saleforce-python-object/
sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            instance_url=instance_url
)

# sets up params at CLI
parser = argparse.ArgumentParser(description ='RUN SOQL Query for Salesforce')
parser.add_argument('--object',type=str, help='Salesforce Object Name')
parser.add_argument('--columns',type=str, help = 'Salesforce Object Columns')
parser.add_argument('--where_field', type=str, help='Where Column')
parser.add_argument('--csv_file',type=str,help='csv file')
parser.add_argument('--csv_field_map',type=str,help='CSV Mapped Field')
args = parser.parse_args()

# python Get_ID.py --object Object1 --columns "Id, col1, col2, col3" 
# --where_field Name --csv_file myfile.csv --csv_field_map NameofPerson

def query_sf(table_name:str) -> dict[str, any]:
    ''' query all data for a table '''
    soql_query = "SELECT * FROM "\
                 + table_name
    query_result = sf.query_all(soql_query)
    return query_result

def update() -> None:
    ''' update account fields '''
    pass

def insert() -> None:
    ''' insert files into contentversion '''
    pass

# TODO --- make a csv file to feed back?
def export(response:dict) -> None:
    ''' exports csv files to Data '''
    if response['done'] is True:
        initalize_df = 0
        if len(response['records']) > 0 and initalize_df == 0:
            df = pd.DataFrame(response['records'])
            initalize_df += 1
        else:
            df = df.append(pd.DataFrame(response['records']))
        df = df.drop('attributes', axis=1)
        df.to_csv('')
    else:
        print('No data retrieved')
