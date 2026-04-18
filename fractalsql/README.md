# Fractal Flask Backend

Flask + SQLAlchemy backend for user registration, authentication, admin status management, file uploads, and Excel synchronization.

## Setup
- Python 3.10+ recommended.
- Create a virtualenv and install dependencies:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- Copy `.env.example` to `.env` and adjust `SECRET_KEY`, `DATABASE_URL`, `ADMIN_EMAIL`/`ADMIN_PASSWORD`, and `EXCEL_OUTPUT_PATH` (defaults to `G:\fractal website\Base\Base.xlsx`).

## Database
Initialize migrations and create the schema:
```powershell
flask db init
flask db migrate -m "Create users"
flask db upgrade
```
SQLite is the default (`app.db`). Swap `DATABASE_URL` for Postgres if desired.

## Run
```powershell
$env:FLASK_APP="app.py"
flask run
```

## API (JSON)
- `POST /api/auth/register` — fields: name, email, password, phone, id_number, gender, dob (YYYY-MM-DD), social_link, city. Logs user in. Writes Excel snapshot.
- `POST /api/auth/login` — fields: email, password. Session cookie auth.
- `POST /api/auth/logout`
- `GET /api/user/me` — current user (auth required).
- `PATCH /api/user/me` — update profile fields (name, phone, id_number, gender, dob, social_link, city). Validates unique ID number. Writes Excel.
- `POST /api/user/photo` — multipart `photo` upload; returns `url` (`/uploads/<file>`). Persists filename and writes Excel.
- `GET /uploads/<filename>` — serves uploaded files.
- `POST /api/admin/login` — admin credentials from env; sets `session["is_admin"]`.
- `POST /api/admin/logout`
- `GET /api/admin/users` — list all users (admin-only).
- `PATCH /api/admin/users/<id>/status` — body `{ "status": "permanent|temporary|door|declined" }`. Writes Excel.

## Excel Sync
Every create/update/status change triggers `services/excel_export.write_users_to_excel()`, rewriting the spreadsheet at `EXCEL_OUTPUT_PATH` with columns: Name, Email, Phone, ID, DOB, Gender, Social, City, Status, Updated. A file lock (`.lock`) prevents concurrent writes. Ensure the process has write access to that path.

## Front-end Integration Notes
- Replace localStorage with fetch calls to the API above.
- Registration/login use session cookies; include `credentials: "include"` in fetch calls if cross-origin.
- Dashboard can fetch `/api/user/me` to display name/status and photo URL.
- Status-to-icon mapping: permanent=green filled, temporary=green outline, door=yellow, declined=red.
- Admin panel: fetch `/api/admin/users` to populate rows; call the PATCH endpoint to update statuses.
