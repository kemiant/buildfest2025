from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from nrclex import NRCLex
import time
from collections import Counter
from nltk.stem import WordNetLemmatizer  # Fixes variations like "irritated" -> "irritate"
import nltk

nltk.download('wordnet')  # Ensure WordNet is available
lemmatizer = WordNetLemmatizer()  # Initialize Lemmatizer

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

# Emotion keyword mapping (used FIRST before NRCLex)
EMOTION_KEYWORDS = {
    "anger": ["angry", "mad", "furious", "rage"],
    "fear": ["scared", "afraid", "terrified", "nervous", "anxious"],
    "joy": ["happy", "excited", "delighted", "joyful", "glad"],
    "sadness": ["sad", "unhappy", "depressed", "down", "miserable"],
    "disgust": ["disgusted", "gross", "revolted", "sickened"],
    "surprise": ["shocked", "amazed", "astonished", "surprised"],
    "trust": ["trust", "confident", "assured", "reliable"],
    "anticipation": ["eager", "expecting", "anticipating"],
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

@app.route("/analyze-sentiment", methods=["POST"])
def analyze_sentiment():
    data = request.json
    text = data.get("text", "").strip().lower()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Step 1: Try to detect emotion using the keyword dictionary first
    detected_emotion = detect_emotion_from_text(text)

    # Step 2: If no direct match, use NRCLex analysis **on each word separately**
    if detected_emotion == "neutral":
        words = text.split()  # Break text into individual words
        emotion_counter = Counter()  # Stores frequency of detected emotions

        for word in words:
            lemmatized_word = lemmatizer.lemmatize(word)  # Convert word to base form
            analysis = NRCLex(lemmatized_word)  # Run NRCLex on the lemmatized word

            # Ensure NRCLex actually finds meaningful values
            for emotion, score in analysis.raw_emotion_scores.items():
                if score > 0.05:  # Only consider words with valid scores
                    emotion_counter[emotion] += score  # Accumulate emotion scores

        # Step 3: Find the emotion with the highest total score
        if emotion_counter:
            detected_emotion = emotion_counter.most_common(1)[0][0]  # Get most frequent emotion

    # Step 4: Ensure detected emotion is mapped to a color
    print(f"Detected emotions from NRCLex: {emotion_counter}")
    settings = EMOTION_HAPTIC_MAPPINGS.get(detected_emotion, {"led": (255, 255, 255), "color": "yellow", "vibration": 150})

    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    for dot in devices:
        dot.set_led(*settings["led"])
        dot.registers.set_vibration_mode(1)
        dot.registers.set_vibration_frequency(settings["vibration"])
        dot.registers.set_vibration_intensity(1.0)

    highlighted_text_data.append({"text": text, "color": settings["color"], "note": text})

    time.sleep(1.5)

    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
        dot.set_led(*adjusted_led)
        dot.registers.set_thermal_intensity(NEUTRAL_TEMP)

    return jsonify({
        "message": f"Emotion detected: {detected_emotion}, color assigned: {settings['color']}, haptic feedback triggered.",
        "color": settings["color"],
        "emotion": detected_emotion
    })

def detect_emotion_from_text(text):
    """
    Manually detects emotion from text using expanded keyword matching.
    If no exact word match is found, return "neutral".
    """
    words = text.split()  # Tokenize text
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in words for word in keywords):  # Direct match
            return emotion
    return "neutral"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
