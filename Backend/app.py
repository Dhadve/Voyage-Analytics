from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)

# ================= LOAD ARTIFACTS =================
MODEL_PATH = "model/flight_price_model.pkl"
FEATURE_PATH = "model/feature_names.pkl"

model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURE_PATH)

# Load hotel data
hotels_df = pd.read_csv("data/hotels.csv")

# ================= HEALTH CHECK =================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Voyage Analytics API running"})


# =====================================================
# ================= FLIGHT PRICE API ==================
# =====================================================
@app.route("/predict-flight", methods=["POST"])
def predict_flight():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON payload received"}), 400

        df = pd.DataFrame([data])

        # One-hot encode categorical columns
        df = pd.get_dummies(
            df,
            columns=["from", "to", "agency", "flightType"],
            drop_first=False
        )

        # Align features with training
        df = df.reindex(columns=feature_names, fill_value=0)

        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# ================= HOTEL RECOMMENDER =================
# =====================================================
@app.route("/recommend-hotels", methods=["POST"])
def recommend_hotels():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON payload received"}), 400

        place = data.get("place")
        days = int(data.get("days", 1))
        max_total = float(data.get("max_total", 20000))

        if not place:
            return jsonify({"error": "place is required"}), 400

        # 1️⃣ Filter by city
        filtered = hotels_df[hotels_df["place"] == place].copy()

        if filtered.empty:
            return jsonify({"recommended_hotels": []})

        # 2️⃣ Remove duplicate hotel names
        filtered = filtered.drop_duplicates(subset=["name"])

        # 3️⃣ Recalculate total based on USER entered days
        filtered["calculated_total"] = filtered["price"] * days

        # 4️⃣ Apply budget filter
        filtered = filtered[
            filtered["calculated_total"] <= max_total
        ]

        # 5️⃣ Sort by lowest total cost
        filtered = filtered.sort_values(
            by="calculated_total",
            ascending=True
        )

        # 6️⃣ Return only necessary clean fields
        result = filtered[[
            "name",
            "place",
            "price",
            "calculated_total"
        ]].head(5).to_dict(orient="records")

        return jsonify({
            "recommended_hotels": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# =====================================================
# ================= RUN (LOCAL ONLY) ==================
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

