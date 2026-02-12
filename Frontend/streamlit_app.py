import streamlit as st
import pandas as pd
import requests
import joblib
import os
import altair as alt

# ================= CONFIG =================
st.set_page_config(
    page_title="Voyage Analytics Pro",
    page_icon="✈️",
    layout="wide"
)

BACKEND_URL = "https://voyage-analytics-r34b.onrender.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DARK GLASSMORPHISM CSS =================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
.block-container {
    padding-top: 2rem;
}
.glass-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0 8px 32px 0 rgba(0,0,0,0.3);
    transition: 0.3s ease-in-out;
}
.glass-card:hover {
    transform: scale(1.02);
}
.metric-box {
    background: rgba(0,0,0,0.4);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN SYSTEM =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "history" not in st.session_state:
    st.session_state.history = []

def login_page():
    st.title("🔐 Login to Voyage Analytics")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Enter valid credentials")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= LOAD FEATURE NAMES =================
@st.cache_resource
def load_feature_names():
    return joblib.load(os.path.join(BASE_DIR, "feature_names.pkl"))

feature_names = load_feature_names()

# ================= HEADER =================
st.title("✈️ Voyage Analytics Pro")
st.caption(f"Welcome, {st.session_state.username}")

tab1, tab2 = st.tabs(["✈️ Flight Planning", "🏨 Hotel Planning"])

# ================= FLIGHT TAB =================
with tab1:
    from_options = sorted([c.replace("from_", "") for c in feature_names if c.startswith("from_")])
    to_options = sorted([c.replace("to_", "") for c in feature_names if c.startswith("to_")])
    agency_options = sorted([c.replace("agency_", "") for c in feature_names if c.startswith("agency_")])
    flight_type_options = sorted([c.replace("flightType_", "") for c in feature_names if c.startswith("flightType_")])

    col1, col2, col3 = st.columns(3)

    with col1:
        from_city = st.selectbox("From", from_options)

    with col2:
        to_options_filtered = [city for city in to_options if city != from_city]
        to_city = st.selectbox("To", to_options_filtered)

    with col3:
        if st.button("🔄 Swap Cities"):
            from_city, to_city = to_city, from_city

    day = st.slider("Travel Day", 1, 31, 10)
    agency = st.selectbox("Agency", agency_options)
    flight_type = st.selectbox("Flight Type", flight_type_options)
    distance = 1000  # simple default

    if st.button("💰 Predict Flight Price"):
        payload = {
            "from": from_city,
            "to": to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day
        }

        res = requests.post(f"{BACKEND_URL}/predict-flight", json=payload)

        if res.status_code == 200:
            price = res.json()["predicted_price"]

            st.session_state.flight_price = price
            st.session_state.destination = to_city

            st.markdown(f"""
            <div class="metric-box">
                <h2>Estimated Flight Price</h2>
                <h1>₹ {price}</h1>
            </div>
            """, unsafe_allow_html=True)

            st.session_state.history.append({
                "from": from_city,
                "to": to_city,
                "flight_price": price
            })

        else:
            st.error(res.json())

# ================= HOTEL TAB =================
with tab2:
    if "destination" in st.session_state:
        place = st.session_state.destination
        st.info(f"Hotel city auto-selected: {place}")
    else:
        place = st.text_input("Destination City")

    days = st.number_input("Stay Duration (Days)", 1, 30, 2)
    max_total = st.number_input("Total Budget", value=20000)

    if st.button("🏨 Find Hotels"):
        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code == 200:
            hotels = res.json()["recommended_hotels"]

            for hotel in hotels:
                flight_price = st.session_state.get("flight_price", 0)
                total_trip = hotel["calculated_total"] + flight_price

                budget_status = "✅ Within Budget"
                if total_trip > max_total:
                    budget_status = "❌ Over Budget"

                st.markdown(f"""
                <div class="glass-card">
                    <h3>{hotel['name']}</h3>
                    <p>Price per night: ₹ {hotel['price']}</p>
                    <p>Stay Cost: ₹ {hotel['calculated_total']}</p>
                    <p><b>Total Trip Cost: ₹ {total_trip}</b></p>
                    <p>{budget_status}</p>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.error(res.json())

# ================= SIDEBAR HISTORY =================
st.sidebar.title("📜 Booking History")

if st.session_state.history:
    for h in st.session_state.history[::-1]:
        st.sidebar.write(f"{h['from']} ➜ {h['to']} | ₹ {h['flight_price']}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.history = []
    st.rerun()

