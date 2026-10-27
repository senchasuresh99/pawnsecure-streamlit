import requests
import pandas as pd
import streamlit as st
from html import escape

st.set_page_config(page_title="PawnSecure", page_icon="🔐", layout="wide", initial_sidebar_state="collapsed")
DEFAULT_API = "https://pawnsecure.onrender.com"
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --purple:#7028e4; --purple2:#4f46e5; --ink:#182033; --muted:#778094; --line:#ececf4; }
html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
.stApp { background: #f5f6fb; color: var(--ink); }
.block-container { max-width: 1180px; padding-top: 1.3rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
.hero {
  background: linear-gradient(125deg,#6d28d9 0%,#5b35db 55%,#4338ca 100%);
  padding: 28px 30px; border-radius: 26px; color: white; margin-bottom: 22px;
  box-shadow: 0 14px 35px rgba(91,53,219,.18);
}
.brand-row { display:flex; align-items:center; gap:14px; }
.brand-mark { width:52px; height:52px; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.25); border-radius:16px; font-size:27px; }
.brand-name { font-size:25px; font-weight:800; letter-spacing:-.5px; line-height:1.1; }
.brand-sub { font-size:13px; color:rgba(255,255,255,.8); margin-top:5px; }
.hero-title { font-size:clamp(25px,3.5vw,36px); font-weight:800; margin:25px 0 5px; letter-spacing:-.8px; }
.hero-desc { color:rgba(255,255,255,.82); font-size:14px; }
.section-title { font-size:21px; font-weight:750; margin: 24px 0 13px; letter-spacing:-.4px; }
.metric-card { background:white; border:1px solid #eeeef5; border-radius:20px; padding:19px; min-height:118px; box-shadow:0 4px 14px rgba(20,25,50,.035); }
.metric-top { color:#737c8e; font-size:13px; font-weight:600; display:flex; align-items:center; gap:9px; }
.metric-icon { width:36px; height:36px; border-radius:12px; display:inline-flex; align-items:center; justify-content:center; font-size:17px; }
.metric-value { font-size:28px; font-weight:800; color:#151b2a; margin-top:12px; letter-spacing:-.7px; }
.metric-note { font-size:12px; color:#9299a8; margin-top:2px; }
.dealer-card { background:#fff; border:1px solid #ececf4; border-radius:20px; padding:19px; margin: 10px 0; box-shadow:0 4px 14px rgba(20,25,50,.035); }
.dealer-title { font-size:17px; font-weight:750; color:#1a2233; padding-right:8px; }
.dealer-meta { color:#747d90; font-size:13px; margin-top:8px; overflow-wrap:anywhere; }
.badge { display:inline-block; padding:6px 11px; border-radius:999px; font-size:11px; font-weight:750; letter-spacing:.25px; }
.badge-green { background:#dcfce7; color:#15803d; }
.badge-orange { background:#fff0d9; color:#b45309; }
.badge-purple { background:#f0e7ff; color:#6d28d9; }
.login-shell { max-width:520px; margin: 4vh auto 0; }
.login-panel { background:white; border:1px solid #ececf4; border-radius:24px; padding:26px; box-shadow:0 12px 35px rgba(20,25,50,.06); }
.small-muted { color:#81899a; font-size:13px; }
div.stButton > button { border-radius:13px; min-height:44px; font-weight:650; border:1px solid #e4e4ef; }
div.stButton > button[kind="primary"] { background:linear-gradient(100deg,#7c3aed,#5b35db); border:0; color:white; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] { border-radius:12px; }
div[data-testid="stDataFrame"] { border:1px solid #e9e9f2; border-radius:14px; overflow:hidden; }
hr { border-color:#e7e8f0; }
@media (max-width: 640px) {
 .block-container { padding: .8rem .8rem 2rem; }
 .hero { padding:22px 19px; border-radius:21px; }
 .brand-name { font-size:22px; }
 .metric-card { padding:14px; min-height:105px; border-radius:16px; }
 .metric-value { font-size:24px; }
 .dealer-card { padding:15px; border-radius:17px; }
 .login-panel { padding:20px; }
}
</style>
""", unsafe_allow_html=True)

if "auth" not in st.session_state: st.session_state.auth = None
if "api_base" not in st.session_state: st.session_state.api_base = DEFAULT_API

def api_request(method, path, *, token=None, dealer_id=None, params=None, body=None, timeout=20):
    headers = {"Accept":"application/json"}
    if token: headers["Authorization"] = "Bearer " + token
    if dealer_id is not None: headers["X-DEALER-ID"] = str(dealer_id)
    try:
        r = requests.request(method, st.session_state.api_base.rstrip("/") + path,
                             headers=headers, params=params, json=body, timeout=timeout)
        if not r.ok: return None, f"HTTP {r.status_code}: {(r.text or r.reason)[:350]}"
        if not r.content: return {}, None
        try: return r.json(), None
        except ValueError: return r.text, None
    except requests.RequestException as e:
        return None, f"API connection failed: {e}"

def hero(title, subtitle, role="Trusted Records"):
    st.markdown(f"""
    <div class="hero">
      <div class="brand-row"><div class="brand-mark">🔐</div>
        <div><div class="brand-name">PawnSecure</div><div class="brand-sub">{escape(role)}</div></div>
      </div>
      <div class="hero-title">{escape(title)}</div>
      <div class="hero-desc">{escape(subtitle)}</div>
    </div>""", unsafe_allow_html=True)

def metric_card(label, value, icon, tone, note="Live data from your backend"):
    colors = {"purple":("#f0e7ff","#7c3aed"), "blue":("#e2edff","#2563eb"),
              "green":("#dcfce7","#16a34a"), "orange":("#ffedd5","#ea580c"),
              "red":("#fee2e2","#dc2626"), "teal":("#ccfbf1","#0f9f91")}
    bg, fg = colors.get(tone, colors["purple"])
    st.markdown(f"""<div class="metric-card">
      <div class="metric-top"><span class="metric-icon" style="background:{bg};color:{fg}">{icon}</span>{escape(str(label))}</div>
      <div class="metric-value">{escape(str(value))}</div><div class="metric-note">{escape(note)}</div>
    </div>""", unsafe_allow_html=True)

def dealer_cards(rows):
    if not rows:
        st.info("No dealer records were returned by the API.")
        return
    for d in rows:
        if not isinstance(d, dict):
            continue
        name = d.get("name") or d.get("dealerName") or d.get("shopName") or "Dealer"
        did = d.get("id", d.get("dealerId", "—"))
        gst = d.get("gstNumber") or d.get("gst") or d.get("gstin") or "Not provided"
        phone = d.get("phone") or d.get("phoneNumber") or d.get("mobile") or "Not provided"
        email = d.get("email") or "Not provided"
        status = str(d.get("status") or d.get("approvalStatus") or ("Approved" if d.get("approved") is True else "Dealer")).upper()
        is_pending = "PENDING" in status or "REJECT" in status
        badge = "badge-orange" if is_pending else "badge-green"
        label = "PENDING" if "PENDING" in status else ("REJECTED" if "REJECT" in status else ("APPROVED" if ("APPROV" in status or d.get("approved") is True) else escape(status.title())))
        st.markdown(f"""<div class="dealer-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap">
            <div class="dealer-title">🏪 {escape(str(name))}</div><span class="badge {badge}">● {label}</span>
          </div>
          <div class="dealer-meta">Dealer ID: {escape(str(did))} &nbsp;·&nbsp; GST: {escape(str(gst))}</div>
          <div class="dealer-meta">☎ {escape(str(phone))} &nbsp;·&nbsp; ✉ {escape(str(email))}</div>
        </div>""", unsafe_allow_html=True)

def show_data(data, label):
    if data is None:
        st.info(f"No {label} data loaded yet.")
    elif isinstance(data, list):
        if data:
            st.dataframe(pd.json_normalize(data), use_container_width=True, hide_index=True)
        else: st.info(f"No {label} records found.")
    elif isinstance(data, dict):
        numeric = [(k,v) for k,v in data.items() if isinstance(v,(int,float)) and not isinstance(v,bool)]
        if numeric:
            cols = st.columns(min(3,len(numeric)))
            for i,(k,v) in enumerate(numeric[:3]): cols[i].metric(k.replace("_"," ").title(),v)
        with st.expander("View API response details"): st.json(data)
    else: st.write(data)

# Header and sign-in
if not st.session_state.auth:
    hero("Your business. Your records. Your trust.", "A secure analytics space for PawnSecure dealers and administrators.", "Admin & Dealer Portal")
    st.markdown('<div class="login-shell"><div class="section-title">Welcome back 👋</div><p class="small-muted">Sign in with your existing PawnSecure account.</p></div>', unsafe_allow_html=True)
    with st.container(border=True):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.caption("🔒 Authentication is handled by your existing Spring Boot backend.")
        if st.button("Sign in securely  →", type="primary", use_container_width=True):
            if not email.strip() or not password:
                st.error("Please enter both your email and password.")
            else:
                result, err = api_request("POST", PATHS["login"], body={"email":email.strip(),"password":password})
                if err: st.error(err)
                elif not isinstance(result,dict) or not result.get("token"):
                    st.error("The login response did not contain a token. Check the backend response.")
                    st.json(result)
                else:
                    st.session_state.auth = result
                    st.rerun()
    with st.expander("Connection settings"):
        st.session_state.api_base = st.text_input("Backend API URL", st.session_state.api_base).strip().rstrip("/")
    st.markdown('<p class="small-muted" style="text-align:center;margin-top:28px">PawnSecure · Connecting Trust. Securing Value.</p>', unsafe_allow_html=True)
    st.stop()

auth = st.session_state.auth
token = auth.get("token")
role = str(auth.get("role","")).upper().replace("ROLE_","")
dealer_id = auth.get("id", auth.get("dealerId"))
name = auth.get("name") or auth.get("dealerName") or "User"

with st.sidebar:
    st.markdown("## 🔐 PawnSecure")
    st.caption("Business analytics")
    st.session_state.api_base = st.text_input("Backend API URL", st.session_state.api_base).strip().rstrip("/")
    st.divider()
    st.markdown(f"**{name}**")
    st.caption(f"{role.title()} account")
    if st.button("Log out", use_container_width=True):
        st.session_state.auth = None
        st.session_state.pop("admin_dealers",None)
        st.session_state.pop("admin_pending",None)
        st.session_state.pop("dealer_results",None)
        st.rerun()

if role == "ADMIN":
    hero("Admin Dashboard", f"Welcome back, {name}. Manage dealer visibility and review account records.", "Admin Portal")
    dealers_data = st.session_state.get("admin_dealers")
    pending_data = st.session_state.get("admin_pending")
    if st.button("↻  Refresh dashboard data", type="primary", use_container_width=True):
        data, err = api_request("GET",PATHS["admin_dealers"],token=token)
        st.session_state.admin_dealers = (data,err)
        data2, err2 = api_request("GET",PATHS["admin_pending"],token=token)
        st.session_state.admin_pending = (data2,err2)
        st.rerun()
    dealers_data = st.session_state.get("admin_dealers")
    pending_data = st.session_state.get("admin_pending")
    dealers = dealers_data[0] if dealers_data and not dealers_data[1] and isinstance(dealers_data[0],list) else []
    pending = pending_data[0] if pending_data and not pending_data[1] and isinstance(pending_data[0],list) else []
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    metrics = [("Total dealers",len(dealers),"🏪","purple"),("Approved",max(0,len(dealers)-len(pending)),"✓","green"),("Pending review",len(pending),"◷","orange"),("Portal status","Live","●","blue")]
    for col, (label,value,icon,tone) in zip(cols,metrics):
        with col: metric_card(label,value,icon,tone,"From dealer API" if label!="Portal status" else "Connected dashboard")
    st.markdown('<div class="section-title">Dealer management</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["All dealers", "Pending approvals"])
    with tab1:
        if dealers_data is None:
            st.info("Tap Refresh dashboard data to load dealers from your backend.")
        elif dealers_data[1]: st.error(dealers_data[1])
        else: dealer_cards(dealers)
    with tab2:
        if pending_data is None: st.info("Tap Refresh dashboard data to load pending dealers.")
        elif pending_data[1]: st.error(pending_data[1])
        else: dealer_cards(pending)
    st.warning("Approval and subscription renewal are intentionally not enabled in this dashboard until the exact production request and confirmation flow are verified.")

elif role == "DEALER":
    hero(f"Good to see you, {name}", "Your Girvi activity and customer account overview.", "Dealer Portal")
    if dealer_id is None:
        st.error("Dealer ID was not returned by login, so APIs requiring X-DEALER-ID may not work.")
    if st.button("↻  Refresh my dashboard", type="primary", use_container_width=True):
        result = {}
        for key,path in [("stats",PATHS["dashboard_stats"]),("today",PATHS["today_summary"]),("due",PATHS["due_today"]),("overdue",PATHS["overdue"]),("customers",PATHS["customers"]),("girvi",PATHS["girvi"])]:
            params = {"page":0,"size":10} if key=="girvi" else None
            result[key] = api_request("GET",path,token=token,dealer_id=dealer_id,params=params)
        st.session_state.dealer_results = result
        st.rerun()
    results = st.session_state.get("dealer_results",{})
    stats, stat_err = results.get("stats",(None,None))
    st.markdown('<div class="section-title">Business snapshot</div>', unsafe_allow_html=True)
    if stat_err: st.error("Dashboard statistics: "+stat_err)
    elif isinstance(stats,dict):
        metric_fields = [
            ("Today's Girvi", "todayGirviAmount","₹","purple"),
            ("Active customers","activeCustomers","","blue"),
            ("Due today","dueTodayCount","","orange"),
            ("Overdue accounts","overdueCount","","red"),
            ("Closed today","todayClosedAmount","₹","green"),
            ("Interest collected","todayInterestPaid","₹","teal"),
        ]
        cols = st.columns(3)
        for i,(label,key,prefix,tone) in enumerate(metric_fields):
            if key in stats:
                with cols[i%3]: metric_card(label,f"{prefix}{stats[key]}","₹" if prefix=="₹" else "•",tone)
    else: st.info("Tap Refresh my dashboard to load live figures from your backend.")
    st.markdown('<div class="section-title">Account activity</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Today's Girvi","Due today","Overdue","Customers","Girvi records"])
    for tab,(key,label) in zip(tabs,[("today","Today's Girvi"),("due","Due today"),("overdue","Overdue accounts"),("customers","My customers"),("girvi","Girvi records")]):
        with tab:
            if key not in results: st.info("Refresh the dashboard to load this section.")
            else:
                data,err = results[key]
                if err: st.error(err)
                else: show_data(data,label)
else:
    hero("Account not recognized", "The backend did not return an expected role.", "Sign-in support")
    st.error(f"Received role: {role or 'empty'}. Expected ADMIN or DEALER.")
    if st.button("Sign out"): st.session_state.auth=None; st.rerun()

st.markdown("---")
st.markdown('<p class="small-muted" style="text-align:center">PawnSecure · Connecting Trust. Securing Value. &nbsp; | &nbsp; Data served by your existing Spring Boot API</p>', unsafe_allow_html=True)
