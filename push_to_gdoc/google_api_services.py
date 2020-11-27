import pickle
import tempfile
import os

from appdirs import AppDirs
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pathlib import Path


SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def get_api_services():
    try:
        from google.colab import auth

        auth.authenticate_user()
        return {"docs": build("docs", "v1"), "drive": build("drive", "v3")}
    except ImportError:
        pass

    dirs = AppDirs("push_to_gdoc", "ODSC")
    tmp = Path(tempfile.gettempdir())
    config_dir = Path(dirs.user_config_dir)

    service_creds_raw = os.getenv("PUSH_TO_GDOCS_SERVICE_CREDS")
    if service_creds_raw:
        service_credentials = tmp / "push_google_docs_service_account_creds.json"
        with open(service_credentials, "w+") as service_account_creds_file:
            service_account_creds_file.write(service_creds_raw)
    else:
        service_credentials = config_dir / "service_account_credentials.json"

    if service_credentials.exists():
        creds = service_account.Credentials.from_service_account_file(
            service_credentials, scopes=SCOPES
        )
    else:
        tmp_auth_save = tmp / "push_google_docs_google_auth.pickle"

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if tmp_auth_save.exists():
            with open(tmp_auth_save, "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config_dir / "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(tmp_auth_save, "wb") as token:
                pickle.dump(creds, token)
    return {
        "docs": build("docs", "v1", credentials=creds),
        "drive": build("drive", "v3", credentials=creds),
    }
