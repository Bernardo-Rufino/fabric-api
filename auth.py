
from azure.identity import ClientSecretCredential

class Auth:

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize variables.

        Args:
            tenant_id (str, optional): tenant ID.
            client_id (str, optional): client ID (app registration).
            client_secret (str, optional): client secret/credentials (app registration).
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


    def get_token(self) -> str:
        """
        Generates the bearer token to be used on Power BI REST API requests.

        Returns:
            str: token for authorization.
        """
        auth_url = 'https://analysis.windows.net/powerbi/api/.default'

        auth = ClientSecretCredential(
                    authority = 'https://login.microsoftonline.com/',
                    tenant_id = self.tenant_id,
                    client_id = self.client_id,
                    client_secret = self.client_secret)

        response = auth.get_token(auth_url)
        access_token = response.token

        return access_token
