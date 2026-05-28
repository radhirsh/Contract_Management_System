# ContractOS – Contract Management System

A full-stack, production-ready Django-based Contract Management System for managing contracts, clauses, users, audit logs, redline suggestions, SharePoint sync, and more.
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/651bdb86-e6f3-464a-a4cd-36113a512b28" />

---

## Features
- Dashboard with contract stats, expiring contracts, recent uploads, and activity feed
- CRUD for contracts, clauses, users
- Redline engine with AI suggestions (manual for demo)
- Contract comparison (side-by-side)
- SharePoint integration (config, sync status/log)
- Audit logs
- JWT authentication
- Responsive UI with Tailwind CSS
- PostgreSQL database
- Admin panel for all entities
- Azure OpenAI integration (LLM tasks)
- Azure Document Intelligence for OCR/parsing (PDF, DOCX, scanned image friendly)
- Azure Blob Storage with automatic local-media fallback when Blob config is unavailable
- Celery + Redis for async ingestion, OCR, LLM analysis, and scheduled expiry alerts

---

## Folder Structure
```
contractos/
├── manage.py
├── contractos/           # Django project settings, URLs, WSGI/ASGI
├── contracts/            # Contracts app (models, views, templates)
├── users/                # Custom user app (models, views, templates)
├── clauses/              # Clause repository app
├── audit/                # Audit logs app
├── sharepoint/           # SharePoint integration app
├── templates/            # Global templates
├── static/               # Static files (css, js, images)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### 1. Clone and Install
```sh
git clone <repo-url>
cd contractos
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 1.1 Configure Environment Variables
- Copy `.env.example` to `.env`.
- Add your Azure OpenAI, Azure Document Intelligence, and (optional) Azure Blob credentials.
- If Azure Blob values are missing or disabled, Django automatically uses local file storage.

### 2. Configure Environment
- Copy `.env.example` to `.env` and fill in secrets and DB info.

### 3. Database Setup
```sh
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
```

Seeded demo accounts use password: `Demo@12345`

To reset and reseed demo data:
```sh
python manage.py seed_demo_data --reset
```

### 4. Tailwind CSS (Optional)
- Tailwind is preconfigured for static styling. To rebuild CSS:
```sh
npx tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.css --minify
```

### 5. Run Server
```sh
python manage.py runserver
```

### 6. Run Celery Worker and Beat
Start worker:
```sh
celery -A contractos worker -l info
```

Start scheduler (for 30/60/90 alert jobs):
```sh
celery -A contractos beat -l info
```

## Storage Behavior
- `ENABLE_AZURE_BLOB=True` and valid Azure Blob credentials: file uploads go to Blob.
- If not configured: file uploads go to local media storage (`MEDIA_ROOT`).
- Blob versioning and soft delete are account-level Azure Storage settings; app includes validation flags in env.

---

## API Documentation
- All API endpoints are under `/api/`
- JWT Auth: `/api/users/token/` (obtain), `/api/users/token/refresh/`
- Contracts CRUD: `/api/contracts/`
- Clauses CRUD: `/api/clauses/`
- Users CRUD: `/api/users/`
- Audit logs: `/api/audit/`
- SharePoint: `/api/sharepoint/`

---

## Environment Variables
- See `.env.example` for all required variables.

---

## Deployment
- Set `DJANGO_DEBUG=False` and configure `ALLOWED_HOSTS` in production.
- Use Gunicorn/Uvicorn + Nginx for deployment.
- Set up PostgreSQL and static/media file serving.
- Use HTTPS and secure your secret key.

---

## License
MIT
