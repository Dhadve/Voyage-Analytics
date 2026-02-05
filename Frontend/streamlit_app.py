import streamlit as st
import requests
import pandas as pd

# ================= CONFIG =================
API_BASE_URL = "https://voyage-analytics-r34b.onrender.com"  # 🔴 CHANGE THIS

st.set_page_config(
    page_title="Voyage Analytics",
    page_icon="✈️",
    layout="wide"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}
.block-container {
    padding-top: 2rem;
}
h1, h2, h3 {
    color: #0f172a;
}
.card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("<h1>✈️ Voyage Analytics</h1>", unsafe_allow_html=True)
st.caption("Flight Price Prediction & Hotel Recommendation System")

st.divider()

# ================= TABS =================
tab1, tab2 = st.tabs(["✈️ Flight Price Prediction", "🏨 Hotel Recommendation"])

# ================= FLIGHT PRICE =================
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Predict Flight Price")

    col1, col2 = st.columns(2)

    with col1:
        from_city = st.selectbox(
            "From",
            ["Brasilia (DF)", "Recife (PE)"]
        )

        to_city = st.selectbox(
            "To",
            ["Brasilia (DF)", "Recife (PE)"]
        )

        agency = st.selectbox(
            "Agency",
            ["CloudNine", "FlyingDrops", "Rainbow"]
        )

    with col2:
        flight_type = st.selectbox(
            "Flight Type",
            ["economy", "business", "firstClass", "premium"]
        )

        distance = st.number_input("Distance (km)", min_value=100, value=1000)
        day = st.slider("Day of Month", 1, 31, 15)

    if st.button("Predict Price 🚀"):
        payload = {
            "from": from_city,
            "to": to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day
        }

        try:
            res = requests.post(f"{API_BASE_URL}/predict-flight", json=payload)
            result = res.json()

            if "predicted_price" in result:
                st.success(f"💰 Estimated Price: ₹ {result['predicted_price']}")
            else:
                st.error(result.get("error", "Prediction failed"))

        except Exception as e:
            st.error(str(e))

    st.markdown("</div>", unsafe_allow_html=True)

# ================= HOTEL RECOMMENDER =================
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Find Best Hotels")

    col1, col2 = st.columns(2)

    with col1:
        place = st.selectbox(
            "Destination",
            ["Florianopolis (SC)", "Salvador (BH)"]
        )

        days = st.number_input("Number of Days", min_value=1, value=1)

    with col2:
        max_price = st.number_input("Max Price / Night", value=500)
        max_total = st.number_input("Max Total Budget", value=5000)

    if st.button("Recommend Hotels 🏨"):
        payload = {
            "place": place,
            "days": days,
            "max_price": max_price,
            "max_total": max_total
        }

        try:
            res = requests.post(f"{API_BASE_URL}/recommend-hotels", json=payload)
            result = res.json()

            if "recommended_hotels" in result and result["recommended_hotels"]:
                df = pd.DataFrame(result["recommended_hotels"])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No hotels found for given criteria")

        except Exception as e:
            st.error(str(e))

    st.markdown("</div>", unsafe_allow_html=True)

# ================= FOOTER =================
st.divider()
st.caption("Built with ❤️ using Streamlit | ML-Powered Travel Analytics")
