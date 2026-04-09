from msal import ConfidentialClientApplication
from backend.app.core.config import settings


class EmailAuth:
    def __init__(self):
        self.authority = f"https://login.microsoftonline.com/{settings.TENANT_ID}"

        # Application permission scope (REQUIRED)
        self.scopes = ["https://graph.microsoft.com/.default"]

        self.app = ConfidentialClientApplication(
            client_id=settings.CLIENT_ID,
            client_credential=settings.CLIENT_SECRET,
            authority=self.authority,
        )

    def get_token(self) -> str:
        token = self.app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" not in token:
            raise RuntimeError(f"Token acquisition failed: {token}")

        return token["access_token"]
