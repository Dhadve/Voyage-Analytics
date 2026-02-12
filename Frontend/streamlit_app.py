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

# ================= HEADER =================
st.markdown("""
# ✈️ Voyage Analytics
### Smart Flight Pricing + Hotel Planning System
""")

st.divider()

tab1, tab2 = st.tabs(["✈️ Plan Flight", "🏨 Plan Stay"])

# =====================================================
# ✈️ FLIGHT TAB
# =====================================================

with tab1:

    st.subheader("Flight Planner")

    col1, col2, col3 = st.columns(3)

    from_city = col1.selectbox("From", [
        "Recife (PE)", "Brasilia (DF)", "Sao Paulo (SP)",
        "Rio de Janeiro (RJ)", "Natal (RN)",
        "Florianopolis (SC)", "Salvador (BH)", "Aracaju (SE)"
    ])

    to_options = [c for c in [
        "Recife (PE)", "Brasilia (DF)", "Sao Paulo (SP)",
        "Rio de Janeiro (RJ)", "Natal (RN)",
        "Florianopolis (SC)", "Salvador (BH)", "Aracaju (SE)"
    ] if c != from_city]

    to_city = col2.selectbox("To", to_options)

    day = col3.number_input("Day", min_value=1, max_value=31, value=10)

    agency = col1.selectbox("Agency", ["CloudFy", "FlyingDrops", "Rainbow"])
    flight_type = col2.selectbox("Class", ["economic", "premium", "firstClass"])

    distance = col3.number_input("Distance (km)", min_value=200, value=1000)

    if st.button("🔍 Predict Price"):

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

            # 🔥 METRIC CARD
            st.metric("💰 Flight Price", f"₹ {price}")

            # 📈 Price Simulation Chart
            trend_df = pd.DataFrame({
                "Day": list(range(1, 31)),
                "Estimated Price": [
                    price * (0.9 + d * 0.004) for d in range(30)
                ]
            })

            chart = alt.Chart(trend_df).mark_line().encode(
                x="Day",
                y="Estimated Price"
            )

            st.altair_chart(chart, use_container_width=True)

        else:
            st.error(res.json())

# =====================================================
# 🏨 HOTEL TAB
# =====================================================

with tab2:

    st.subheader("Hotel Planner")

    col1, col2, col3 = st.columns(3)

    place = col1.selectbox(
        "Destination",
        [
            "Recife (PE)", "Brasilia (DF)", "Sao Paulo (SP)",
            "Rio de Janeiro (RJ)", "Natal (RN)",
            "Florianopolis (SC)", "Salvador (BH)", "Aracaju (SE)"
        ]
    )

    days = col2.number_input("Stay (Days)", min_value=1, value=2)

    max_total = col3.number_input("Max Budget", value=20000)

    if st.button("🏨 Find Hotels"):

        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code == 200:
            hotels = res.json().get("recommended_hotels", [])

            if hotels:
                df = pd.DataFrame(hotels)

                # 🔥 Trip Cost Summary Card
                cheapest = df.iloc[0]["calculated_total"]

                st.metric("💼 Cheapest Stay", f"₹ {cheapest}")

                st.dataframe(df, use_container_width=True)

            else:
                st.warning("No hotels found under this budget.")

        else:
            st.error(res.json())
