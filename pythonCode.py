from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from textblob import TextBlob  # Install using: pip install textblob

app = Flask(__name__)

# Color mappings for LED and vibration settings
HAPTIC_MAPPINGS = {
    "yellow": {"led": (255, 255, 0), "vibration": 150},
    "red": {"led": (255, 0, 0), "vibration": 200},
    "blue": {"led": (0, 0, 255), "vibration": 250},
    "green": {"led": (0, 255, 0), "vibration": 100},
}

@app.route("/")
def home():
    return send_file("website.html")

@app.route("/haptic-feedback")
def haptic_feedback():
    color = request.args.get("color")
    if color not in HAPTIC_MAPPINGS:
        return "Invalid color", 400

    devices = discover_devices(1)
    if not devices:
        return "No dots found", 500

    dot = devices[0]
    settings = HAPTIC_MAPPINGS[color]

    dot.set_led(*settings["led"])
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    return f"Haptic feedback triggered for {color}!"

@app.route("/analyze-sentiment", methods=["POST"])
def analyze_sentiment():
    data = request.json
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Perform sentiment analysis
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity

    # Map sentiment to color
    if polarity > 0.3:
        color = "green"  # Positive
    elif polarity < -0.3:
        color = "red"  # Negative
    else:
        color = "yellow"  # Neutral

    # Send haptic feedback
    devices = discover_devices(1)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    dot = devices[0]
    settings = HAPTIC_MAPPINGS[color]

    dot.set_led(*settings["led"])
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    return jsonify({"message": f"Sentiment detected as {color}, haptic feedback triggered!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
