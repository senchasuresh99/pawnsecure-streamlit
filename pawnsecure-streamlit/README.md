# PawnSecure Streamlit Admin + Dealer Dashboard

This dashboard uses the real route mappings found in the supplied `pawnsecure-main.zip` source code.

## Architecture
Streamlit → existing Spring Boot API (`https://pawnsecure.in`) → existing Neon PostgreSQL database.

It does not connect directly to PostgreSQL and does not modify the React website or Java backend.

## Included functionality
- Login via `POST /api/auth/login` and retain the returned JWT in the Streamlit session.
- Admin: load all dealers (`GET /api/**`) and pending dealers (`GET /api/**`).
- Dealer: load dashboard stats (`GET /api/**`), today's Girvi summary, due-today, overdue, customers and paginated Girvi records.
- Send `Authorization: Bearer <token>` for authenticated calls.
- Send `X-DEALER-ID` for endpoints requiring the dealer ID.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
1. Upload the contents of this folder to your GitHub repository.
2. Create an app on Streamlit Community Cloud, selecting `app.py`.
3. Deploy and sign in using an existing PawnSecure Admin or Dealer account.

The API base URL can be changed in the sidebar if needed.

## Known limitations / careful notes
- The dashboard is read-oriented. It intentionally does not trigger dealer approval or subscription renewal because approval requires a request DTO (`dashboardControl`) and these actions mutate production data.
- It counts records returned by the admin list endpoints; it does not assume the Dealer entity's exact status field names.
- Metal-rate admin controller currently has no active GET/POST mapping in the supplied source (its POST mapping is commented out), so metal rates are not presented as live here.
- Collection endpoints were not found in the supplied controller mappings, so no fake collection figures are shown. The stats DTO does include today's closed amount and today's interest paid.
- The login response role must be `ADMIN` or `DEALER`. If backend login returns a different role string, adjust role normalization after verifying the actual response.
- Confirm deployment API URL and test with authorized accounts before production use.
