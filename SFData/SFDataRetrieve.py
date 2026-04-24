"""
Salesforce data retrieval via REST API.
Incomplete — OAuth and response parsing still need implementation.
"""
from __future__ import annotations

from typing import List

import pandas as pd
import requests


class SFDataRetrieve:
    """Fetch Salesforce object data and write to CSV."""

    def __init__(self, api_url: str, object_list: List[str]) -> None:
        self.api_url = api_url
        self.object_list = object_list

    def get_objects(self) -> requests.Response:
        """
        Request object data from the Salesforce REST API.
        TODO: add request timeout
        TODO: implement OAuth — see Salesforce REST API docs:
              https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest_compatible_editions.htm
        """
        return requests.get(self.api_url, timeout=30)

    def parse_json(self, input_path: str, output_path: str) -> None:
        """
        Parse a Salesforce JSON response file and write to CSV.
        TODO: extend to loop over each object in self.object_list.
        """
        with open(input_path, encoding='utf-8') as input_file:
            df = pd.read_json(input_file)
        df.to_csv(output_path, encoding='utf-8', index=False)
