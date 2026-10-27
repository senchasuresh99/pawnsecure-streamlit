import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="PawnSecure | Admin Console", page_icon="🔐", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --purple:#5b2be0; --ink:#18233b; --muted:#718096; }
.block-container {padding-top:1.2rem; padding-bottom:2rem; max-width:1500px;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#fbfaff 0%,#f4f0ff 100%); border-right:1px solid #ebe6fa;}
.hero {background:linear-gradient(110deg,#4c1dce 0%,#7139ec 55%,#4d49e8 100%); color:white; padding:28px 30px; border-radius:20px; margin-bottom:18px; box-shadow:0 10px 30px #4f2bd51c;}
.hero h1 {font-size:2rem; margin:0 0 8px 0; color:white;}
.hero p {margin:0; color:#eee8ff;}
.metric-card {background:#fff; border:1px solid #e9eaf3; border-radius:16px; padding:18px 18px 15px 18px; min-height:120px; box-shadow:0 3px 12px #1a24500a;}
.metric-label {color:#69758c; font-size:.92rem; margin-bottom:8px;}
.metric-value {font-size:2rem; font-weight:750; color:#18233b; line-height:1.1;}
.metric-icon {font-size:1.25rem; float:right; background:#f1eaff; padding:8px 10px; border-radius:12px;}
.section-title {font-size:1.25rem; font-weight:750; color:#18233b; margin:1.2rem 0 .7rem 0;}
div[data-testid="stButton"] button {border-radius:10px; font-weight:600;}
.status-approved {background:#e0f9eb;color:#087443;border-radius:20px;padding:5px 10px;font-weight:700;font-size:.82rem;}
.small-muted {color:#718096;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

DEFAULT_API = "https://pawnsecure.onrender.com"
if "api_base" not in st.session_state: st.session_state.api_base = DEFAULT_API
if "token" not in st.session_state: st.session_state.token = ""
if "dealer_id" not in st.session_state: st.session_state.dealer_id = ""
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "role" not in st.session_state: st.session_state.role = ""
if "dashboard_data" not in st.session_state: st.session_state.dashboard_data = {}

def api_call(method, path, *, json_data=None, params=None, needs_dealer=True, timeout=25):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    if needs_dealer and st.session_state.dealer_id:
        headers["X-DEALER-ID"] = str(st.session_state.dealer_id)
    url = st.session_state.api_base.rstrip("/") + path
    try:
        r = requests.request(method, url, headers=headers, json=json_data, params=params, timeout=timeout)
        try: payload = r.json()
        except Exception: payload = r.text
        return r.status_code, payload
    except requests.RequestException as e:
        return 0, str(e)

def as_list(payload):
    if isinstance(payload, list): return payload
    if isinstance(payload, dict):
        for key in ("content","data","dealers","items","results"):
            if isinstance(payload.get(key), list): return payload[key]
    return []

def first_value(obj, *keys, default="—"):
    if not isinstance(obj, dict): return default
    for k in keys:
        v=obj.get(k)
        if v is not None and v!="": return v
    return default

def show_metric(col, icon, label, value, note="Live API data"):
    with col:
        st.markdown(f'<div class="metric-card"><span class="metric-icon">{icon}</span><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="small-muted">{note}</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔐 PawnSecure")
    st.caption("Trusted Pawnbroking Platform")
    st.divider()
    page = st.radio("WORKSPACE", ["Overview", "Dealer Management", "Dealer Dashboard", "API & Settings"], label_visibility="visible")
    st.divider()
    st.markdown("**Connection**")
    st.caption("Spring Boot API")
    st.code(st.session_state.api_base, language=None)
    if st.session_state.token:
        st.success(f"Signed in · {st.session_state.role or 'User'}")
        if st.button("Sign out", use_container_width=True):
            for k in ["token","dealer_id","user_name","role","dashboard_data"]:
                st.session_state[k] = "" if k != "dashboard_data" else {}
            st.rerun()
    else:
        st.info("Sign in to load protected data")

st.markdown(f"""<div class="hero"><h1>Welcome back{', ' + st.session_state.user_name if st.session_state.user_name else ''} 👋</h1><p>Manage dealers, subscriptions and Girvi activity from one secure workspace.</p><p style="margin-top:12px;font-size:.9rem">PawnSecure Admin Console · {date.today().strftime('%d %B %Y')}</p></div>""", unsafe_allow_html=True)

if not st.session_state.token:
    st.markdown("### Sign in to PawnSecure")
    st.info("Use your existing Admin or Dealer account. Login is sent to your Spring Boot `/api/auth/login` endpoint.")
    with st.form("login_form"):
        c1,c2 = st.columns(2)
        with c1: email = st.text_input("Email")
        with c2: password = st.text_input("Password", type="password")
        login = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if login:
        if not email.strip() or not password:
            st.error("Enter your email and password.")
        else:
            code, data = api_call("POST","/api/auth/login",json_data={"email":email.strip(),"password":password},needs_dealer=False)
            if code == 200 and isinstance(data,dict) and data.get("token"):
                st.session_state.token = data["token"]
                st.session_state.dealer_id = data.get("id","")
                st.session_state.user_name = data.get("name",email.split("@")[0])
                st.session_state.role = str(data.get("role","")).replace("ROLE_","")
                st.success("Login successful.")
                st.rerun()
            else:
                st.error(f"Login failed ({code}): {data}")
    st.stop()

role = st.session_state.role.upper()
is_admin = "ADMIN" in role

if page == "API & Settings":
    st.markdown("### API connection")
    st.caption("This dashboard calls your existing Java backend; it does not connect directly to PostgreSQL.")
    with st.form("settings_form"):
        base = st.text_input("Spring Boot base URL", value=st.session_state.api_base)
        dealer_id = st.text_input("Dealer ID (used for X-DEALER-ID header)", value=str(st.session_state.dealer_id))
        save = st.form_submit_button("Save settings", type="primary")
    if save:
        st.session_state.api_base = base.strip().rstrip("/")
        st.session_state.dealer_id = dealer_id.strip()
        st.success("Settings saved for this session.")
    if st.button("Test login-protected API", use_container_width=True):
        endpoint = "/api/admin/dealers" if is_admin else "/api/dashboard/stats"
        code,data=api_call("GET",endpoint,needs_dealer=not is_admin)
        if code==200: st.success(f"API reachable ({code}).")
        else: st.warning(f"API returned {code}: {data}")
    st.warning("Never paste your JWT token into screenshots or share it publicly. Session values are held in Streamlit session state.")
    st.stop()

if page == "Overview":
    if is_admin:
        code, dealers_payload = api_call("GET","/api/admin/dealers",needs_dealer=False)
        dealers = as_list(dealers_payload) if code == 200 else []
        pcode, pending_payload = api_call("GET","/api/admin/pending",needs_dealer=False)
        pending = as_list(pending_payload) if pcode == 200 else []
        approved = [d for d in dealers if str(first_value(d,"approved","isApproved","status","dealerStatus",default="")).lower() in ("true","approved","active")]
        renewals = [d for d in dealers if "renew" in str(first_value(d,"subscriptionStatus","status",default="")).lower()]
        c1,c2,c3,c4=st.columns(4)
        show_metric(c1,"🏪","Total dealers",len(dealers) if code==200 else "—")
        show_metric(c2,"✅","Approved / active",len(approved) if code==200 else "—")
        show_metric(c3,"🕒","Pending approval",len(pending) if pcode==200 else "—")
        show_metric(c4,"🔄","Renewal status",len(renewals) if code==200 else "—")
        st.markdown('<div class="section-title">Recent dealer registrations</div>',unsafe_allow_html=True)
        if code==200 and dealers:
            rows=[]
            for d in dealers[:8]:
                rows.append({"Dealer":first_value(d,"name","shopName","businessName"),"Email":first_value(d,"email"),"Phone":first_value(d,"phone","phoneNumber"),"GST":first_value(d,"gstNumber","gst","licenseNumber"),"Status":first_value(d,"status","dealerStatus","approved","isApproved"),"Dashboard":first_value(d,"dashboardControl"),"ID":first_value(d,"id","dealerId")})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        elif code!=200:
            st.warning(f"Could not load dealer list (HTTP {code}). {dealers_payload}")
        else: st.info("The API returned no dealers.")
        st.caption("Metrics are calculated from the current API response. If your Dealer entity uses different status field names, those cards may need field mapping.")
    else:
        code, stats = api_call("GET","/api/dashboard/stats")
        tcode, today = api_call("GET","/api/girvi/today/summary")
        duecode, due = api_call("GET","/api/girvi/due-today/count")
        ocode, overdue = api_call("GET","/api/girvi/overdue/count")
        stats = stats if isinstance(stats,dict) else {}
        today = today if isinstance(today,dict) else {}
        c1,c2,c3,c4=st.columns(4)
        show_metric(c1,"💰","Today's Girvi",first_value(today,"totalAmount","amount","todayAmount",default="₹—"))
        show_metric(c2,"👥","Active customers",first_value(stats,"activeCustomers","totalCustomers","customerCount"))
        show_metric(c3,"📅","Due today",due if duecode==200 else "—")
        show_metric(c4,"⏰","Overdue accounts",overdue if ocode==200 else "—")
        st.markdown('<div class="section-title">Today’s activity</div>',unsafe_allow_html=True)
        if tcode==200: st.json(today,expanded=True)
        else: st.info(f"Today's summary endpoint returned {tcode}.")
        if code!=200: st.warning(f"Dashboard stats returned {code}: {stats}")
    st.stop()

if page == "Dealer Management":
    if not is_admin:
        st.error("Dealer management is available to Admin accounts only.")
        st.stop()
    tab1,tab2=st.tabs(["All dealers","Pending approvals"])
    with tab1:
        if st.button("Refresh all dealers",type="primary"):
            st.rerun()
        code,data=api_call("GET","/api/admin/dealers",needs_dealer=False)
        dealers=as_list(data)
        if code==200 and dealers:
            for d in dealers:
                did=first_value(d,"id","dealerId",default="")
                name=first_value(d,"name","shopName","businessName",default="Dealer")
                status=str(first_value(d,"status","dealerStatus","approved","isApproved",default="Unknown"))
                gst=first_value(d,"gstNumber","gst","licenseNumber")
                phone=first_value(d,"phone","phoneNumber")
                email=first_value(d,"email")
                dash=first_value(d,"dashboardControl")
                with st.container(border=True):
                    left, right=st.columns([4,1])
                    with left:
                        st.markdown(f"#### 🏪 {name}")
                        st.caption(f"GST: {gst}  ·  Phone: {phone}  ·  Email: {email}")
                        st.markdown(f"**Status:** `{status}`　 **Dashboard:** `{dash}`　 **Dealer ID:** `{did}`")
                    with right:
                        st.button("View details",key=f"view_{did}",disabled=True,use_container_width=True)
                        st.caption("Read-only card")
        elif code!=200: st.error(f"Dealer API failed ({code}): {data}")
        else: st.info("No dealer records returned.")
    with tab2:
        code,data=api_call("GET","/api/admin/pending",needs_dealer=False)
        pending=as_list(data)
        if code==200 and pending:
            st.write(f"**{len(pending)} dealer(s) awaiting approval**")
            for d in pending:
                did=first_value(d,"id","dealerId",default="")
                st.markdown(f"**{first_value(d,'name','shopName','businessName')}** · ID `{did}` · {first_value(d,'email')}")
                st.caption(f"GST: {first_value(d,'gstNumber','gst','licenseNumber')} · Phone: {first_value(d,'phone','phoneNumber')}")
                st.info("Approval changes account state. Use the existing React Admin Portal for approval until the exact dashboard-control request values are confirmed.")
                st.divider()
        elif code!=200: st.error(f"Pending dealer API failed ({code}): {data}")
        else: st.success("No pending dealers.")
    st.stop()

if page == "Dealer Dashboard":
    if is_admin:
        st.info("You are signed in as Admin. To see dealer metrics, sign in with an existing Dealer account and enter its dealer ID if needed.")
    code,stats=api_call("GET","/api/dashboard/stats")
    if code==200 and isinstance(stats,dict):
        st.markdown("### Dealer statistics")
        cols=st.columns(3)
        items=list(stats.items())
        for i,(k,v) in enumerate(items[:9]):
            show_metric(cols[i%3],"📊",str(k).replace("_"," ").title(),v)
        with st.expander("Raw API response"): st.json(stats)
    else:
        st.warning(f"Dashboard stats API returned {code}: {stats}")
    tabs=st.tabs(["Today's Girvi","Due today","Overdue"])
    for tab, path in zip(tabs,["/api/girvi/today","/api/girvi/due-today","/api/girvi/overdue"]):
        with tab:
            if st.button("Load records",key="load_"+path):
                c,d=api_call("GET",path)
                if c==200:
                    records=as_list(d)
                    if records: st.dataframe(pd.json_normalize(records),use_container_width=True,hide_index=True)
                    else: st.json(d)
                else: st.error(f"Request failed ({c}): {d}")
    st.stop()
