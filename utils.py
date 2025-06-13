import os.path
import base64
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add PDF-to-image conversion
from pdf2image import convert_from_path

# If modifying these scopes, delete the file token.json.
# 'gmail.modify' scope allows reading, sending, deleting, and modifying emails,
# which includes downloading attachments.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def authenticate_gmail():
    """
    Authenticates with the Gmail API using OAuth 2.0.
    Returns the authenticated Gmail API service object, or None if an error occurs.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred during Gmail API service build: {error}")
        return None


def get_email_details(service, message_id):
    """
    Fetches full details of an email message.
    """
    try:
        message = service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()
        return message
    except HttpError as error:
        print(f"Error fetching message {message_id}: {error}")
        return None


def download_attachment(service, message_id, part_id, filename, save_path='.'):
    """
    Downloads a specific attachment and handles PDF conversion to PNG.
    Returns a list of saved file paths (only generated PNGs for PDFs, original for others).
    """
    saved_files = []
    try:
        attachment = service.users().messages().attachments().get(
            userId='me', messageId=message_id, id=part_id
        ).execute()
        file_data = base64.urlsafe_b64decode(attachment['data'])
        full_save_path = os.path.join(save_path, filename)
        with open(full_save_path, 'wb') as f:
            f.write(file_data)
        print(f"Downloaded attachment: '{filename}' to '{full_save_path}'")

        # If it's a PDF, convert to PNG(s) without listing the PDF in saved_files
        if filename.lower().endswith('.pdf'):
            try:
                images = convert_from_path(full_save_path)
                base, _ = os.path.splitext(full_save_path)
                for i, image in enumerate(images, start=1):
                    png_name = f"{base}_page{i}.png"
                    image.save(png_name, 'PNG')
                    saved_files.append(png_name)
                    print(f"Converted page {i} to '{png_name}'")
            except Exception as e:
                print(f"Error converting PDF '{filename}' to images: {e}")
        else:
            # For non-PDF attachments, include the original file path
            saved_files.append(full_save_path)

    except HttpError as error:
        print(f"Error downloading '{filename}': {error}")
    except Exception as e:
        print(f"Unexpected error downloading '{filename}': {e}")

    return saved_files


def parse_email_content(service, message, save_path='.'):
    """
    Parses a Gmail message object to extract metadata and download attachments,
    including converting PDFs to PNGs when detected.
    Returns a dict with subject, sender, date, body, has_attachments, and attachment_paths.
    """
    email_data = {
        'subject': 'N/A',
        'sender': 'N/A',
        'date': 'N/A',
        'body': '',
        'has_attachments': False,
        'attachment_paths': []
    }
    message_id = message['id']
    headers = message['payload']['headers']
    for header in headers:
        if header['name'] == 'Subject':
            email_data['subject'] = header['value']
        elif header['name'] == 'From':
            email_data['sender'] = header['value']
        elif header['name'] == 'Date':
            email_data['date'] = header['value']

    parts = message['payload'].get('parts', [])
    if not parts:
        body = message['payload'].get('body', {}).get('data')
        if body:
            try:
                email_data['body'] = base64.urlsafe_b64decode(body).decode('utf-8')
            except Exception as e:
                print(f"Error decoding body for {message_id}: {e}")
    else:
        for part in parts:
            mime_type = part.get('mimeType')
            filename = part.get('filename', '')
            body = part.get('body', {})

            if mime_type == 'text/plain' and 'data' in body:
                try:
                    email_data['body'] = base64.urlsafe_b64decode(body['data']).decode('utf-8')
                except Exception as e:
                    print(f"Error decoding text part for {message_id}: {e}")

            if filename and body.get('attachmentId'):
                email_data['has_attachments'] = True
                saved = download_attachment(
                    service, message_id, body['attachmentId'], filename, save_path
                )
                email_data['attachment_paths'].extend(saved)

            elif mime_type == 'multipart/alternative':
                for sub in part.get('parts', []):
                    sub_mime = sub.get('mimeType')
                    sub_body = sub.get('body', {})
                    sub_fn = sub.get('filename', '')
                    if sub_mime == 'text/plain' and 'data' in sub_body:
                        try:
                            email_data['body'] = base64.urlsafe_b64decode(
                                sub_body['data']).decode('utf-8')
                        except Exception as e:
                            print(f"Error decoding sub-part for {message_id}: {e}")
                    if sub_fn and sub_body.get('attachmentId'):
                        email_data['has_attachments'] = True
                        saved = download_attachment(
                            service, message_id, sub_body['attachmentId'], sub_fn, save_path
                        )
                        email_data['attachment_paths'].extend(saved)

    return email_data


def check_emails_from_sender(service, sender_email, mark_as_read=False, save_path='.'):
    """
    Checks for emails from a sender, parses and downloads attachments,
    with PDF-to-PNG conversion.
    """
    emails_data = []
    try:
        query = f'from:{sender_email} in:inbox'
        results = service.users().messages().list(
            userId='me', q=query
        ).execute()
        messages = results.get('messages', [])
        if not messages:
            print(f"No emails found from {sender_email}.")
            return []
        for msg in messages:
            detail = get_email_details(service, msg['id'])
            if detail:
                data = parse_email_content(
                    service, detail, save_path
                )
                data['message_id'] = msg['id']
                emails_data.append(data)
                if mark_as_read:
                    service.users().messages().modify(
                        userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}
                    ).execute()
        return emails_data
    except HttpError as error:
        print(f"Error checking emails: {error}")
        return []