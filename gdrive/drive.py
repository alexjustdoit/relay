"""
Google Drive + Docs integration for Relay.

- Ensures "Relay Handoffs" folder exists (created on first save)
- Creates a Google Doc from the handoff content
- Returns the Doc URL
"""
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

FOLDER_NAME = "Relay Handoffs"


def _drive(creds: Credentials):
    return build("drive", "v3", credentials=creds)


def _docs(creds: Credentials):
    return build("docs", "v1", credentials=creds)


def _get_or_create_folder(creds: Credentials) -> str:
    """Return the ID of the 'Relay Handoffs' folder, creating it if needed."""
    service = _drive(creds)
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder = service.files().create(body={
        "name": FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }, fields="id").execute()
    return folder["id"]


def create_handoff_doc(creds: Credentials, title: str, content: str) -> str:
    """
    Create a Google Doc in the Relay Handoffs folder.
    content is plain text; we insert it as-is.
    Returns the URL of the created doc.
    """
    folder_id = _get_or_create_folder(creds)
    drive_service = _drive(creds)

    file_meta = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    doc_file = drive_service.files().create(body=file_meta, fields="id").execute()
    doc_id = doc_file["id"]

    docs_service = _docs(creds)
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
    ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"
