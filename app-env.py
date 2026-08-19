"""Backwards-compatible entrypoint.

The two backends were consolidated (TODO P1). All logic now lives in `app.py`,
which loads configuration from the environment (and a `.env` file when
python-dotenv is installed) and includes the wpa-sec leaked-credential
enrichment. This shim keeps `python app-env.py` working for existing docs and
muscle memory.
"""

from app import app  # noqa: F401  (re-exported for WSGI servers: `app-env:app`)

if __name__ == "__main__":
    import os

    # SEC-01: safe defaults; opt into debug / non-local binding via env only.
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "8080"))
    app.run(host=host, port=port, debug=debug)
