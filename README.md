# Nearby Hands — Local Service Marketplace

Nearby Hands is a hackathon MVP that connects customers with local service providers. Customers can discover providers, send service requests, and leave reviews. Providers can manage their profiles, services, availability, and incoming requests. Administrators can verify providers and manage service categories.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL, JWT authentication
- Frontend: HTML, CSS, and vanilla JavaScript

## Project structure

```text
.
├── BACKEND/
│   ├── alembic/             # Database migrations
│   ├── src/                 # FastAPI application
│   ├── .env                 # Local backend configuration (not committed)
│   └── requirements.txt
├── FRONTEND/
│   ├── css/style.css
│   ├── js/                  # API, authentication, pages, and UI helpers
│   └── index.html
└── README.md
```

## Prerequisites

- Python 3.14 or a compatible Python 3 release
- PostgreSQL database

## Backend setup

From the project root:

```bash
cd BACKEND
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

Create `BACKEND/.env` with your local values:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/local_service_marketplace
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Apply migrations, then start the API:

```bash
venv/bin/python -m alembic upgrade head
venv/bin/python -m uvicorn src.main:app --reload
```

The API runs at `http://localhost:8000` and interactive documentation is available at `http://localhost:8000/docs`.

## Frontend setup

In a second terminal:

```bash
cd FRONTEND
python3 -m http.server 5500 --bind 0.0.0.0
```

Open `http://0.0.0.0:5500` in the browser. The frontend expects the backend at `http://localhost:8000`; change the public URL in `FRONTEND/js/config.js` if your API runs elsewhere.

The backend CORS policy permits local frontend origins using `localhost`, `127.0.0.1`, `0.0.0.0`, or `[::1]` on any port.

## Features

### Customer

- Register and log in
- Browse and filter providers by name, service, location, area, and availability
- View provider profiles and reviews
- Create, track, and cancel service requests
- Review completed requests

### Provider

- Register a provider account
- Update profile and availability
- Add or remove offered services
- Accept, reject, and complete incoming requests

### Admin

- View marketplace metrics
- Verify or reject pending providers
- Create, update, and delete service categories

## Authentication

The API issues JWT access tokens through `POST /auth/login`. The frontend stores the token in browser local storage and automatically sends it as:

```text
Authorization: Bearer <access_token>
```

`POST /auth/login` uses form data (`username` is the user's email and `password` is the password). Registration uses JSON at `POST /auth/register`.

## Main API areas

- `/auth` — registration, login, and current session
- `/categories` — public category listing and admin category management
- `/providers` — provider discovery, provider profiles, services, and availability
- `/requests` — customer and provider service-request workflow
- `/reviews` — completed-request reviews and provider reviews
- `/admin` — dashboard and provider verification

## Notes

- Do not commit `BACKEND/.env`, local databases, or `venv/`; these are covered by `.gitignore`.
- The frontend has no build step and no external frontend dependencies.
