import os
import json
import requests
import pandas as pd
import dataset
from typing import Dict
from utilities import create_directory
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError, KustoMultiApiError


class KQLDatabase:

    def __init__(self, kusto_uri: str, database_name: str, client_id: str, client_secret: str, tenant_id: str):
        """
        Initialize variables.
        """
        self.kusto_uri = kusto_uri
        self.database_name = database_name

        # Create a connection string for authentication
        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            "https://trd-q70msbdsfhsq3ntat4.z2.kusto.fabric.microsoft.com/", client_id, client_secret, tenant_id
        )

        # Create a Kusto client
        self.client = KustoClient(kcsb)
        self.data_dir = './data/monitoring'

        create_directory(self.data_dir)


    def query_kql_database(self, kql_query: str):
        """
        Connects to a Kusto (KQL) database and executes a query.

        Args:
            kql_query (str): The KQL query to execute.

        Returns:
            pandas.DataFrame: A DataFrame containing the query results, or None if an error occurs.
        """
        try:
            # Execute the query
            response = self.client.execute(self.database_name, kql_query)

            # Convert the response to a pandas DataFrame
            columns = kql_query.rsplit('| project', maxsplit=1)[1].strip().split(', ')
            df = pd.DataFrame(response.primary_results[0], columns=columns, dtype=str)

            return df

        except KustoServiceError as error:
            if 'E_QUERY_RESULT_SET_TOO_LARGE' in str(error):
                print('ERROR: Query set too large, try adding some more filters!')
            else:
                print(f"An error occurred: {error}")
            return None
        except KustoMultiApiError as error:
            print(f"An error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None