import streamlit as st
import requests
import pandas as pd
from urllib.parse import urljoin

st.set_page_config(
    page_title="PawnSecure Dashboard",
    page_icon="🔐",
    layout="wide",
)

DEFAULT_API_URL = "https://pawnsecure.onrender.com"

def get_api_base_url() -> str:
    try:
        return st.secrets.get("PAWNSECURE_API_URL", DEFAULT_API_URL).rstrip("/")
    except Exception:
        return DEFAULT_API_URL

API_BASE_URL = get_api_base_url()

st.title("🔐 PawnSecure Dashboard")
st.caption("Streamlit dashboard connected to your existing Java Spring Boot backend.")
st.info(
    "This is a deployment-ready starter dashboard. It does not modify your Java backend "
    "or connect directly to Neon. Business screens must be mapped to your existing API endpoints."
)

with st.sidebar:
    st.header("Configuration")
    st.text_input("Backend URL", value=API_BASE_URL, disabled=True)
    st.caption("Configure PAWNSECURE_API_URL in Streamlit app Secrets to change this value.")
    st.divider()
    st.write("**Current architecture**")
    st.write("React frontend: Netlify")
    st.write("Java backend: Render")
    st.write("Database: Neon PostgreSQL")
    st.write("Dashboard: Streamlit")

tab_overview, tab_api, tab_setup = st.tabs(
    ["Overview", "API Connection", "Setup Guide"]
)

with tab_overview:
    st.subheader("Admin overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Backend", "Configured")
    col2.metric("Database", "Through Java API")
    col3.metric("Dashboard", "Starter")

    st.markdown("### Planned modules")
    st.dataframe(
        pd.DataFrame(
            [
                {"Module": "Dealer management", "Status": "Needs API mapping"},
                {"Module": "Customer management", "Status": "Needs API mapping"},
                {"Module": "Girvi / pawn transactions", "Status": "Needs API mapping"},
                {"Module": "Fraud reviews", "Status": "Needs API mapping"},
                {"Module": "Subscriptions", "Status": "Needs API mapping"},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.warning(
        "No customer, Aadhaar, transaction, or fraud data is shown until the exact "
        "secured API endpoints and authentication flow are configured."
    )

with tab_api:
    st.subheader("Check backend connectivity")
    st.write(
        "The default test calls `/actuator/health`. This endpoint works only if Spring Boot "
        "Actuator is installed and the health endpoint is exposed."
    )
    health_path = st.text_input("Health endpoint path", value="/actuator/health")
    if st.button("Check backend", type="primary"):
        url = f"{API_BASE_URL}{'/' if not health_path.startswith('/') else ''}{health_path.lstrip('/')}"
        try:
            response = requests.get(url, timeout=20)
            st.write("Requested endpoint:", url)
            st.write("HTTP status:", response.status_code)
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text[:2000] or "(empty response)")
            if response.ok:
                st.success("The endpoint responded successfully.")
            else:
                st.warning(
                    "The server responded, but this endpoint returned a non-success status. "
                    "If Actuator is not enabled, test an existing health endpoint instead."
                )
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
            st.caption(
                "Check that the Render service is running, the URL is correct, and the "
                "chosen endpoint is reachable."
            )

with tab_setup:
    st.subheader("Deploy this dashboard")
    st.markdown(
        """
1. Extract this ZIP file.
2. Create a new GitHub repository named `pawnsecure-streamlit`.
3. Upload `app.py`, `requirements.txt`, `README.md`, `.gitignore`, and `.streamlit/config.toml`.
4. Open [Streamlit Community Cloud](https://share.streamlit.io/) and create an app from that repository.
5. Set the app file path to `app.py`.
6. In the app's **Settings → Secrets**, add:

```toml
PAWNSECURE_API_URL = "https://pawnsecure.onrender.com"
```

7. Deploy and open the **API Connection** tab to test the backend.
        """
    )
    st.markdown(
        "Official guide: [Deploy a Streamlit app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)"
    )

st.divider()
st.caption("PawnSecure • Starter dashboard • Keep credentials and personal data out of source control.")
