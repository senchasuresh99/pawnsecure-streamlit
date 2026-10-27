# PawnSecure Streamlit Dashboard

A Python/Streamlit starter dashboard that calls the existing PawnSecure Java Spring Boot backend.

## Current architecture

- Frontend: React hosted on Netlify
- Backend: Java Spring Boot hosted on Render (`https://pawnsecure.onrender.com`)
- Database: PostgreSQL hosted on Neon
- New dashboard: Streamlit

This dashboard does **not** run Java inside Streamlit and does not connect directly to Neon. It is a separate frontend that can call existing backend REST APIs.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app defaults to `https://pawnsecure.onrender.com`. You can override it by setting `PAWNSECURE_API_URL` in Streamlit Secrets.

## Deploy on Streamlit Community Cloud

1. Push these files to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Under app Settings → Secrets, add:

```toml
PAWNSECURE_API_URL = "https://pawnsecure.onrender.com"
```

5. Deploy.

## API health check

The dashboard tests `/actuator/health`. That route is available only if Spring Boot Actuator is installed and configured. If it is not available, enter a different health endpoint in the app. Do not expose sensitive Actuator endpoints.

## Before adding real business data

To build the dealer, customer, pawn transaction, fraud review, and subscription screens, map the actual API routes and authentication requirements from the Java project. Use the Java backend for authorization and business rules. Do not expose Neon credentials, JWT signing secrets, SMTP credentials, or customer Aadhaar data in Streamlit source code or logs.
