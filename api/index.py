"""Vercel serverless entrypoint.

Vercel's @vercel/python runtime serves the module-level WSGI callable named
`app`. All logic lives in the root `app.py`; this file only re-exports it.

Note: `app.py`'s `if __name__ == "__main__": app.run(...)` block is NOT executed
here (that only runs the local dev server), so serverless deploys can't
accidentally start the Werkzeug debugger. Configuration comes from Vercel
environment variables — see docs/DEPLOY.md.
"""

from app import app  # noqa: F401  (WSGI app served by Vercel)

# Some Vercel setups look for `handler`; expose it as an alias for robustness.
handler = app
