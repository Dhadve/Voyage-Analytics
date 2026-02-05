from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)

# Load model
model = joblib.load("model/flight_price_model.pkl")

# ✅ EXACT FEATURES USED DURING TRAINING
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

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        # Convert input to DataFrame
        df = pd.DataFrame([data])

        # One-hot encode categorical columns
        df = pd.get_dummies(
            df,
            columns=["from", "to", "agency", "flightType"],
            drop_first=False
        )

        # 🔑 Align columns with training data
        df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0)

        # Predict
        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


