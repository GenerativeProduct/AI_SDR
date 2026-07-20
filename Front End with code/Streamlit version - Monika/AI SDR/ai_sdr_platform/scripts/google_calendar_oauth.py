from __future__ import annotations

import argparse

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Authorize the AI SDR Meeting Agent for Google Calendar."
    )
    parser.add_argument(
        "--client-secrets",
        required=True,
        help="Path to the OAuth desktop-app client JSON downloaded from Google Cloud.",
    )
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        access_type="offline",
        prompt="consent",
    )
    if not credentials.refresh_token:
        raise RuntimeError(
            "Google returned no refresh token. Revoke the prior grant and run again."
        )
    print("Add these values to ai_sdr_platform/.env.sdr:")
    print(f"SDR_MEETING_GOOGLE_CLIENT_ID={credentials.client_id}")
    print(f"SDR_MEETING_GOOGLE_CLIENT_SECRET={credentials.client_secret}")
    print(f"SDR_MEETING_GOOGLE_REFRESH_TOKEN={credentials.refresh_token}")


if __name__ == "__main__":
    main()
