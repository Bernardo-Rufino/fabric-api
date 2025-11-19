# Power BI API Wrapper

### <b><u>Project</u></b>

The objective of this project is to facilitate the interaction with the Power BI REST API.
<br></br>
### <b><u>Setting up</u></b>
- This project suppose that you already have an app registed on Azure (having a client/app id and client secret/credential);

- <b>Install dependencies</b>:

    ```shell
    pip install -r requirements.txt 
    ```

- <b>Setup enviroment variables</b>:
    ```shell
    TENANT_ID='<YOUR_TENANT_ID>'
    CLIENT_ID='<YOUR_CLIENT_ID>'
    CLIENT_SECRET='<YOUR_CLIENT_SECRET>'
    CLIENT_ID_SHAREPOINT='<YOUR_SHAREPOINT_CLIENT_ID>'
    CLIENT_SECRET_SHAREPOINT='<YOUR_SHAREPOINT_CLIENT_SECRET>'
    AZURE_SUBSCRIPTION_ID='<YOUR_AZURE_SUBSCRIPTION_ID>'
    AZURE_RESOURCE_GROUP_ID='<YOUR_AZURE_RESOURCE_GROUP_ID>'
    ```

### Workspaces

- List workspaces;
- List users;
- List reports;
- Add user to workspace;
- Update user role on workspace (individual or batch)
- Remove user from the workspace;

### Datasets

- List datasets on a workspace;
- List users with access to a dataset;
- Add user access rights to a specific dataset;
- Update user access rights to a specific dataset;
- Remove user access rights to a specific dataset;

### Limitations

- Power BI Rest API has a 200 requests per hour limit (you get blocked);
- Not all users can be updated, check the documentation: [Get and update dataset permissions with APIs](https://learn.microsoft.com/en-us/power-bi/developer/embedded/datasets-permissions#get-and-update-dataset-permissions-with-apis);