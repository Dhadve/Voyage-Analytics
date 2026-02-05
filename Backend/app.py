from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)

# Load ML model
model = joblib.load("model/flight_price_model.pkl")

# Load hotel data
hotels_df = pd.read_csv("data/hotels.csv")

# === FEATURES USED DURING TRAINING (VERY IMPORTANT) ===
FEATURE_COLUMNS = [
    "distance",
    "day",

    # from
    "from_Brasilia (DF)",
    "from_Recife (PE)",

    # to
    "to_Brasilia (DF)",
    "to_Recife (PE)",

    # agency
    "agency_CloudNine",
    "agency_FlyingDrops",
    "agency_Rainbow",

    # flightType
    "flightType_economy",
    "flightType_business",
    "flightType_firstClass",
    "flightType_premium"
]

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Flight Price API running"})

# ================= FLIGHT PRICE API =================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        df = pd.DataFrame([data])

        df = pd.get_dummies(
            df,
            columns=["from", "to", "agency", "flightType"],
            drop_first=False
        )

        # Align features
        df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0)

        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= HOTEL RECOMMENDER API =================
@app.route("/recommend-hotel", methods=["POST"])
def recommend_hotel():
    try:
        data = request.get_json()

        city = data.get("city")
        max_price = data.get("max_price", 5000)
        min_rating = data.get("min_rating", 3)

        if not city:
            return jsonify({"error": "city is required"}), 400

        filtered = hotels_df[
            (hotels_df["city"] == city) &
            (hotels_df["price_per_night"] <= max_price) &
            (hotels_df["rating"] >= min_rating)
        ].sort_values(
            by=["rating", "price_per_night"],
            ascending=[False, True]
        )

        return jsonify({
            "recommended_hotels": filtered.head(5).to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
