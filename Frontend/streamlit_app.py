import streamlit as st
import pandas as pd
import requests
import joblib
import os
import altair as alt
import random

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

if "from_city" not in st.session_state:
    st.session_state.from_city = None

if "to_city" not in st.session_state:
    st.session_state.to_city = None

# ================= UTIL =================
def estimate_distance(frm, to):
    if frm == to:
        return 0
    return random.randint(300, 3000)

# ================= UI HEADER =================
st.title("✈️ Voyage Analytics")
st.caption("Flight Price Prediction & Hotel Recommendation System")

tab1, tab2 = st.tabs(["✈️ Flight Price", "🏨 Hotel Recommender"])

# =====================================================
# ================= FLIGHT PRICE TAB ==================
# =====================================================
with tab1:
    st.subheader("Flight Price Prediction")

    # Extract dynamic categories
    from_options = sorted(c.replace("from_", "") for c in feature_names if c.startswith("from_"))
    to_options = sorted(c.replace("to_", "") for c in feature_names if c.startswith("to_"))
    agency_options = sorted(c.replace("agency_", "") for c in feature_names if c.startswith("agency_"))
    flight_type_options = sorted(c.replace("flightType_", "") for c in feature_names if c.startswith("flightType_"))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.from_city = st.selectbox(
            "From",
            from_options,
            index=0 if st.session_state.from_city is None else from_options.index(st.session_state.from_city)
        )

    # 🚫 Remove From city from To list
    filtered_to_options = [c for c in to_options if c != st.session_state.from_city]

    with col2:
        st.session_state.to_city = st.selectbox(
            "To",
            filtered_to_options,
            index=0 if st.session_state.to_city not in filtered_to_options else filtered_to_options.index(st.session_state.to_city)
        )

    with col3:
        agency = st.selectbox("Agency", agency_options)

    col4, col5, col6 = st.columns(3)

    with col4:
        flight_type = st.selectbox("Flight Type", flight_type_options)

    with col5:
        day = st.slider("Day of Month", 1, 31, 10)

    with col6:
        st.markdown("###")
        if st.button("🔁 Swap From ↔ To"):
            st.session_state.from_city, st.session_state.to_city = (
                st.session_state.to_city,
                st.session_state.from_city
            )
            st.rerun()


    distance = estimate_distance(st.session_state.from_city, st.session_state.to_city)
    st.info(f"📏 Estimated Distance: **{distance} km**")

    submit_flight = st.button("🔍 Predict Flight Price")

    if submit_flight:
        if st.session_state.from_city == st.session_state.to_city:
            st.error("❌ From and To cities cannot be the same.")
            st.stop()

        payload = {
            "from": st.session_state.from_city,
            "to": st.session_state.to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day
        }

        res = requests.post(f"{BACKEND_URL}/predict-flight", json=payload)

        if res.status_code != 200:
            st.error(res.text)
            st.stop()

        price = res.json()["predicted_price"]
        st.success(f"💰 Predicted Flight Price: ₹ {price}")

        st.session_state.history.append({
            "from": st.session_state.from_city,
            "to": st.session_state.to_city,
            "price": price
        })

        # Price trend
        trend_df = pd.DataFrame({
            "Day": range(1, 31),
            "Estimated Price": [price * (0.95 + d * 0.003) for d in range(30)]
        })

        chart = alt.Chart(trend_df).mark_line(point=True).encode(
            x="Day",
            y="Estimated Price"
        ).properties(title="📈 Estimated Monthly Price Trend")

        st.altair_chart(chart, use_container_width=True)

# =====================================================
# ================= HOTEL TAB =========================
# =====================================================
with tab2:
    st.subheader("Hotel Recommendation")

    # 🔥 AUTO-FILL from flight To city
    place = st.session_state.to_city

    col1, col2, col3 = st.columns(3)

    with col1:
        st.text_input("Destination City", value=place, disabled=True)

    with col2:
        days = st.number_input("Number of Days", min_value=1, value=2)

    with col3:
        max_total = st.number_input("Max Hotel Budget", value=20000)

    submit_hotel = st.button("🏨 Recommend Hotels")

    if submit_hotel:
        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code != 200:
            st.error(res.text)
            st.stop()

        data = res.json()
        hotels = data.get("recommended_hotels", [])

        if not hotels:
            st.warning("No hotels found for selected criteria.")
            st.stop()

        df = pd.DataFrame(hotels)

        st.success("🏨 Recommended Hotels")
        st.dataframe(df, use_container_width=True)

        # 💼 Combined cost
        if st.session_state.history:
            flight_price = st.session_state.history[-1]["price"]
            df["flight_price"] = flight_price
            df["trip_total"] = df["total"] + flight_price

            st.subheader("💼 Total Trip Cost (Flight + Hotel)")
            st.dataframe(df[["name", "total", "flight_price", "trip_total"]])

# =====================================================
# ================= SIDEBAR ===========================
# =====================================================
st.sidebar.title("👤 User History")

if st.session_state.history:
    for h in st.session_state.history[::-1][:5]:
        st.sidebar.write(f"{h['from']} ➜ {h['to']} : ₹ {h['price']}")
else:
    st.sidebar.write("No searches yet.")



