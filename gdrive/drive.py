"""
Google Drive + Docs integration for Relay.

- Ensures "Relay Handoffs" folder exists (created on first save)
- Creates a Google Doc from the handoff content
- Reads/writes relay_history.json for cross-session history persistence
- Returns the Doc URL
"""
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

FOLDER_NAME = "Relay Handoffs"
HISTORY_FILENAME = "relay_history.json"


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


def load_history_from_drive(creds: Credentials) -> list | None:
    """
    Load relay_history.json from the Relay Handoffs folder.
    Returns the history list, or None if the file doesn't exist yet.
    """
    try:
        service = _drive(creds)
        folder_id = _get_or_create_folder(creds)
        query = (
            f"name='{HISTORY_FILENAME}' and '{folder_id}' in parents "
            f"and mimeType='application/json' and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if not files:
            return None
        file_id = files[0]["id"]
        content = service.files().get_media(fileId=file_id).execute()
        data = json.loads(content)
        return data if isinstance(data, list) else None
    except Exception:
        return None


def save_history_to_drive(creds: Credentials, history: list) -> None:
    """
    Write relay_history.json to the Relay Handoffs folder.
    Creates the file on first save, overwrites on subsequent saves.
    """
    try:
        import io
        from googleapiclient.http import MediaIoBaseUpload

        service = _drive(creds)
        folder_id = _get_or_create_folder(creds)
        content_bytes = json.dumps(history, indent=2).encode()
        media = MediaIoBaseUpload(
            io.BytesIO(content_bytes),
            mimetype="application/json",
            resumable=False,
        )

        # Check if the file already exists
        query = (
            f"name='{HISTORY_FILENAME}' and '{folder_id}' in parents "
            f"and mimeType='application/json' and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])

        if files:
            service.files().update(fileId=files[0]["id"], media_body=media).execute()
        else:
            service.files().create(
                body={"name": HISTORY_FILENAME, "parents": [folder_id], "mimeType": "application/json"},
                media_body=media,
                fields="id",
            ).execute()
    except Exception:
        pass
