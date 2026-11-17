#!/usr/bin/env python3
"""One-time: authorise the SAVE STATE YouTube channel (upload + manage + analytics).
Starts a localhost listener, prints the consent URL (Claude opens it in Chrome, picks the SAVE STATE channel, Allows).
Writes autopilot/keys/youtube-token.json. Same OAuth client as Figures (project automedia-492314, In production)."""
import os, json, socket
from pathlib import Path
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
from google_auth_oauthlib.flow import InstalledAppFlow
K = Path(__file__).resolve().parents[1] / "keys"
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"]
flow = InstalledAppFlow.from_client_secrets_file(str(K / "youtube-credentials.json"), SCOPES)
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
creds = flow.run_local_server(port=port, open_browser=False, prompt="consent", access_type="offline",
                              authorization_prompt_message="CONSENT_URL: {url}", success_message="SAVE STATE authorised. You can close this tab.")
(K / "youtube-token.json").write_text(creds.to_json()); os.chmod(K / "youtube-token.json", 0o600)
from googleapiclient.discovery import build
me = build("youtube", "v3", credentials=creds).channels().list(part="snippet", mine=True).execute()
print("AUTHORISED channel:", [(c["id"], c["snippet"]["title"]) for c in me.get("items", [])])
