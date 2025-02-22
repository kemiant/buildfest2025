from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from nrclex import NRCLex
import time  

app = Flask(__name__)

# Emotion-to-color mapping for highlighting & haptic feedback
EMOTION_HAPTIC_MAPPINGS = {
    "anger": {"led": (255, 0, 0), "color": "red", "vibration": 200},        
    "fear": {"led": (128, 0, 128), "color": "blue", "vibration": 250},      
    "joy": {"led": (0, 255, 0), "color": "green", "vibration": 100},        
    "sadness": {"led": (0, 0, 255), "color": "blue", "vibration": 220},     
    "disgust": {"led": (255, 165, 0), "color": "yellow", "vibration": 180}, 
    "surprise": {"led": (255, 255, 0), "color": "yellow", "vibration": 150},
    "trust": {"led": (0, 255, 255), "color": "green", "vibration": 120},    
    "anticipation": {"led": (255, 192, 203), "color": "yellow", "vibration": 130},  
}

NEUTRAL_TEMP = 0.0  
LED_NEUTRAL = (255, 255, 255)  

highlighted_text_data = []

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

    # Ensure a valid color was sent
    if color not in ["yellow", "red", "blue", "green"]:
        return jsonify({"error": "Invalid color"}), 400

    # Define custom color mappings to match highlight colors
    COLOR_HAPTIC_MAPPINGS = {
        "yellow": {"led": (255, 255, 0), "vibration": 150},
        "red": {"led": (255, 0, 0), "vibration": 200},
        "blue": {"led": (0, 0, 255), "vibration": 250},
        "green": {"led": (0, 255, 0), "vibration": 100},
    }

    devices = discover_devices(1)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    dot = devices[0]

    # Set LED and haptics based on the user-selected color
    settings = COLOR_HAPTIC_MAPPINGS[color]
    dot.set_led(*settings["led"])
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    # Store highlight with selected color
    highlighted_text_data.append({"text": text, "color": color, "note": None})

    # Play haptic feedback for 1.5 seconds
    time.sleep(1.5)

    # Turn off vibration and LED
    dot.registers.set_vibration_intensity(0.0)
    adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
    dot.set_led(*adjusted_led)
    dot.registers.set_thermal_intensity(NEUTRAL_TEMP)  # Reset temperature to neutral
    dot.registers.set_thermal_intensity(0.0)  # Reset temp

    return jsonify({"message": f"Haptic feedback triggered for {color}, then turned off."})


@app.route("/analyze-sentiment", methods=["POST"])
def analyze_sentiment():
    data = request.json
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Perform sentiment analysis using NRCLex
    analysis = NRCLex(text)
    emotion_frequencies = analysis.affect_frequencies  # Dictionary of emotions & scores

    # Ensure NRCLex provided valid emotions
    if not emotion_frequencies or sum(emotion_frequencies.values()) == 0:
        return jsonify({"error": "Could not detect emotion from text."}), 400

    # Get the most dominant emotion based on highest score
    top_emotion = max(emotion_frequencies, key=emotion_frequencies.get, default="neutral")

    # Ensure the detected emotion is mapped to a color
    settings = EMOTION_HAPTIC_MAPPINGS.get(top_emotion, {"color": "yellow", "vibration": 150})

    devices = discover_devices(1)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    dot = devices[0]

    # Send LED and haptic feedback
    dot.set_led(*settings["led"])
    dot.registers.set_vibration_mode(1)
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    # Store the note with detected emotion
    highlighted_text_data.append({"text": text, "color": settings["color"], "note": text})

    # Play haptic feedback for 1.5 seconds
    time.sleep(1.5)

    # Stop vibration and reset settings
    dot.registers.set_vibration_intensity(0.0)
    adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
    dot.set_led(*adjusted_led)
    dot.registers.set_thermal_intensity(NEUTRAL_TEMP)  # Reset temperature to neutral
    dot.registers.set_thermal_intensity(0.0)  # Reset temperature

    return jsonify({
        "message": f"Emotion detected: {top_emotion}, color assigned: {settings['color']}, haptic feedback triggered.",
        "color": settings["color"],
        "emotion": top_emotion
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
