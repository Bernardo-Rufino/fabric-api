# msdev-kit

Microsoft developer toolkit for Python: Fabric/Power BI, MS Graph (Entra), and SharePoint.

## Installation

### Install from PyPI (recommended)

```shell
pip install msdev-kit
```

### Install from GitHub

```shell
pip install git+https://github.com/Bernardo-Rufino/msdev-kit.git
```

### Install for local development

```shell
git clone https://github.com/Bernardo-Rufino/msdev-kit.git
cd msdev-kit
pip install -e .
```

---

## Prerequisites

- Python >= 3.10
- An Azure app registration with a client ID and client secret

## Getting Started

### Authentication

All classes use a shared `Auth` object. You can use different service principals for different services:

```python
from msdev_kit import Auth

# service principal auth
auth = Auth(tenant_id="...", client_id="...", client_secret="...")

token = auth.get_token()             # Power BI API (default)
token = auth.get_token('fabric')     # Fabric API
token = auth.get_token('graph')      # MS Graph API
token = auth.get_token('azure')      # Azure Management API

# interactive user auth
token = auth.get_token_for_user('pbi')
```

### Credentials

Set up credentials via environment variables or a `.env` file:

```shell
TENANT_ID='<YOUR_TENANT_ID>'
CLIENT_ID='<YOUR_CLIENT_ID>'
CLIENT_SECRET='<YOUR_CLIENT_SECRET>'
```

---

## Sub-packages

### `msdev_kit.fabric` — Fabric & Power BI

All existing Fabric/Power BI classes, accessed via the `fabric` sub-package:

```python
from msdev_kit.fabric import Workspace, Dataset, Report, Dataflow, Pipeline
from msdev_kit import Auth

auth = Auth(tenant_id, client_id, client_secret)
ws = Workspace(auth.get_token('fabric'))
```

#### Workspace

Manage Power BI workspaces, users, and permissions.

| Method | Description |
|---|---|
| `list_workspaces_for_user(...)` | List all workspaces the user has access to, with optional filters. |
| `get_workspace_details(workspace_id)` | Get details for a specific workspace. |
| `list_users(workspace_id)` | List all users in a workspace. |
| `list_reports(workspace_id)` | List all reports in a workspace. |
| `add_user(user_principal_name, workspace_id, access_right, user_type)` | Add a user or service principal to a workspace. |
| `update_user(user_principal_name, workspace_id, access_right)` | Update a user's role on a workspace. |
| `remove_user(user_principal_name, workspace_id)` | Remove a user from a workspace. |
| `batch_update_user(user, workspaces_list)` | Batch update a user across multiple workspaces. |

#### Dataset

Manage datasets (semantic models), permissions, and execute DAX queries.

| Method | Description |
|---|---|
| `list_datasets(workspace_id)` | List all datasets in a workspace. |
| `get_dataset_details(workspace_id, dataset_id)` | Get details of a specific dataset. |
| `get_dataset_name(workspace_id, dataset_id)` | Resolve the display name of a dataset. Tries the PBI API first, falls back to the Fabric semantic models API. |
| `execute_query(workspace_id, dataset_id, query)` | Execute a DAX query against a dataset. Runs a COUNTROWS pre-check to detect if API row/value limits would truncate the result and returns truncation metadata. |
| `list_users(workspace_id, dataset_id)` | List users with access to a dataset. |
| `add_user(user_principal_name, workspace_id, dataset_id, access_right)` | Grant a user access to a dataset. |
| `update_user(user_principal_name, workspace_id, dataset_id, access_right)` | Update a user's access to a dataset. |
| `remove_user(user_principal_name, workspace_id, dataset_id)` | Remove a user's access to a dataset. |
| `list_dataset_related_reports(workspace_id, dataset_id)` | List all reports linked to a dataset. |
| `export_dataset_related_reports(workspace_id, dataset_id)` | Export all reports linked to a dataset as `.pbix` files. |

#### Report

Retrieve report metadata, definitions, visuals, and report-level measures.

| Method | Description |
|---|---|
| `list_reports(workspace_id)` | List all reports in a workspace. |
| `get_report_metadata(workspace_id, report_id)` | Get metadata for a specific report. |
| `get_report_name(workspace_id, report_id)` | Get a report's display name. |
| `list_report_pages(workspace_id, report_id)` | List all pages in a report. |
| `get_report_json_pages_and_visuals(json_data, workspace_id, report_id)` | Parse a PBIR-Legacy report JSON and extract pages and visual details into a DataFrame. |
| `get_legacy_report_json(workspace_id, report_id, operations)` | Get and decode the full report definition for PBIR-Legacy reports. |
| `export_report(workspace_id, report_id, ...)` | Export a report as a `.pbix` file. |
| `get_report_measures(workspace_id, report_id, operations)` | Extract report-level measures and generate a DAX Query View script. Supports both PBIR and PBIR-Legacy formats. |
| `rebind_report(workspace_id, report_id, new_dataset_id, new_dataset_workspace_id, admin, dataset)` | Rebind a report to a new dataset/semantic model and migrate Read access to the new dataset. |

#### Dataflow

Manage Power BI and Fabric dataflows, including Gen1, Gen2, and Gen2 CI/CD.

| Method | Description |
|---|---|
| `list_dataflows(workspace_id)` | List all dataflows in a workspace (Gen1, Gen2 standard, and Gen2 CI/CD). Results are merged and deduplicated with a `source` column. |
| `get_dataflow_details(workspace_id, dataflow_id)` | Get details of a specific dataflow. |
| `get_dataflow_name(workspace_id, dataflow_id)` | Resolve the display name of a dataflow. |
| `create_dataflow(workspace_id, dataflow_content)` | Create a new Power BI dataflow. |
| `delete_dataflow(workspace_id, dataflow_id, type='pbi')` | Delete a dataflow. Use `type='fabric'` for Fabric API. |
| `export_dataflow_json(workspace_id, dataflow_id, dataflow_name)` | Export a dataflow definition as JSON. |
| `get_dataflow_gen2_definition(workspace_id, dataflow_id)` | Get the definition of a Dataflow Gen2 CI/CD item. |
| `create_dataflow_gen2_from_definition(workspace_id, display_name, definition)` | Create a Dataflow Gen2 CI/CD from a definition. |
| `update_dataflow_gen2_from_definition(workspace_id, dataflow_id, display_name, definition)` | Update an existing Dataflow Gen2 CI/CD definition. |
| `get_data_destinations(workspace_id, dataflow_id)` | Get the data destination details for each table in a dataflow. |
| `change_data_destination(workspace_id, dataflow_id, destination_type, ...)` | Change a dataflow's data destination (Lakehouse/Warehouse). Supports `preview`, `replace`, and `create` modes. |
| `create_dataflow_with_new_destination(workspace_id, dataflow_id, ...)` | Create a new Gen2 CI/CD dataflow from an existing one with a different data destination. |
| `upgrade_to_gen2_cicd(...)` | Upgrade a Gen1 or Gen2 (standard) dataflow to Gen2 CI/CD. |

#### Pipeline

Manage Fabric Data Pipelines.

| Method | Description |
|---|---|
| `list_pipelines(workspace_id)` | List all Fabric Data Pipelines in a workspace. |
| `get_pipeline(workspace_id, pipeline_id)` | Get the metadata of a specific pipeline. |
| `get_pipeline_definition(workspace_id, pipeline_id)` | Get the full definition of a Fabric Data Pipeline. |
| `update_pipeline_definition(workspace_id, pipeline_id, definition)` | Update an existing pipeline definition. |
| `get_pipeline_activities(workspace_id, pipeline_id_or_name)` | Get the list of activities from a pipeline. |
| `find_pipelines_by_dataflow(workspace_id, dataflow_id_or_name)` | Find all pipelines in a workspace that reference a specific dataflow. |
| `replace_dataflow_id_in_pipeline(workspace_id, pipeline_id, old_dataflow_id, new_dataflow_id)` | Replace a dataflow ID in all RefreshDataflow activities of a pipeline. |

#### Other modules

| Module | Description |
|---|---|
| `Capacity` | Monitor and manage Power BI and Fabric capacities. |
| `Operations` | Track long-running Fabric API operations. |
| `Admin` | Power BI Admin API operations. |
| `KQLDatabase` | Query Kusto (KQL) databases in Microsoft Fabric. |
| `Notebook` | Manage Fabric notebooks. |
| `Database` | Query and write to SQL databases (Lakehouse, Warehouse) via ODBC. |

---

### `msdev_kit.graph` — MS Graph (Entra)

Manage Entra ID (Azure AD) users and groups via the MS Graph API.

```python
from msdev_kit import Auth
from msdev_kit.graph import GraphClient

auth = Auth(tenant_id, client_id, client_secret)
graph = GraphClient(auth)

user_id = graph.get_user_id('user@company.com')
group_id = graph.get_group_id('Data Team')
members = graph.list_group_members(group_id)
```

| Method | Description |
|---|---|
| `get_user_id(email)` | Resolve user object ID by UPN/email, with mail fallback. |
| `get_group_id(group_name)` | Resolve Entra group object ID by display name. |
| `list_group_members(group_id)` | Paginated member list (id, displayName, mail, UPN). |
| `add_group_member(group_id, user_id)` | Add user to group. Silently ignores already-member errors. |
| `remove_group_member(group_id, user_id)` | Remove user from group. Silently ignores 404/403. |

---

### `msdev_kit.sharepoint` — SharePoint

Manage SharePoint files and folders via MS Graph API (no ACS/Office365 dependency).

```python
from msdev_kit import Auth
from msdev_kit.sharepoint import SharePointClient

auth = Auth(tenant_id, client_id, client_secret)
sp = SharePointClient(auth, sp_hostname='company', sp_site_path='sites/DataTeam')

sp.download_file('/Reports/monthly.xlsx', local_dir='./downloads')
sp.upload_file('/Reports/updated.xlsx', source='./local/updated.xlsx')
sp.create_folder('/Reports/2026')
```

| Method | Description |
|---|---|
| `download_file(file_path, local_dir)` | Download a file from the default document library. Returns local file path. |
| `upload_file(remote_path, source, content_type?)` | Upload/overwrite a file. `source` is a local file path (str) or raw bytes. |
| `create_folder(folder_path)` | Create a folder and all intermediate folders. |

Hostname and site path inputs are normalized automatically — accepts short names (`company`), FQDNs (`company.sharepoint.com`), or full URLs (`https://company.sharepoint.com`).

---

## Limitations

- The Power BI REST API has a **200 requests per hour** rate limit.
- Not all users can be updated via the API. See Microsoft docs: [Dataset permissions](https://learn.microsoft.com/en-us/power-bi/developer/embedded/datasets-permissions#get-and-update-dataset-permissions-with-apis).
- **Dataset query limits** (executeQueries API):
  - Max **100,000 rows** or **1,000,000 values** (rows x columns) per query, whichever is hit first.
  - Max **15 MB** of data per query.
  - **120 query requests per minute** per user.
  - Only **DAX** queries are supported (no MDX, INFO functions, or DMV).
  - Datasets hosted in Azure Analysis Services or with a live connection to on-premises AAS are not supported.
  - Service Principals are not supported for datasets with RLS or SSO enabled.
