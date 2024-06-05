"""Incomplete - retrieves SF data"""
import pandas as pd
import requests


class SFDataRetrieve():
    """Accesses SF objects and return csv file"""
    def __init__(self, api_url, object_list):
        self.api_url = api_url
        self.object_list = object_list

    def get_objects(self) -> dict:
        """Request object data from api"""
        # TODO - write timeout/throw error
        # TODO - Oauth, https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest_compatible_editions.htm
        response = requests.get(self.api_url)
        return response

    def parse_json(self) -> None:
        """Parses json response"""
        # TODO - make loop for each file needed for SF data load
        with open('jsonfile.json', encoding='utf-8') as input_file:
            df = pd.read_json(input_file)
        df.to_csv('filename.csv', encoding='utf-8', index=False)
