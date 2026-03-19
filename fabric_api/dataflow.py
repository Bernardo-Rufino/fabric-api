import os
import re
import copy
import json
import base64
import requests
import pandas as pd
from typing import Dict
from .utilities import create_directory
from .workspace import Workspace


class Dataflow:

    def __init__(self, token: str):
        """
        Initialize variables.
        """
        self.main_url = 'https://api.powerbi.com/v1.0/myorg'
        self.fabric_api_base_url = 'https://api.fabric.microsoft.com'
        self.token = token
        self.headers = {'Authorization': f'Bearer {self.token}'}
        self.workspace = Workspace(self.token)

        # Directories
        self.dataflows_dir = './data/dataflows'
        self.directories = [self.dataflows_dir]

        for dir in self.directories:
            create_directory(dir)


    def _get_dataflow_pbi_definition(self, workspace_id: str, dataflow_id: str) -> Dict:
        """
        Fetches a dataflow definition from the Power BI REST API.
        Works for Gen1 and Gen2 (standard) dataflows.

        Args:
            workspace_id (str): The workspace ID.
            dataflow_id (str): The dataflow ID.

        Returns:
            Dict: A dictionary with 'message' ('Success' or error) and 'content' (full API response).
        """
        if workspace_id == '':
            return {'message': 'Missing workspace id, please check.', 'content': ''}

        if dataflow_id == '':
            return {'message': 'Missing dataflow id, please check.', 'content': ''}

        request_url = f'{self.main_url}/groups/{workspace_id}/dataflows/{dataflow_id}'
        r = requests.get(url=request_url, headers=self.headers)

        if r.status_code == 200:
            return {'message': 'Success', 'content': json.loads(r.content)}
        else:
            try:
                response = json.loads(r.content)
                error_message = response['error']['message']
            except Exception:
                error_message = r.text
            return {'message': {'error': error_message, 'status_code': r.status_code}}


    def list_dataflows(self, workspace_id: str = '', type: str = 'pbi') -> Dict:
        """
        List all dataflows in a workspace_id that the user has access to.

        Args:
            workspace_id (str, optional): workspace id to search for.

        Returns:
            Dict: status message and content.
        """
        # If workspace ID was not informed, return error message...
        if workspace_id == '':
            return {'message': 'Missing workspace id, please check.', 'content': ''}
        
        if type not in ('pbi', 'fabric'):
            return {'message': 'Type must be "pbi" or "fabric".', 'content': ''}
        
        # Main URL
        elif type == 'pbi':
            request_url = f'{self.main_url}/groups/{workspace_id}/dataflows'
        elif type == 'fabric':
            request_url = f'{self.fabric_api_base_url}/v1/workspaces/{workspace_id}/dataflows'
        else:
            return {'message': 'Type must be "pbi" or "fabric".', 'content': ''} # Just as fallback, it won't reach here.

        workspace_name = self.workspace.get_workspace_details(workspace_id).get('content', {}).get('name', 'notFound')
        filename = f'dataflows_{workspace_name}.xlsx'

        # Make the request
        r = requests.get(url=request_url, headers=self.headers)

        # Get HTTP status and content
        status = r.status_code
        response = json.loads(r.content).get('value', '')

        # If success...
        if status == 200:
            if type == 'fabric':
                df = pd.json_normalize(response)
                df['name'] = df['displayName']
                df.drop(columns=['displayName'], inplace=True)
            else:
                df = pd.DataFrame(response)
            df.to_excel(f'{self.dataflows_dir}/{filename}', index=False)
            result = json.loads(df.to_json(orient='records'))

            return {'message': 'Success', 'content': result}

        else:                
            # If any error happens, return message.
            response = json.loads(r.content)
            error_message = response['error']['message']

            return {'message': {'error': error_message, 'content': response}}
            

    def get_dataflow_details(self, workspace_id: str = '', dataflow_id: str = '', folder_name: str = '') -> Dict:
        """
        Get all details from a specific dataflow in a workspace and save to a JSON file.

        Args:
            workspace_id (str, optional): workspace id to search for.
            dataflow_id (str, optional): dataflow id to get the details.
            folder_name (str, optional): folder name to save the JSON file. If not provided, uses the workspace name.

        Returns:
            Dict: status message and content.
        """
        result = self._get_dataflow_pbi_definition(workspace_id, dataflow_id)

        if result.get('message') != 'Success':
            return result

        response = result['content']

        if folder_name == '':
            folder_name = self.workspace.get_workspace_details(workspace_id).get('content', {}).get('name', 'notFound')

        # Save to json file
        filepath = f'{self.dataflows_dir}/{folder_name}/dataflows'
        filename = f'{filepath}/{response.get("name", "")}.json'
        os.makedirs(filepath, exist_ok=True)

        with open(filename, mode='w', encoding='utf-8-sig') as f:
            json.dump(response, f, ensure_ascii=True, indent=4)

        return result


    def create_dataflow(
                self, 
                workspace_id: str = '', 
                dataflow_content: Dict = '') -> Dict:
        """
        Creates a new Power BI dataflow in a specified workspace.

        Args:
            workspace_id (str): workspace id where dataflow will be created.
            dataflow_content (Dict): dataflow json with all details from it.

        Returns:
            Dict: status message.
        """

        # If both, user and workspace if are provided...
        if (dataflow_content != '') & (workspace_id != ''):

            request_url = self.main_url + f'/groups/{workspace_id}/imports?datasetDisplayName=model.json&nameConflit=Ignore'

            body = {
                'value': json.dumps(dataflow_content, ensure_ascii=True)
            }
            
            # Make the request
            r = requests.post(url=request_url, headers=self.headers, files=body)

            # Get HTTP status and content
            status = r.status_code

            # If success...
            if status in (200, 202):
                return {'message': 'Success'}
            
            else:                
                
                try:
                    # If any error happens, return message.
                    response = json.loads(r.content)
                    error_message = response['error']

                except:
                    return {'message': 'Error reading JSON response'}
                
                return {'message': {'error': error_message, 'content': response}}

        else:
            return {'message': 'Missing parameters, please check.'}


    def delete_dataflow(
                    self, 
                    workspace_id: str = '', 
                    dataflow_id: str = '',
                    type: str = 'pbi') -> Dict:
            """
            Deletes a Power BI dataflow from a specified workspace.

            Args:
                workspace_id (str): workspace id where dataflow will be deleted.
                dataflow_id (str): dataflow id to be deleted.

            Returns:
                Dict: status message.
            """
            # If workspace ID was not informed, return error message...
            if workspace_id == '':
                return {'message': 'Missing workspace id, please check.', 'content': ''}
            
            # If dataflow ID was not informed, return error message...
            if dataflow_id == '':
                return {'message': 'Missing dataflow id, please check.', 'content': ''}
            

            if type not in ('pbi', 'fabric'):
                return {'message': 'Type must be "pbi" or "fabric".', 'content': ''}
            
            # Main URL
            elif type == 'pbi':
                request_url = f'{self.main_url}/groups/{workspace_id}/dataflows/{dataflow_id}'
            elif type == 'fabric':
                request_url = f'{self.fabric_api_base_url}/v1/workspaces/{workspace_id}/dataflows/{dataflow_id}'
            else:
                return {'message': 'Type must be "pbi" or "fabric".', 'content': ''} # Just as fallback, it won't reach here.

            
            # Make the request
            r = requests.delete(url=request_url, headers=self.headers)

            # Get HTTP status and content
            status = r.status_code

            # If success...
            if status in (200, 202):
                return {'message': 'Success'}
            
            else:                
                
                try:
                    # If any error happens, return message.
                    print(r.text)
                    response = json.loads(r.content)
                    error_message = response['error']

                except:
                    return {'message': 'Error reading JSON response'}
                
                return {'message': {'error': error_message, 'content': response}}
            

    def export_dataflow_json(self, workspace_id: str = '', dataflow_id: str = '', dataflow_name: str = '') -> Dict:
        """
        Exports the JSON definition of a Power BI dataflow.

        Args:
            workspace_id (str, optional): workspace id where the dataflow resides.
            dataflow_id (str, optional): dataflow id to get the details.
            dataflow_name (str, optional): name to save the exported JSON file.

        Returns:
            Dict: status message and content.
        """
        result = self._get_dataflow_pbi_definition(workspace_id, dataflow_id)

        if result.get('message') != 'Success':
            return result

        response = result['content']
        response['pbi:mashup']['allowNativeQueries'] = False

        # Save to json file
        filename = f'{self.dataflows_dir}/prod backup/{dataflow_name}.json'

        with open(filename, mode='w', encoding='utf-8-sig') as f:
            json.dump(response, f, ensure_ascii=True, indent=4)

        return {'message': 'Success', 'content': response}

    def get_dataflow_gen2_definition(self, workspace_id: str, dataflow_id: str) -> Dict:
        """
        Gets the definition of a Dataflow Gen2 (CI/CD) from a specified workspace.
        Only Dataflow Gen2 (CI/CD / native Fabric) items support definition export.
        Standard Dataflow Gen2 items are not supported.

        Args:
            workspace_id (str): The ID of the workspace where the Dataflow Gen2 resides.
            dataflow_id (str): The ID of the Dataflow Gen2 to retrieve the definition for.

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the Dataflow Gen2 definition content.
        """
        api_url = f'{self.fabric_api_base_url}/v1/workspaces/{workspace_id}/dataflows/{dataflow_id}/getDefinition'

        print(f"Extracting definition for dataflow {dataflow_id} from workspace {workspace_id}...")
        response = requests.post(api_url, headers=self.headers)

        if response.status_code == 200:
            definition = response.json()
            print("Successfully extracted Dataflow Gen2 definition.")
            return {'message': 'Success', 'content': definition}
        else:
            # getDefinition only works for Dataflow Gen2 (CI/CD / native Fabric).
            # Standard Dataflow Gen2 items return an error here.
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_code = error_data.get('errorCode', '')

            if response.status_code == 400 or error_code == 'UnknownError':
                return {
                    'message': {
                        'error': 'This dataflow does not support definition export. '
                                 'Only Dataflow Gen2 (CI/CD) items created via the native Fabric experience support this operation. '
                                 'Standard Dataflow Gen2 items are not supported.',
                        'status_code': response.status_code
                    }
                }

            error_message = response.text
            print(f"Error getting Dataflow Gen2 definition: {response.status_code} - {error_message}")
            return {'message': {'error': error_message, 'status_code': response.status_code}}
        

    def create_dataflow_gen2_from_definition(self, workspace_id: str, display_name: str, definition: Dict) -> Dict:
        """
        Creates a new Dataflow Gen2 in a specified workspace from a given definition.

        Args:
            workspace_id (str): The ID of the target workspace where the Dataflow Gen2 will be created.
            display_name (str): The display name for the new Dataflow Gen2.
            definition (Dict): The complete JSON definition of the Dataflow Gen2 (obtained from get_dataflow_gen2_definition).

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the details of the newly created Dataflow Gen2.
        """
        api_url = f'{self.fabric_api_base_url}/v1/workspaces/{workspace_id}/dataflows'
        
        payload = {
            "displayName": display_name,
            "description": "",
            "definition": definition['definition']
        }
        
        print(f"Creating Dataflow Gen2 '{display_name}' in workspace {workspace_id}...")
        response = requests.post(api_url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            new_item = response.json()
            print(f"Successfully created Dataflow Gen2. New Item ID: {new_item['id']}")
            return {'message': 'Success', 'content': new_item}
        elif response.status_code == 400 and 'ItemDisplayNameAlreadyInUse' in response.text:
            error_message = response.text
            print(f"Error creating Dataflow Gen2: {response.status_code} - {error_message}")
            print('Use update method instead.')
            return {'message': {'error': error_message, 'status_code': response.status_code}}
        else:
            error_message = response.text
            print(f"Error creating Dataflow Gen2: {response.status_code} - {error_message}")
            return {'message': {'error': error_message, 'status_code': response.status_code}}
        

    def update_dataflow_gen2_from_definition(self, workspace_id: str, dataflow_id: str, display_name: str, definition: Dict) -> Dict:
        """
        Updates an existing Dataflow Gen2 in a specified workspace with a new definition.

        Args:
            workspace_id (str): The ID of the workspace where the Dataflow Gen2 resides.
            dataflow_id (str): The ID of the Dataflow Gen2 to update.
            display_name (str): The new display name for the Dataflow Gen2 (can be the same as current).
            definition (Dict): The complete JSON definition of the Dataflow Gen2 (obtained from get_dataflow_gen2_definition).

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the details of the updated Dataflow Gen2.
        """
        api_url = f'{self.fabric_api_base_url}/v1/workspaces/{workspace_id}/dataflows/{dataflow_id}/updateDefinition?updateMetadata=true'
        
        payload = {
            "definition": definition['definition']
        }
        
        print(f"Updating Dataflow Gen2 '{display_name}' (ID: {dataflow_id}) in workspace {workspace_id}...")
        response = requests.post(api_url, headers=self.headers, json=payload)

        if response.status_code in (200, 202):
            if response.content:
                updated_item = response.json()
            else:
                updated_item = {'id': dataflow_id, 'displayName': display_name}
            print(f"Successfully updated Dataflow Gen2. Item ID: {updated_item['id']}")
            return {'message': 'Success', 'content': updated_item}
        else:
            error_message = response.text
            print(f"Error updating Dataflow Gen2: {response.status_code} - {error_message}")
            return {'message': {'error': error_message, 'status_code': response.status_code}}


    def _rewrite_data_destination_queries(self, m_code: str, destination_type: str,
                                           destination_workspace_id: str,
                                           destination_item_id: str) -> str:
        """
        Rewrites all _DataDestination queries in M code to point to a new destination type.
        Preserves the table name from each existing _DataDestination query.
        Works for both standard format (with NavigationTable.CreateTableOnDemand)
        and CI/CD format (without wrapper).

        Args:
            m_code: The M (Power Query) code string.
            destination_type: Target destination - 'Lakehouse' or 'Warehouse'.
            destination_workspace_id: Workspace ID of the target destination.
            destination_item_id: Item ID of the target (lakehouseId or warehouseId).

        Returns:
            Modified M code with rewritten _DataDestination queries.
        """
        def replace_match(match):
            full_match = match.group(0)
            query_name = match.group(1)

            # Extract table name from existing query
            # Use word boundaries to avoid matching workspaceId, lakehouseId, warehouseId, ItemKind
            table_match = re.search(r'\b(?:Id|Item)\b\s*=\s*"([^"]+)"', full_match)
            table_name = table_match.group(1) if table_match else query_name

            if destination_type.lower() == 'warehouse':
                return (
                    f'shared {query_name}_DataDestination = let\r\n'
                    f'  Pattern = Fabric.Warehouse([CreateNavigationProperties = false, HierarchicalNavigation = null]),\r\n'
                    f'  Navigation_1 = Pattern{{[workspaceId = "{destination_workspace_id}"]}}[Data],\r\n'
                    f'  Navigation_2 = Navigation_1{{[warehouseId = "{destination_item_id}"]}}[Data],\r\n'
                    f'  TableNavigation = Navigation_2{{[Item = "{table_name}", Schema = "dbo"]}}?[Data]?\r\n'
                    f'in\r\n'
                    f'  TableNavigation;\r\n'
                )
            else:  # lakehouse
                return (
                    f'shared {query_name}_DataDestination = let\r\n'
                    f'  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = null]),\r\n'
                    f'  Navigation_1 = Pattern{{[workspaceId = "{destination_workspace_id}"]}}[Data],\r\n'
                    f'  Navigation_2 = Navigation_1{{[lakehouseId = "{destination_item_id}"]}}[Data],\r\n'
                    f'  TableNavigation = Navigation_2{{[Id = "{table_name}", ItemKind = "Table"]}}?[Data]?\r\n'
                    f'in\r\n'
                    f'  TableNavigation;\r\n'
                )

        pattern = r'shared\s+(\w+)_DataDestination\s*=\s*let[\s\S]*?;\r?\n'
        return re.sub(pattern, replace_match, m_code)


    def _update_destination_connections(self, connections: list, destination_type: str) -> list:
        """
        Updates connection entries to match the new destination type.
        Replaces Lakehouse/Warehouse connection entries with the target type.

        Args:
            connections: List of connection dicts (connectionOverrides, trustedConnections, or CI/CD connections).
            destination_type: Target destination - 'Lakehouse' or 'Warehouse'.

        Returns:
            Updated connections list.
        """
        source_types = ('Lakehouse', 'Warehouse')
        target = 'Lakehouse' if destination_type.lower() == 'lakehouse' else 'Warehouse'

        updated = []
        for conn in connections:
            conn = dict(conn)  # Shallow copy to avoid mutating original
            if conn.get('kind') in source_types:
                conn['kind'] = target
                conn['path'] = target
                if 'connectionName' in conn:
                    conn['connectionName'] = json.dumps({"kind": target, "path": target})
            updated.append(conn)
        return updated


    def change_data_destination(self, definition: Dict, destination_type: str,
                                destination_workspace_id: str, destination_item_id: str) -> Dict:
        """
        Changes the data destination of a dataflow definition, keeping everything else as-is.

        Rewrites all _DataDestination queries to point to a new destination type
        (e.g., switch from Lakehouse to Warehouse or vice versa).
        Only queries with an existing data destination (_DataDestination suffix) are affected.
        Auto-detects whether the definition is standard (PBI API) or CI/CD (Fabric API) format.

        For standard format (PBI API response), modifies:
        - pbi:mashup.document: Rewrites _DataDestination queries.
        - pbi:mashup.connectionOverrides: Updates Lakehouse/Warehouse connections.
        - pbi:mashup.trustedConnections: Updates Lakehouse/Warehouse connections.

        For CI/CD format (Fabric API definition), modifies:
        - mashup.pq: Rewrites _DataDestination queries.
        - queryMetadata.json: Updates connections.

        Note: The [DataDestinations] annotation settings (Automatic vs Manual mapping) in CI/CD
        format are preserved as-is. If switching to a Warehouse destination requires Manual column
        mappings, adjust the annotation in the mashup.pq accordingly.

        Args:
            definition: The dataflow definition dict. Either:
                - Standard format: Full PBI API response from _get_dataflow_pbi_definition.
                - CI/CD format: Fabric API definition from get_dataflow_gen2_definition.
            destination_type: Target destination type - 'Lakehouse' or 'Warehouse'.
            destination_workspace_id: Workspace ID where the target Lakehouse/Warehouse resides.
            destination_item_id: The ID of the target Lakehouse or Warehouse.

        Returns:
            Dict: A deep copy of the definition with updated data destinations.
                Returns error dict if format is unrecognized or no mashup document is found.
        """
        if destination_type.lower() not in ('lakehouse', 'warehouse'):
            return {'message': 'destination_type must be "Lakehouse" or "Warehouse".', 'content': ''}

        # Detect format
        is_cicd = 'definition' in definition and 'parts' in definition.get('definition', {})
        is_standard = 'pbi:mashup' in definition

        if not is_cicd and not is_standard:
            return {'message': 'Unrecognized definition format. Expected standard (PBI API) or CI/CD (Fabric API) format.', 'content': ''}

        result = copy.deepcopy(definition)

        if is_standard:
            mashup = result.get('pbi:mashup', {})
            document = mashup.get('document', '')

            if not document:
                return {'message': 'No mashup document found in definition.', 'content': ''}

            # Rewrite _DataDestination queries in M code
            mashup['document'] = self._rewrite_data_destination_queries(
                document, destination_type, destination_workspace_id, destination_item_id
            )

            # Update connections
            if 'connectionOverrides' in mashup:
                mashup['connectionOverrides'] = self._update_destination_connections(
                    mashup['connectionOverrides'], destination_type
                )
            if 'trustedConnections' in mashup:
                mashup['trustedConnections'] = self._update_destination_connections(
                    mashup['trustedConnections'], destination_type
                )

            return result

        elif is_cicd:
            parts = result['definition']['parts']

            for part in parts:
                payload = base64.b64decode(part['payload']).decode('utf-8')

                if part['path'] == 'mashup.pq':
                    # Rewrite _DataDestination queries in mashup.pq
                    payload = self._rewrite_data_destination_queries(
                        payload, destination_type, destination_workspace_id, destination_item_id
                    )
                    part['payload'] = base64.b64encode(payload.encode('utf-8')).decode('utf-8')

                elif part['path'] == 'queryMetadata.json':
                    # Update connections in queryMetadata.json
                    metadata = json.loads(payload)
                    if 'connections' in metadata:
                        metadata['connections'] = self._update_destination_connections(
                            metadata['connections'], destination_type
                        )
                    payload = json.dumps(metadata, indent=2)
                    part['payload'] = base64.b64encode(payload.encode('utf-8')).decode('utf-8')

            return result


    def create_dataflow_with_new_destination(
                self,
                workspace_id: str,
                dataflow_id: str,
                destination_type: str,
                destination_workspace_id: str,
                destination_item_id: str,
                display_name: str = '',
                target_workspace_id: str = '',
                compute_engine_settings: Dict = None) -> Dict:
        """
        Creates a new Dataflow Gen2 CI/CD from an existing Gen2 dataflow (standard or CI/CD),
        changing the data destination to a new Lakehouse or Warehouse.

        Auto-detects whether the source is standard (PBI API) or CI/CD (Fabric API):
        - Standard Gen2: Fetches via PBI API, changes destination, converts to CI/CD, creates.
        - CI/CD Gen2: Fetches via Fabric API, changes destination, creates.

        Only queries with an existing data destination are affected.

        Args:
            workspace_id (str): Workspace ID where the source dataflow resides.
            dataflow_id (str): ID of the source dataflow.
            destination_type (str): Target destination type - 'Lakehouse' or 'Warehouse'.
            destination_workspace_id (str): Workspace ID where the target Lakehouse/Warehouse resides.
            destination_item_id (str): The ID of the target Lakehouse or Warehouse.
            display_name (str, optional): Display name for the new dataflow.
                If not provided, uses the original name with '_cicd' suffix.
            target_workspace_id (str, optional): Workspace where the new dataflow will be created.
                If not provided, creates in the same workspace as the source.
            compute_engine_settings (Dict, optional): Compute engine settings for the new CI/CD dataflow.
                Only used when converting from standard to CI/CD format.

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the new dataflow details.
        """
        if workspace_id == '':
            return {'message': 'Missing workspace id, please check.', 'content': ''}
        if dataflow_id == '':
            return {'message': 'Missing dataflow id, please check.', 'content': ''}
        if destination_type.lower() not in ('lakehouse', 'warehouse'):
            return {'message': 'destination_type must be "Lakehouse" or "Warehouse".', 'content': ''}

        create_workspace_id = target_workspace_id if target_workspace_id != '' else workspace_id

        # Try Fabric API first (CI/CD format)
        print(f"Checking if dataflow {dataflow_id} is Gen2 CI/CD...")
        cicd_result = self.get_dataflow_gen2_definition(workspace_id, dataflow_id)

        if cicd_result.get('message') == 'Success':
            # CI/CD dataflow
            cicd_content = cicd_result['content']

            if display_name == '':
                # Extract name from .platform
                for part in cicd_content.get('definition', {}).get('parts', []):
                    if part['path'] == '.platform':
                        platform = json.loads(base64.b64decode(part['payload']).decode('utf-8'))
                        display_name = platform.get('metadata', {}).get('displayName', 'dataflow') + '_cicd'
                        break

            # Change data destination
            print(f"Changing data destination to {destination_type}...")
            modified = self.change_data_destination(
                cicd_content, destination_type, destination_workspace_id, destination_item_id
            )

            # Update display name in .platform
            for part in modified['definition']['parts']:
                if part['path'] == '.platform':
                    platform = json.loads(base64.b64decode(part['payload']).decode('utf-8'))
                    platform['metadata']['displayName'] = display_name
                    part['payload'] = base64.b64encode(
                        json.dumps(platform, indent=2).encode('utf-8')
                    ).decode('utf-8')
                    break

            print(f"Creating Dataflow Gen2 CI/CD '{display_name}' in workspace {create_workspace_id}...")
            return self.create_dataflow_gen2_from_definition(create_workspace_id, display_name, modified)

        # Standard Gen2 - fetch from PBI API
        print("Dataflow is standard Gen2. Fetching definition via PBI API...")
        pbi_result = self._get_dataflow_pbi_definition(workspace_id, dataflow_id)

        if pbi_result.get('message') != 'Success':
            return pbi_result

        pbi_content = pbi_result['content']

        if display_name == '':
            display_name = pbi_content.get('name', 'dataflow') + '_cicd'

        # Change data destination on the standard definition
        print(f"Changing data destination to {destination_type}...")
        modified = self.change_data_destination(
            pbi_content, destination_type, destination_workspace_id, destination_item_id
        )

        # Convert to CI/CD format
        print("Converting to CI/CD format...")
        definition = self._convert_gen2_to_cicd_definition(modified, display_name, compute_engine_settings)

        if definition is None:
            return {'message': {'error': 'Could not extract mashup document from dataflow.', 'content': ''}}

        print(f"Creating Dataflow Gen2 CI/CD '{display_name}' in workspace {create_workspace_id}...")
        return self.create_dataflow_gen2_from_definition(create_workspace_id, display_name, definition)


    def replace_dataflow_destination(
                self,
                workspace_id: str,
                dataflow_id: str,
                destination_type: str,
                destination_workspace_id: str,
                destination_item_id: str,
                compute_engine_settings: Dict = None) -> Dict:
        """
        Replaces the data destination of an existing Dataflow Gen2 in-place.

        Auto-detects whether the source is standard (PBI API) or CI/CD (Fabric API):
        - CI/CD Gen2: Updates the existing dataflow definition in-place via Fabric API (POST updateDefinition).
        - Standard Gen2: Creates a new CI/CD dataflow with the same name and deletes
          the original standard dataflow. The new dataflow will have a different ID.

        Only queries with an existing data destination are affected.
        The dataflow name, queries, and all other settings are preserved.

        Args:
            workspace_id (str): Workspace ID where the dataflow resides.
            dataflow_id (str): ID of the dataflow to update.
            destination_type (str): Target destination type - 'Lakehouse' or 'Warehouse'.
            destination_workspace_id (str): Workspace ID where the target Lakehouse/Warehouse resides.
            destination_item_id (str): The ID of the target Lakehouse or Warehouse.
            compute_engine_settings (Dict, optional): Compute engine settings for the CI/CD dataflow.
                Only used when converting from standard to CI/CD format.

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the updated/new dataflow details.
        """
        if workspace_id == '':
            return {'message': 'Missing workspace id, please check.', 'content': ''}
        if dataflow_id == '':
            return {'message': 'Missing dataflow id, please check.', 'content': ''}
        if destination_type.lower() not in ('lakehouse', 'warehouse'):
            return {'message': 'destination_type must be "Lakehouse" or "Warehouse".', 'content': ''}

        # Try Fabric API first (CI/CD format)
        print(f"Checking if dataflow {dataflow_id} is Gen2 CI/CD...")
        cicd_result = self.get_dataflow_gen2_definition(workspace_id, dataflow_id)

        if cicd_result.get('message') == 'Success':
            # CI/CD dataflow — update in-place
            cicd_content = cicd_result['content']

            # Extract current display name from .platform
            display_name = 'dataflow'
            for part in cicd_content.get('definition', {}).get('parts', []):
                if part['path'] == '.platform':
                    platform = json.loads(base64.b64decode(part['payload']).decode('utf-8'))
                    display_name = platform.get('metadata', {}).get('displayName', 'dataflow')
                    break

            # Change data destination
            print(f"Changing data destination to {destination_type}...")
            modified = self.change_data_destination(
                cicd_content, destination_type, destination_workspace_id, destination_item_id
            )

            # Update the existing dataflow in-place
            print(f"Updating Dataflow Gen2 CI/CD '{display_name}' (ID: {dataflow_id}) in-place...")
            return self.update_dataflow_gen2_from_definition(
                workspace_id, dataflow_id, display_name, modified
            )

        # Standard Gen2 — create new CI/CD with same name, then delete the original
        print("Dataflow is standard Gen2. Fetching definition via PBI API...")
        pbi_result = self._get_dataflow_pbi_definition(workspace_id, dataflow_id)

        if pbi_result.get('message') != 'Success':
            return pbi_result

        pbi_content = pbi_result['content']
        display_name = pbi_content.get('name', 'dataflow')

        # Change data destination
        print(f"Changing data destination to {destination_type}...")
        modified = self.change_data_destination(
            pbi_content, destination_type, destination_workspace_id, destination_item_id
        )

        # Convert to CI/CD format (keeping the same name)
        print("Converting to CI/CD format...")
        definition = self._convert_gen2_to_cicd_definition(modified, display_name, compute_engine_settings)

        if definition is None:
            return {'message': {'error': 'Could not extract mashup document from dataflow.', 'content': ''}}

        # Delete the original standard dataflow first (name must be free for the new one)
        print(f"Deleting original standard dataflow '{display_name}' (ID: {dataflow_id})...")
        delete_result = self.delete_dataflow(workspace_id, dataflow_id, type='pbi')
        if delete_result.get('message') != 'Success':
            print(f"Warning: Could not delete original dataflow: {delete_result}")
            return {'message': {'error': f'Failed to delete original dataflow before recreating: {delete_result}', 'content': ''}}

        # Create the new CI/CD dataflow with the same name
        print(f"Creating Dataflow Gen2 CI/CD '{display_name}' in workspace {workspace_id}...")
        return self.create_dataflow_gen2_from_definition(workspace_id, display_name, definition)


    def _transform_mashup_to_cicd(self, document: str, gen2_content: Dict) -> str:
        """
        Transforms a Gen2 standard M document into the CI/CD mashup.pq format.

        Key transformations:
        - Adds [StagingDefinition] header if fastCopy is enabled.
        - Adds [DataDestinations] annotations before queries that write to destinations.
        - Removes internal pipeline queries (DefaultStaging, FastCopyStaging, *_WriteToDataDestination, *_TransformForWriteToDataDestination).
        - Removes [Staging = "..."] annotations.
        - Simplifies DataDestination queries by removing NavigationTable.CreateTableOnDemand wrapper.
        """
        result = document

        # 1. Add StagingDefinition if fastCopy is enabled
        if gen2_content.get('ppdf:fastCopy', False):
            result = '[StagingDefinition = [Kind = "FastCopy"]]\n' + result

        # 2. Identify queries with data destinations (those that have _WriteToDataDestination counterparts)
        dest_queries = re.findall(r'shared\s+(\w+)_WriteToDataDestination\s*=', result)

        # 3. Remove [Staging = "..."] annotations
        result = re.sub(r'\[Staging\s*=\s*"[^"]*"\]\r?\n', '', result)

        # 4. Remove internal pipeline queries
        internal_queries = ['DefaultStaging', 'FastCopyStaging']
        for qname in dest_queries:
            internal_queries.append(f'{qname}_WriteToDataDestination')
            internal_queries.append(f'{qname}_TransformForWriteToDataDestination')

        for query_name in internal_queries:
            pattern = rf'shared\s+{re.escape(query_name)}\s*=\s*let[\s\S]*?;\r?\n'
            result = re.sub(pattern, '', result)

        # 5. Add [DataDestinations] annotation before queries that have destinations
        for query_name in dest_queries:
            dd_annotation = (
                f'[DataDestinations = {{[Definition = [Kind = "Reference", '
                f'QueryName = "{query_name}_DataDestination", IsNewTarget = true], '
                f'Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}}]\n'
            )
            result = result.replace(f'shared {query_name} =', f'{dd_annotation}shared {query_name} =')

        # 6. Simplify DataDestination queries - remove NavigationTable.CreateTableOnDemand wrapper
        result = re.sub(
            r',\r?\n\s*Table\s*=\s*NavigationTable\.CreateTableOnDemand\([^\n]*\)\r?\nin\r?\n\s*Table;',
            '\r\nin\r\n  TableNavigation;\r\n',
            result
        )

        return result


    def _build_query_metadata(self, gen2_content: Dict, compute_engine_settings: Dict = None) -> Dict:
        """
        Builds the queryMetadata.json content for CI/CD from Gen2 standard PBI API response.

        Args:
            gen2_content (Dict): Full response from PBI API.
            compute_engine_settings (Dict, optional): Override compute engine settings.
                If not provided, derives allowFastCopy from ppdf:fastCopy.
        """
        mashup = gen2_content.get('pbi:mashup', {})
        queries_metadata = mashup.get('queriesMetadata', {})
        annotations = gen2_content.get('annotations', [])

        # Internal queries to exclude
        internal_suffixes = ('_WriteToDataDestination', '_TransformForWriteToDataDestination')
        internal_names = ('DefaultStaging', 'FastCopyStaging')

        # Filter and transform queriesMetadata
        cicd_queries = {}
        for name, meta in queries_metadata.items():
            if name in internal_names or any(name.endswith(s) for s in internal_suffixes):
                continue
            entry = {
                'queryId': meta.get('queryId', ''),
                'queryName': meta.get('queryName', name),
                'loadEnabled': False
            }
            if meta.get('queryGroupId'):
                entry['queryGroupId'] = meta['queryGroupId']
            if name.endswith('_DataDestination'):
                entry['isHidden'] = True
            cicd_queries[name] = entry

        # Extract query groups from annotations
        query_groups = []
        for ann in annotations:
            if ann.get('name') == 'pbi:QueryGroups':
                raw_groups = json.loads(ann['value'])
                for g in raw_groups:
                    group = {
                        'id': g['Id'],
                        'name': g['Name'],
                        'description': g.get('Description', '')
                    }
                    if g.get('Order') is not None:
                        group['order'] = g['Order']
                    query_groups.append(group)
                break

        # Build connections from connectionOverrides
        connections = []
        for conn in mashup.get('connectionOverrides', []):
            connections.append({
                'path': conn['path'],
                'kind': conn['kind']
            })

        # Build computeEngineSettings
        # Note: "Allow combining data from multiple sources" (pbi:mashup.fastCombine) is not
        # part of the CI/CD definition format. It must be configured via the Fabric portal UI.
        if compute_engine_settings is not None:
            engine_settings = compute_engine_settings
        else:
            engine_settings = {}
            fast_copy = gen2_content.get('ppdf:fastCopy', False)
            if not fast_copy:
                engine_settings['allowFastCopy'] = False

        return {
            'formatVersion': '202502',
            'computeEngineSettings': engine_settings,
            'name': gen2_content.get('name', ''),
            'queryGroups': query_groups,
            'documentLocale': gen2_content.get('culture', 'en-US'),
            'queriesMetadata': cicd_queries,
            'connections': connections
        }


    def _convert_gen2_to_cicd_definition(self, gen2_content: Dict, display_name: str, compute_engine_settings: Dict = None) -> Dict:
        """
        Converts a Gen2 standard dataflow definition (from PBI API) to Gen2 CI/CD definition format (Fabric API).

        Builds three definition parts:
        - mashup.pq: Transformed Power Query M script.
        - queryMetadata.json: Query metadata, groups, connections.
        - .platform: Platform metadata with display name.

        Args:
            gen2_content (Dict): Full response from PBI API GET /groups/{ws}/dataflows/{df}.
            display_name (str): Display name for the new CI/CD dataflow.
            compute_engine_settings (Dict, optional): Override compute engine settings
                (e.g. allowFastCopy, allowPartitionedCompute, allowModernEvaluationEngine).
                If not provided, derives from source properties.

        Returns:
            Dict: CI/CD definition payload ready for create_dataflow_gen2_from_definition, or None if conversion fails.
        """
        mashup = gen2_content.get('pbi:mashup', {})
        document = mashup.get('document', '')

        if not document:
            return None

        # Build mashup.pq
        mashup_pq = self._transform_mashup_to_cicd(document, gen2_content)

        # Build queryMetadata.json
        query_metadata = self._build_query_metadata(gen2_content, compute_engine_settings)

        # Build .platform
        platform = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {
                "type": "Dataflow",
                "displayName": display_name
            },
            "config": {
                "version": "2.0",
                "logicalId": "00000000-0000-0000-0000-000000000000"
            }
        }

        # Encode all parts as base64
        mashup_pq_b64 = base64.b64encode(mashup_pq.encode('utf-8')).decode('utf-8')
        query_metadata_b64 = base64.b64encode(json.dumps(query_metadata, indent=2).encode('utf-8')).decode('utf-8')
        platform_b64 = base64.b64encode(json.dumps(platform, indent=2).encode('utf-8')).decode('utf-8')

        return {
            "definition": {
                "parts": [
                    {"path": "queryMetadata.json", "payload": query_metadata_b64, "payloadType": "InlineBase64"},
                    {"path": "mashup.pq", "payload": mashup_pq_b64, "payloadType": "InlineBase64"},
                    {"path": ".platform", "payload": platform_b64, "payloadType": "InlineBase64"}
                ]
            }
        }


    def upgrade_to_gen2_cicd(
                self,
                workspace_id: str,
                dataflow_id: str,
                display_name: str = '',
                description: str = '',
                destination_workspace_id: str = '',
                include_schedule: bool = False,
                compute_engine_settings: Dict = None,
                source_type: str = 'gen1') -> Dict:
        """
        Upgrades a Dataflow Gen1 or Gen2 (standard) to Dataflow Gen2 CI/CD (native Fabric).

        For Gen1: Uses the Power BI saveAsNativeArtifact API (preview) to convert directly.
        Handles connection format updates, sensitivity labels, and optionally migrates refresh schedules.

        For Gen2 (standard): Fetches the definition via PBI API and converts it to the CI/CD format
        (mashup.pq, queryMetadata.json, .platform), then creates a new Dataflow Gen2 CI/CD via Fabric API.
        If the dataflow is already CI/CD, it re-creates it with the given display name.

        Note: This method creates a NEW Dataflow Gen2 CI/CD item. The original dataflow is NOT
        deleted automatically. You can use delete_dataflow() to remove the original after verifying
        the new dataflow works correctly.

        Args:
            workspace_id (str): The ID of the workspace where the source dataflow resides.
            dataflow_id (str): The ID of the source dataflow to upgrade.
            display_name (str, optional): The display name for the new Dataflow Gen2 CI/CD.
                If not provided, for Gen1 the API auto-generates a name (e.g. original_name_copy1).
                For Gen2, uses the original dataflow name with '_cicd' suffix.
            description (str, optional): Description for the new artifact. If not provided,
                copies the description from the source dataflow (Gen1 only).
            destination_workspace_id (str, optional): The ID of the workspace where the new dataflow
                will be created. If not provided, creates in the same workspace as the source.
            include_schedule (bool, optional): Whether to migrate the refresh schedule from the source
                dataflow (Gen1 only). The schedule is copied in disabled state. Defaults to False.
            compute_engine_settings (Dict, optional): Compute engine settings for the new CI/CD dataflow
                (Gen2 only). Supported keys: allowFastCopy (bool), allowPartitionedCompute (bool),
                allowModernEvaluationEngine (bool). If not provided, derives allowFastCopy from the
                source dataflow's ppdf:fastCopy setting.
            source_type (str): Type of source dataflow - 'gen1' or 'gen2'. Defaults to 'gen1'.

        Returns:
            Dict: A dictionary containing the status ('Success' or error) and the details of the newly created Dataflow Gen2 CI/CD.
        """
        if workspace_id == '':
            return {'message': 'Missing workspace id, please check.', 'content': ''}

        if dataflow_id == '':
            return {'message': 'Missing dataflow id, please check.', 'content': ''}

        if source_type not in ('gen1', 'gen2'):
            return {'message': 'source_type must be "gen1" or "gen2".', 'content': ''}

        # If no destination workspace provided, use the source workspace
        target_workspace_id = destination_workspace_id if destination_workspace_id != '' else workspace_id

        if source_type == 'gen1':
            # Use the dedicated saveAsNativeArtifact API for Gen1 → Gen2 CI/CD conversion
            request_url = f'{self.main_url}/groups/{workspace_id}/dataflows/{dataflow_id}/saveAsNativeArtifact'

            body = {
                'includeSchedule': include_schedule
            }

            if display_name != '':
                body['displayName'] = display_name

            if description != '':
                body['description'] = description

            if target_workspace_id != workspace_id:
                body['targetWorkspaceId'] = target_workspace_id

            print(f"Converting Gen1 dataflow {dataflow_id} to Gen2 CI/CD via saveAsNativeArtifact...")
            r = requests.post(url=request_url, headers=self.headers, json=body)

            if r.status_code == 200:
                response = json.loads(r.content)
                artifact = response.get('artifactMetadata', {})
                errors = response.get('errors', [])

                if errors:
                    print(f"Migration completed with warnings: {errors}")

                print(f"Successfully created Gen2 CI/CD. New artifact ID: {artifact.get('objectId', 'N/A')}")
                return {'message': 'Success', 'content': response, 'warnings': errors}
            else:
                try:
                    response = json.loads(r.content)
                    error_message = response.get('error', {}).get('message', r.text)
                except Exception:
                    error_message = r.text
                print(f"Error converting Gen1 dataflow: {r.status_code} - {error_message}")
                return {'message': {'error': error_message, 'status_code': r.status_code}}

        elif source_type == 'gen2':
            # For Gen2: first check if already CI/CD via Fabric API
            print(f"Checking if dataflow {dataflow_id} is already Gen2 CI/CD...")
            gen2_definition = self.get_dataflow_gen2_definition(workspace_id, dataflow_id)

            if gen2_definition.get('message') == 'Success':
                # Already a CI/CD dataflow - re-create with the definition
                if display_name == '':
                    display_name = gen2_definition['content'].get('displayName', 'dataflow') + '_cicd'

                print(f"Dataflow is already Gen2 CI/CD. Creating copy as '{display_name}' in workspace {target_workspace_id}...")
                return self.create_dataflow_gen2_from_definition(target_workspace_id, display_name, gen2_definition['content'])

            # Standard Gen2 - fetch from PBI API and convert
            print("Dataflow is standard Gen2. Fetching definition via PBI API for conversion...")
            pbi_result = self._get_dataflow_pbi_definition(workspace_id, dataflow_id)

            if pbi_result.get('message') != 'Success':
                return pbi_result

            pbi_content = pbi_result['content']

            # If display_name not provided, use original name with _cicd suffix
            if display_name == '':
                display_name = pbi_content.get('name', 'dataflow') + '_cicd'

            # Convert PBI API definition to CI/CD format
            definition = self._convert_gen2_to_cicd_definition(pbi_content, display_name, compute_engine_settings)

            if definition is None:
                return {'message': {'error': 'Could not extract mashup document from dataflow. The dataflow may not contain any queries.', 'content': ''}}

            # Create the new Gen2 CI/CD dataflow
            print(f"Creating Dataflow Gen2 CI/CD '{display_name}' in workspace {target_workspace_id}...")
            return self.create_dataflow_gen2_from_definition(target_workspace_id, display_name, definition)

