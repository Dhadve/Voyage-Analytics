import streamlit as st
import pandas as pd
import requests
import joblib
import os
import altair as alt

# ================= CONFIG =================
st.set_page_config(
    page_title="Voyage Analytics",
    page_icon="✈️",
    layout="wide"
)

BACKEND_URL = "https://voyage-analytics-r34b.onrender.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= LOAD FEATURE NAMES =================
@st.cache_resource
def load_feature_names():
    return joblib.load(os.path.join(BASE_DIR, "feature_names.pkl"))

feature_names = load_feature_names()

# ================= SESSION STATE =================
if "history" not in st.session_state:
    st.session_state.history = []

# ================= DISTANCE AUTO MAPPING =================
def auto_distance(frm, to):
    # No hardcoding cities → generic fallback logic
    if frm == to:
        return 300
    return abs(hash(frm) - hash(to)) % 2000 + 300  # realistic random distance

# ================= UI HEADER =================
st.title("✈️ Voyage Analytics")
st.caption("Flight Price Prediction & Hotel Recommendation System")

tab1, tab2 = st.tabs(["✈️ Flight Price", "🏨 Hotel Recommender"])

# =====================================================
# ================= FLIGHT PRICE TAB ==================
# =====================================================
with tab1:
    st.subheader("Flight Price Prediction")

    col1, col2, col3 = st.columns(3)

    # Dynamic options from feature_names.pkl
    from_options = sorted(c.replace("from_", "") for c in feature_names if c.startswith("from_"))
    to_options = sorted(c.replace("to_", "") for c in feature_names if c.startswith("to_"))
    agency_options = sorted(c.replace("agency_", "") for c in feature_names if c.startswith("agency_"))
    flight_type_options = sorted(c.replace("flightType_", "") for c in feature_names if c.startswith("flightType_"))

    with col1:
        from_city = st.selectbox("From", from_options)

    with col2:
        to_city = st.selectbox("To", to_options)

    with col3:
        agency = st.selectbox("Agency", agency_options)

    flight_type = st.selectbox("Flight Type", flight_type_options)
    day = st.slider("Day of Month", 1, 31, 10)

    distance = auto_distance(from_city, to_city)
    st.info(f"📏 Estimated Distance: **{distance} km**")

    if st.button("🔍 Predict Flight Price"):
        payload = {
            "from": from_city,
            "to": to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day
        }

        res = requests.post(f"{BACKEND_URL}/predict-flight", json=payload)

        if res.status_code != 200:
            st.error(res.text)
        else:
            price = res.json()["predicted_price"]
            st.success(f"💰 Predicted Flight Price: ₹ {price}")

            st.session_state.history.append({
                "from": from_city,
                "to": to_city,
                "price": price
            })

            # 📈 Trend chart
            trend_df = pd.DataFrame({
                "Day": list(range(1, 31)),
                "Estimated Price": [price * (0.95 + d * 0.003) for d in range(30)]
            })

            chart = alt.Chart(trend_df).mark_line(point=True).encode(
                x="Day",
                y="Estimated Price"
            ).properties(title="📈 Monthly Price Trend")

            st.altair_chart(chart, use_container_width=True)

# =====================================================
# ================= HOTEL TAB =========================
# =====================================================
with tab2:
    st.subheader("Hotel Recommendation")

    col1, col2, col3 = st.columns(3)

    with col1:
        place = st.text_input("Destination City", "Florianopolis (SC)")

    with col2:
        days = st.number_input("Days of Stay", min_value=1, value=2)

    with col3:
        max_total = st.number_input("Max Total Budget (₹)", value=20000)

    if st.button("🏨 Recommend Hotels"):
        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code != 200:
            st.error(res.text)
        else:
            data = res.json()

            if "recommended_hotels" not in data:
                st.error(data.get("error", "Unknown hotel API error"))
            else:
                df = pd.DataFrame(data["recommended_hotels"])

                if df.empty:
                    st.warning("No hotels found.")
                else:
                    st.success("🏨 Recommended Hotels")

                    if "price" in df.columns:
                        df["hotel_total"] = df["price"] * df["days"]

                    if st.session_state.history:
                        flight_price = st.session_state.history[-1]["price"]
                        df["flight_price"] = flight_price
                        df["trip_total"] = df["total"] + flight_price

                    st.dataframe(df, use_container_width=True)

# =====================================================
# ================= SIDEBAR ===========================
# =====================================================
st.sidebar.title("👤 Recent Flights")

if st.session_state.history:
    for h in st.session_state.history[::-1][:5]:
        st.sidebar.write(f"{h['from']} ➜ {h['to']} | ₹ {h['price']}")
else:
    st.sidebar.info("No predictions yet.")



