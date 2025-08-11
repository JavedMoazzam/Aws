# Streamlit Blog App

A secure Streamlit webapp for writing blogs with an admin panel to upload and maintain posts.

## Features
- Admin authentication with PBKDF2 password hashing
- SQLite-backed CRUD for posts
- Image uploads saved to `data/uploads`
- Public blog with list and detail views by slug
- Environment/secrets driven configuration via `.streamlit/secrets.toml`

## Quick start
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/dev_run.sh
```
Then open http://localhost:8501

## Admin login
Defaults come from `.streamlit/secrets.toml`:
- username: `admin`
- password: `change-me`
Change these before exposing publicly.

## Security notes
- Replace `admin_password` and `session_cookie_key` in `.streamlit/secrets.toml`.
- Use a strong random password: `openssl rand -base64 32`.
- SQLite is file-based; ensure the `data/` directory is not exposed by your reverse proxy.
- Streamlit is best behind authentication when deployed on the public internet.

## Data
- Database: `data/blog.db`
- Uploads: `data/uploads`

## Pages
- `streamlit_app.py` is the entrypoint
- Multipage wrappers in `pages/1_Blog.py` and `pages/2_Admin.py`
