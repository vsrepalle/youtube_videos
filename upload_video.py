import os
import sys
import traceback
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def auth():
    token_path = os.path.join(BASE_DIR, "token.json")
    secrets_path = os.path.join(BASE_DIR, "client_secrets.json")

    if not os.path.exists(secrets_path):
        raise FileNotFoundError(f"❌ client_secrets.json NOT FOUND at {secrets_path}")

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(google.auth.transport.requests.Request())
        else:
            print("🔐 Opening browser for Google login...")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload(video_path, title):
    print("📤 Starting uploader...")
    print(f"📂 Working directory: {BASE_DIR}")
    print(f"🎞 Video path: {video_path}")

    youtube = auth()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title + " #Shorts",
                "description": "Movie update. 100% original content. #Shorts",
                "tags": ["bollywood", "movie news", "shorts"],
                "categoryId": "25"
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=False)
    )

    print("⏳ Uploading to YouTube...")

    response = request.execute()

    print("\n🎉 UPLOAD SUCCESSFUL")
    print(f"🆔 VIDEO ID : {response['id']}")
    print(f"🔗 https://www.youtube.com/shorts/{response['id']}")

if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError("Usage: python upload_video.py <video_path> <title>")

        upload(sys.argv[1], sys.argv[2])

    except Exception as e:
        print("\n❌ UPLOADER FAILED")
        traceback.print_exc()

    input("\nPress ENTER to close this window...")
