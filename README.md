# Menaxhim Dokumentash

## Backend (Starlette)

### Requirements

- Python 3.11+

### Setup

1) Create a virtual environment

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Create `.env`

Copy `.env.example` to `.env` and fill values.

Required variables:

- `DATABASE_URL`
- `JWT_SECRET`
- `DRIVE_FOLDER_ID`
- `GOOGLE_CREDENTIALS_JSON` (paste the entire service-account JSON as a single line)

4) Run the API

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### API Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Postman

Import `api.postman_collection.json`.

The create/replace endpoints are `multipart/form-data` and require selecting a real file in Postman.

### Tests

```bash
pytest -q
```
