# Renty - Car Rental Management

Renty is a Django-based car rental management system with a modern PyQt5 desktop client. This repo includes:

- Backend API (Django + DRF)
- Desktop app (`desktopapp/` - PyQt5)
- Invoice/contract HTML templates
- Docker setup for easy deployment

## Branding

This project uses the "Renty" brand with a soft orange accent palette.

- Primary accent: `#ed8936` / `#f59e0b`
- Darker hover/pressed accents: `#c56a1b`, `#dd6b20`, `#9c4221`
- Desktop logo file expected: `carrental/desktopapp/renty.png`
  - If `renty.png` is missing, the app gracefully falls back to a text logo.

## Project Structure

```
carrental/
  carrental/              # Django project
    settings.py           # Config (STATIC_ROOT, MEDIA_ROOT, etc.)
  rentcars/               # Django app with API views
  desktopapp/             # PyQt5 desktop application
  media/                  # Uploaded files (mounted in Docker)
  manage.py               # Django entrypoint
  requirements.txt        # Full dev deps (includes PyQt5)
  requirements-server.txt # Server-only deps (excludes PyQt5)
  Dockerfile
  docker-compose.yml
  .dockerignore
  .gitignore
  README.md
```

## Local Development (without Docker)

Prereqs: Python 3.12, virtualenv

```bash
# Windows PowerShell examples
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Open: http://127.0.0.1:8000

## Run with Docker

Build and run the backend server (Gunicorn):

```bash
# From carrental/ directory
docker build -t renty-backend .
docker run --name renty-web -p 8000:8000 renty-backend
```

Or with docker-compose:

```bash
# From carrental/ directory
docker-compose up --build -d
```

- App: http://127.0.0.1:8000
- Static files are collected to `staticfiles/`
- Uploaded media is persisted to `media/`

## Environment and Settings

- `ALLOWED_HOSTS` is `[*]` for container usage. Adjust for production.
- `STATIC_ROOT` is configured to `staticfiles/`.
- `MEDIA_ROOT` is `media/`.

For production, set at least:

- `DEBUG=False`
- A secure `SECRET_KEY`
- Restricted `ALLOWED_HOSTS`

You can leverage environment variables via Docker `environment:` entries or a `.env` file (remember `.env` is gitignored).

## Desktop App

The desktop client is in `desktopapp/` and uses the same API base URL:

- Ensure the backend is running at `http://127.0.0.1:8000` (default), or update `API_BASE` in `desktopapp/Authenticate-dashboad.py` if different.
- To run on your host:

```bash
# Ensure dev deps installed (includes PyQt5)
pip install -r requirements.txt
python desktopapp/Authenticate-dashboad.py
```

Logo: place an image at `desktopapp/renty.png` (PNG recommended). The app will fallback to text if no image exists.

## Contracts/Invoices

- Contract HTML template: `desktopapp/carscontract.html` (orange palette applied)
- Server-side contract generation: `rentcars/views.py::generate_rental_contract`
  - Embeds `desktopapp/renty.png` if present.

## Common Commands

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files (Dockerfile does this automatically)
python manage.py collectstatic --noinput
```

## Notes

- Docker image uses `requirements-server.txt` to avoid bundling the desktop runtime (PyQt5) on the server.
- Media and static volumes are mounted in `docker-compose.yml` for persistence and local inspection.

## License

Proprietary — internal use for the client project unless otherwise agreed.
