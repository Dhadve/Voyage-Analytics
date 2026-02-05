import streamlit as st
import pandas as pd
import joblib
import requests

# ================= CONFIG =================
BACKEND_URL = "https://voyage-analytics-r34b.onrender.com"

st.set_page_config(
    page_title="Voyage Analytics",
    page_icon="✈️",
    layout="wide"
)

# ================= LOAD FEATURE NAMES =================
@st.cache_resource
def load_feature_names():
    return joblib.load("feature_names.pkl")

feature_names = load_feature_names()

# ================= EXTRACT DROPDOWN VALUES =================
def extract_values(prefix):
    return sorted([
        col.replace(prefix, "")
        for col in feature_names
        if col.startswith(prefix)
    ])

FROM_CITIES = extract_values("from_")
TO_CITIES = extract_values("to_")
AGENCIES = extract_values("agency_")
FLIGHT_TYPES = extract_values("flightType_")

# ================= HEADER =================
st.markdown(
    """
    <h1 style='text-align:center;'>✈️ Voyage Analytics</h1>
    <p style='text-align:center;color:gray;'>
    Smart Flight Price Prediction & Hotel Recommendations
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# ================= TABS =================
tab1, tab2 = st.tabs(["✈️ Flight Price Predictor", "🏨 Hotel Recommender"])

# ================= FLIGHT TAB =================
with tab1:
    st.subheader("Flight Price Prediction")

    with st.form("flight_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            from_city = st.selectbox("From", FROM_CITIES)
            agency = st.selectbox("Agency", AGENCIES)

        with col2:
            to_city = st.selectbox("To", TO_CITIES)
            flight_type = st.selectbox("Flight Type", FLIGHT_TYPES)

        with col3:
            distance = st.number_input("Distance (km)", min_value=50, step=10)
            day = st.slider("Day of Month", 1, 31, 15)

        submit_flight = st.form_submit_button("🔍 Predict Price")

    if submit_flight:
        payload = {
            "from": from_city,
            "to": to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day
        }

        with st.spinner("Predicting flight price..."):
            res = requests.post(
                f"{BACKEND_URL}/predict-flight",
                json=payload
            )

        if res.status_code == 200:
            price = res.json()["predicted_price"]
            st.success(f"💰 **Predicted Price:** ₹ {price}")
        else:
            st.error(res.json().get("error", "Prediction failed"))

# ================= HOTEL TAB =================
with tab2:
    st.subheader("Hotel Recommendation")

    with st.form("hotel_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            place = st.selectbox("Destination City", TO_CITIES)

        with col2:
            days = st.number_input("Number of Days", min_value=1, max_value=30, value=3)

        with col3:
            max_total = st.number_input("Max Total Budget (₹)", min_value=1000, step=500)

        submit_hotel = st.form_submit_button("🏨 Recommend Hotels")

    if submit_hotel:
        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        with st.spinner("Finding best hotels..."):
            res = requests.post(
                f"{BACKEND_URL}/recommend-hotels",
                json=payload
            )

        if res.status_code == 200:
            hotels = res.json()["recommended_hotels"]

            if hotels:
                df = pd.DataFrame(hotels)
                st.dataframe(
                    df[["name", "price", "days", "total"]],
                    use_container_width=True
                )
            else:
                st.warning("No hotels found within budget.")
        else:
            st.error(res.json().get("error", "Hotel recommendation failed"))

