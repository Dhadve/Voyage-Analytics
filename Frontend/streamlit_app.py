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

BACKEND_URL = "https://voyage-analytics-r34b.onrender.com"  # your backend

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= LOAD FEATURE NAMES =================
@st.cache_resource
def load_feature_names():
    path = os.path.join(BASE_DIR, "feature_names.pkl")
    return joblib.load(path)

feature_names = load_feature_names()

# ================= SESSION STATE =================
if "history" not in st.session_state:
    st.session_state.history = []

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

    # 🔑 Extract categories dynamically from feature names
    from_options = sorted(
        [c.replace("from_", "") for c in feature_names if c.startswith("from_")]
    )
    to_options = sorted(
        [c.replace("to_", "") for c in feature_names if c.startswith("to_")]
    )
    agency_options = sorted(
        [c.replace("agency_", "") for c in feature_names if c.startswith("agency_")]
    )
    flight_type_options = sorted(
        [c.replace("flightType_", "") for c in feature_names if c.startswith("flightType_")]
    )

    with col1:
        from_city = st.selectbox("From", from_options)
        distance = st.number_input("Distance (km)", min_value=100, value=800)

    with col2:
        to_city = st.selectbox("To", to_options)
        day = st.number_input("Day of Month", min_value=1, max_value=31, value=10)

    with col3:
        agency = st.selectbox("Agency", agency_options)
        flight_type = st.selectbox("Flight Type", flight_type_options)

    submit_flight = st.button("🔍 Predict Flight Price")

    if submit_flight:
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

            st.success(f"💰 Predicted Price: ₹ {price}")

            # Save history
            st.session_state.history.append({
                "from": from_city,
                "to": to_city,
                "price": price
            })

            # 📈 Price Trend Chart
            trend_df = pd.DataFrame({
                "Day": list(range(1, 31)),
                "Estimated Price": [
                    price * (0.9 + d * 0.004) for d in range(30)
                ]
            })

            chart = alt.Chart(trend_df).mark_line(point=True).encode(
                x="Day",
                y="Estimated Price"
            ).properties(title="📈 Estimated Monthly Price Trend")

            st.altair_chart(chart, use_container_width=True)

        else:
            st.error(res.json())

# =====================================================
# ================= HOTEL TAB =========================
# =====================================================
with tab2:
    st.subheader("Hotel Recommendation")

    col1, col2, col3 = st.columns(3)

    with col1:
        place = st.text_input("Destination City (e.g. Florianopolis (SC))")

    with col2:
        days = st.number_input("Number of Days", min_value=1, value=2)

    with col3:
        max_total = st.number_input("Max Total Budget", value=20000)

    submit_hotel = st.button("🏨 Recommend Hotels")

    if submit_hotel:
        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code == 200:
            hotels = res.json()["recommended_hotels"]
            df = pd.DataFrame(hotels)

            st.success("🏨 Recommended Hotels")

            if "price" in df.columns:
                df["total_cost"] = df["price"] * df["days"]

            # 💼 Combined Cost View
            if st.session_state.history:
                last_flight_price = st.session_state.history[-1]["price"]
                df["flight_price"] = last_flight_price
                df["trip_total"] = df["total"] + df["flight_price"]

            st.dataframe(df, use_container_width=True)

        else:
            st.error(res.json())

# =====================================================
# ================= SIDEBAR HISTORY ===================
# =====================================================
st.sidebar.title("👤 User History")

if st.session_state.history:
    for h in st.session_state.history[::-1][:5]:
        st.sidebar.write(
            f"{h['from']} ➜ {h['to']} : ₹ {h['price']}"
        )
else:
    st.sidebar.info("No searches yet")

