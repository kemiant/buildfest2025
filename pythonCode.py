from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from textblob import TextBlob  # Install using: pip install textblob
import time  # Added for sleep function

app = Flask(__name__)

# Color mappings for LED and vibration settings
HAPTIC_MAPPINGS = {
    "yellow": {"led": (255, 255, 0), "vibration": 150},
    "red": {"led": (255, 0, 0), "vibration": 200},
    "blue": {"led": (0, 0, 255), "vibration": 250},
    "green": {"led": (0, 255, 0), "vibration": 100},
}

# Default/neutral settings
NEUTRAL_TEMP = 0.0  # Neutral temperature level
LED_NEUTRAL = (255, 255, 255)  # Turn off the LED

highlighted_text_data = []  # Store highlighted text, colors, and notes

def adjust_intensity(color, intensity):
    """ Adjust LED brightness by scaling RGB values based on intensity (0.5 - 1.0) """
    return tuple(int(c * intensity) for c in color)

@app.route("/")
def home():
    return send_file("website.html")

@app.route("/haptic-feedback", methods=["POST"])
def haptic_feedback():
    data = request.json
    text = data.get("text", "")
    color = data.get("color", "")

    if color not in HAPTIC_MAPPINGS:
        return jsonify({"error": "Invalid color"}), 400

    devices = discover_devices(1)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    dot = devices[0]
    settings = HAPTIC_MAPPINGS[color]

    # Set LED and haptics
    dot.set_led(*settings["led"])
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    # Store the highlight
    highlighted_text_data.append({"text": text, "color": color, "note": None})

    # Play haptics for 1.5 seconds
    time.sleep(1.5)

    # Stop vibration, turn off LED, and reset temp
    dot.registers.set_vibration_intensity(0.0)
    adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
    dot.set_led(*adjusted_led)
    dot.registers.set_thermal_intensity(NEUTRAL_TEMP)  # Reset temperature to neutral

    return jsonify({"message": f"Haptic feedback triggered for {color}, then turned off."})

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

    # Calculate LED intensity based on sentiment strength
    intensity = max(0.5, min(1.0, abs(polarity) * 1.5))  # Normalize intensity (0.5 - 1.0)
    adjusted_led = adjust_intensity(HAPTIC_MAPPINGS[color]["led"], intensity)

    # Send haptic feedback
    devices = discover_devices(1)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    dot = devices[0]
    settings = HAPTIC_MAPPINGS[color]

    # Set LED with adjusted intensity and haptics
    dot.set_led(*adjusted_led)
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    # Store the note with color
    highlighted_text_data.append({"text": text, "color": color, "note": text})

    # Play haptics for 1.5 seconds
    time.sleep(1.5)

    # Stop vibration, turn off LED, and reset temp
    dot.registers.set_vibration_intensity(0.0)
    dot.set_led(*LED_OFF)  # Turn off the light
    dot.registers.set_thermal_intensity(NEUTRAL_TEMP)  # Reset temperature to neutral

    return jsonify({
        "message": f"Sentiment detected as {color}, intensity: {round(intensity * 100)}%, haptic feedback triggered, then turned off.",
        "color": color,
        "intensity": round(intensity * 100)
    })

@app.route("/get-highlights", methods=["GET"])
def get_highlights():
    return jsonify(highlighted_text_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
