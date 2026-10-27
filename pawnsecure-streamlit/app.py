import json
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PawnSecure Analytics", page_icon="🔐", layout="wide")
DEFAULT_API = "https://pawnsecure.onrender.com"

# API paths below were mapped from the supplied Spring Boot source archive.
PATHS = {
    "login": "/api/auth/login",
    "admin_dealers": "/api/admin/dealers",
    "admin_pending": "/api/admin/pending",
    "dashboard_stats": "/api/dashboard/stats",
    "girvi": "/api/girvi",
    "today_summary": "/api/girvi/today/summary",
    "due_today": "/api/girvi/due-today",
    "overdue": "/api/girvi/overdue",
    "customers": "/api/customers/yourCustomer",
}

if "auth" not in st.session_state:
    st.session_state.auth = None
if "api_base" not in st.session_state:
    st.session_state.api_base = DEFAULT_API

st.sidebar.title("PawnSecure")
st.sidebar.caption("Admin + Dealer Analytics")
st.session_state.api_base = st.sidebar.text_input("Backend API URL", st.session_state.api_base).strip().rstrip("/")
st.sidebar.caption("Streamlit → Spring Boot REST API → Neon PostgreSQL")


def request_api(method, path, *, token=None, dealer_id=None, params=None, body=None, timeout=20):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if dealer_id is not None:
        headers["X-DEALER-ID"] = str(dealer_id)
    url = st.session_state.api_base + path
    try:
        r = requests.request(method, url, headers=headers, params=params, json=body, timeout=timeout)
        if not r.ok:
            detail = r.text[:500] if r.text else r.reason
            return None, f"HTTP {r.status_code}: {detail}"
        if not r.content:
            return {}, None
        try:
            return r.json(), None
        except ValueError:
            return r.text, None
    except requests.RequestException as e:
        return None, f"API connection failed: {e}"


def show_data(data, label):
    if data is None:
        st.info(f"No {label} data loaded yet.")
    elif isinstance(data, list):
        if data:
            st.dataframe(pd.json_normalize(data), use_container_width=True, hide_index=True)
        else:
            st.info(f"The API returned no {label} records.")
    elif isinstance(data, dict):
        numeric = [(k, v) for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric:
            cols = st.columns(min(4, len(numeric)))
            for i, (k, v) in enumerate(numeric[:4]):
                cols[i].metric(k.replace('_', ' ').title(), v)
        st.json(data)
    else:
        st.write(data)


def get_auth():
    return st.session_state.auth or {}

st.title("🔐 PawnSecure Analytics")
st.caption("Separate dashboard for the existing PawnSecure backend. Your React website is not modified.")

if not st.session_state.auth:
    st.subheader("Sign in to PawnSecure")
    st.info("Use an existing Admin or Dealer account. Login is sent to your Spring Boot `/api/auth/login` endpoint.")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
    if submit:
        if not email.strip() or not password:
            st.error("Enter both email and password.")
        else:
            result, error = request_api("POST", PATHS["login"], body={"email": email.strip(), "password": password})
            if error:
                st.error(error)
            elif not isinstance(result, dict) or not result.get("token"):
                st.error("Login response did not include a JWT token. Check the backend response.")
                st.json(result)
            else:
                st.session_state.auth = result
                st.rerun()
    st.stop()

auth = get_auth()
token = auth.get("token")
role = str(auth.get("role", "")).upper().replace("ROLE_", "")
dealer_id = auth.get("id")
name = auth.get("name", "User")

with st.sidebar:
    st.success(f"Signed in: {name}")
    st.caption(f"Role: {role or 'not returned'} | ID: {dealer_id if dealer_id is not None else 'not returned'}")
    if st.button("Logout", use_container_width=True):
        st.session_state.auth = None
        st.rerun()

if role == "ADMIN":
    st.header("🛡️ Admin Dashboard")
    st.caption("Dealer management and subscription overview")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Refresh all dealers", use_container_width=True):
            data, err = request_api("GET", PATHS["admin_dealers"], token=token)
            st.session_state.admin_dealers = (data, err)
    with c2:
        if st.button("Refresh pending dealers", use_container_width=True):
            data, err = request_api("GET", PATHS["admin_pending"], token=token)
            st.session_state.admin_pending = (data, err)

    if "admin_dealers" in st.session_state:
        data, err = st.session_state.admin_dealers
        if err: st.error(err)
        else:
            dealers = data if isinstance(data, list) else []
            st.subheader("Dealer totals")
            # Dealer entity fields vary; count all returned rows without guessing statuses.
            st.metric("Total dealers returned by API", len(dealers))
            show_data(data, "dealers")
    if "admin_pending" in st.session_state:
        data, err = st.session_state.admin_pending
        st.subheader("Pending approvals")
        if err: st.error(err)
        else:
            pending = data if isinstance(data, list) else []
            st.metric("Pending dealers returned by API", len(pending))
            show_data(data, "pending dealers")

    st.warning("Dealer approval/renewal are state-changing operations. This read-only starter intentionally does not expose those buttons until the exact request DTO and confirmation flow are verified.")

elif role == "DEALER":
    st.header("🏪 Dealer Dashboard")
    st.caption(f"Welcome, {name} · Dealer ID {dealer_id}")
    if dealer_id is None:
        st.error("Login response did not include dealer ID; cannot call APIs that require X-DEALER-ID.")
    if st.button("Refresh dealer dashboard", type="primary", use_container_width=True):
        results = {}
        for key, path in [("stats", PATHS["dashboard_stats"]), ("today", PATHS["today_summary"]), ("due", PATHS["due_today"]), ("overdue", PATHS["overdue"]), ("customers", PATHS["customers"]), ("girvi", PATHS["girvi"])]:
            params = {"page": 0, "size": 10} if key == "girvi" else None
            results[key] = request_api("GET", path, token=token, dealer_id=dealer_id, params=params)
        st.session_state.dealer_results = results
    results = st.session_state.get("dealer_results", {})
    if results:
        stats, err = results.get("stats", (None, "No data"))
        st.subheader("Key metrics")
        if err:
            st.error("Dashboard stats: " + err)
        elif isinstance(stats, dict):
            metric_fields = [
                ("Today Girvi Amount", "todayGirviAmount", "₹"),
                ("Active Customers", "activeCustomers", ""),
                ("Due Today", "dueTodayCount", ""),
                ("Overdue Accounts", "overdueCount", ""),
                ("Closed Amount Today", "todayClosedAmount", "₹"),
                ("Interest Paid Today", "todayInterestPaid", "₹"),
            ]
            cols = st.columns(3)
            for i, (label, key, prefix) in enumerate(metric_fields):
                if key in stats:
                    cols[i % 3].metric(label, f"{prefix}{stats[key]}")
        else:
            show_data(stats, "dashboard statistics")
        labels = [("today", "Today's Girvi summary"), ("due", "Due today"), ("overdue", "Overdue accounts"), ("customers", "My customers"), ("girvi", "Girvi records")]
        for key, label in labels:
            st.subheader(label)
            data, err = results.get(key, (None, "No data"))
            if err: st.error(err)
            else: show_data(data, label)
    else:
        st.info("Click Refresh dealer dashboard to load data from your backend.")
else:
    st.error(f"The backend returned role '{role or 'empty'}'. Expected ADMIN or DEALER. No role-specific data was loaded.")

st.markdown("---")
st.caption("Security: API requests use the JWT from login. Dealer requests also include X-DEALER-ID. All authorization must remain enforced by Spring Boot.")
