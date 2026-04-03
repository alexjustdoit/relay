"""
Google Drive + Docs integration for Relay.

- Ensures "Relay Handoffs" folder exists (created on first save)
- Creates a Google Doc from the handoff content with proper formatting
- Reads/writes relay_history.json for cross-session history persistence
- Returns the Doc URL
"""
import json
import re
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


def _parse_bold(raw: str):
    """
    Strip **bold** markers from text, return (clean_text, [(start, end), ...]).
    Positions are character offsets into clean_text.
    """
    clean = ""
    ranges = []
    last = 0
    for m in re.finditer(r"\*\*(.*?)\*\*", raw):
        clean += raw[last:m.start()]
        s = len(clean)
        clean += m.group(1)
        ranges.append((s, len(clean)))
        last = m.end()
    clean += raw[last:]
    return clean, ranges


def _parse_lines(content: str) -> list[dict]:
    """Parse markdown content into a list of structured line dicts."""
    items = []
    for line in content.split("\n"):
        if line.startswith("# "):
            clean, bold = _parse_bold(line[2:].strip())
            items.append({"text": clean, "style": "HEADING_1", "bullet": None, "bold": bold})
        elif line.startswith("## "):
            clean, bold = _parse_bold(line[3:].strip())
            items.append({"text": clean, "style": "HEADING_2", "bullet": None, "bold": bold})
        elif line.startswith("### "):
            clean, bold = _parse_bold(line[4:].strip())
            items.append({"text": clean, "style": "HEADING_3", "bullet": None, "bold": bold})
        elif line.startswith("- ") or line.startswith("* "):
            clean, bold = _parse_bold(line[2:].strip())
            items.append({"text": clean, "style": "NORMAL_TEXT", "bullet": "BULLET_DISC_CIRCLE_SQUARE", "bold": bold})
        elif not line.strip():
            items.append({"text": "", "style": "NORMAL_TEXT", "bullet": None, "bold": []})
        else:
            clean, bold = _parse_bold(line)
            items.append({"text": clean, "style": "NORMAL_TEXT", "bullet": None, "bold": bold})
    return items


def create_handoff_doc(creds: Credentials, title: str, content: str, metadata: dict | None = None) -> str:
    """
    Create a formatted Google Doc in the Relay Handoffs folder.
    Converts markdown to real Doc formatting: headings, bullets, bold.
    metadata (optional): account_name, type_label, from_name, to_name — prepended as a header block.
    Returns the URL of the created doc.
    """
    folder_id = _get_or_create_folder(creds)
    drive_service = _drive(creds)
    docs_service = _docs(creds)

    # Create empty document
    file_meta = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    doc_file = drive_service.files().create(body=file_meta, fields="id").execute()
    doc_id = doc_file["id"]

    # Prepend header block from metadata
    if metadata:
        header_lines = []
        account_name = metadata.get("account_name", "")
        type_label = metadata.get("type_label", "")
        from_name = metadata.get("from_name", "")
        to_name = metadata.get("to_name", "")

        if account_name:
            header_lines.append(f"# {account_name}")
        if type_label:
            header_lines.append(f"{type_label} Handoff")
        from_to_parts = []
        if from_name:
            from_to_parts.append(f"From: {from_name}")
        if to_name:
            from_to_parts.append(f"To: {to_name}")
        if from_to_parts:
            header_lines.append("  \u2192  ".join(from_to_parts))
        if header_lines:
            content = "\n".join(header_lines) + "\n\n" + content

    parsed = _parse_lines(content)

    # Pass 1: build all insertText requests, tracking character positions
    insert_requests = []
    format_requests = []
    idx = 1  # Google Docs body starts at index 1

    for item in parsed:
        text = item["text"] + "\n"
        line_start = idx
        line_end = idx + len(text)

        insert_requests.append({
            "insertText": {
                "location": {"index": idx},
                "text": text,
            }
        })

        # Paragraph style
        if item["style"] != "NORMAL_TEXT":
            format_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": line_start, "endIndex": line_end},
                    "paragraphStyle": {"namedStyleType": item["style"]},
                    "fields": "namedStyleType",
                }
            })

        # Bullet list
        if item["bullet"]:
            format_requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": line_start, "endIndex": line_end},
                    "bulletPreset": item["bullet"],
                }
            })

        # Inline bold ranges
        for b_start, b_end in item["bold"]:
            format_requests.append({
                "updateTextStyle": {
                    "range": {
                        "startIndex": line_start + b_start,
                        "endIndex": line_start + b_end,
                    },
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })

        idx = line_end

    # Apply insertions first so all text is in the doc before formatting
    if insert_requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": insert_requests},
        ).execute()

    if format_requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": format_requests},
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
