"""
Google OAuth client (Authlib).

Activates only if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are present in
the environment. Otherwise GOOGLE_CONFIGURED stays False and the /google/*
endpoints return a 503 explaining the situation.
"""
import os
from authlib.integrations.starlette_client import OAuth

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_CONFIGURED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

oauth = OAuth()

if GOOGLE_CONFIGURED:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
