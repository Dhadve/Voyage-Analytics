from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)

# ================= LOAD ARTIFACTS =================
model = joblib.load("model/flight_price_model.pkl")
scaler = joblib.load("model/scaler.pkl")
feature_names = joblib.load("model/feature_names.pkl")

# Load hotel data
hotels_df = pd.read_csv("data/hotels.csv")
print(hotels_df.columns.tolist())



# ================= HEALTH CHECK =================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Voyage Analytics API running"})


# ================= FLIGHT PRICE PREDICTION =================
@app.route("/predict-flight", methods=["POST"])
def predict_flight():
    try:
        data = request.get_json()

        # Convert input to DataFrame
        df = pd.DataFrame([data])

        # One-hot encode categorical features
        df = pd.get_dummies(
            df,
            columns=["from", "to", "agency", "flightType"],
            drop_first=False
        )

        # 🔑 ALIGN WITH TRAINING FEATURES
        df = df.reindex(columns=feature_names, fill_value=0)

        # 🔑 SCALE NUMERIC FEATURES ONLY
        numeric_cols = ["distance", "day"]
        df[numeric_cols] = scaler.transform(df[numeric_cols])

        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= HOTEL RECOMMENDER =================
@app.route("/recommend-hotels", methods=["POST"])
def recommend_hotels():
    try:
        data = request.get_json()

        place = data.get("place")
        max_price = data.get("max_price", 5000)
        max_total = data.get("max_total", 20000)

        if not place:
            return jsonify({"error": "place is required"}), 400

        results = hotels_df[
            (hotels_df["place"] == place) &
            (hotels_df["price"] <= max_price) &
            (hotels_df["total"] <= max_total)
        ].sort_values(
            by=["price", "total"],
            ascending=[True, True]
        )

        return jsonify({
            "recommended_hotels": results.head(5).to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# ================= RUN APP =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)





