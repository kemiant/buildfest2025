from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from nrclex import NRCLex
import time
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import nltk

# Ensure necessary NLTK data is downloaded
nltk.download('wordnet')
nltk.download('punkt')

lemmatizer = WordNetLemmatizer()

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

# Emotion keyword mapping (checked first before NRCLex)
EMOTION_KEYWORDS = {
    "anger": ["angry", "mad", "furious", "rage", "irritated"],
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

def get_synonyms(word):
    """Find synonyms using WordNet to increase emotion detection accuracy."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return list(synonyms)

@app.route("/")
def home():
    return send_file("website.html")

@app.route("/haptic-feedback", methods=["POST"])
def haptic_feedback():
    """
    Triggers haptic feedback when highlighting text.
    """
    data = request.json
    text = data.get("text", "")
    color = data.get("color", "")

    if not text or not color:
        return jsonify({"error": "Invalid input"}), 400

    # Use predefined colors for haptic feedback
    settings = next((v for k, v in EMOTION_HAPTIC_MAPPINGS.items() if v["color"] == color), None)

    if not settings:
        return jsonify({"error": "Invalid color"}), 400

    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    for dot in devices:
        dot.set_led(*settings["led"])
        dot.registers.set_vibration_mode(1)
        dot.registers.set_vibration_frequency(settings["vibration"])
        dot.registers.set_vibration_intensity(1.0)

    highlighted_text_data.append({"text": text, "color": color, "note": None})

    time.sleep(1.5)

    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
        dot.set_led(*adjusted_led)
        dot.registers.set_thermal_intensity(NEUTRAL_TEMP)

    return jsonify({"message": f"Haptic feedback triggered for {color}, then turned off."})

@app.route("/analyze-sentiment", methods=["POST"])
def analyze_sentiment():
    """
    Analyzes sentiment when adding a note and triggers corresponding haptic feedback.
    """
    data = request.json
    text = data.get("text", "").strip().lower()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Tokenize and lemmatize each word
    words = [lemmatizer.lemmatize(word) for word in word_tokenize(text)]

    # Step 1: Check predefined emotion keywords first
    detected_emotion = detect_emotion_from_text(words)

    # Step 2: If no keyword match, use NRCLex to analyze each word separately
    emotion_counter = Counter()
    if detected_emotion == "neutral":
        for word in words:
            analysis = NRCLex(word)  # Run NRCLex analysis
            
            # Ensure NRCLex actually finds meaningful values
            for emotion, score_list in analysis.raw_emotion_scores.items():
                if isinstance(score_list, list):  
                    highest_score = max(score_list)  # Take highest score from list
                else:
                    highest_score = score_list  # If it's a single number

                if highest_score > 0:  # Filter out zero-score emotions
                    emotion_counter[emotion] += highest_score  # Accumulate scores

            # If NRCLex fails, try synonyms
            if sum(emotion_counter.values()) == 0:
                synonyms = get_synonyms(word)
                for synonym in synonyms:
                    analysis = NRCLex(synonym)
                    for emotion, score_list in analysis.raw_emotion_scores.items():
                        highest_score = max(score_list) if isinstance(score_list, list) else score_list
                        if highest_score > 0:
                            emotion_counter[emotion] += highest_score

        # Step 3: Select the dominant emotion
        if emotion_counter:
            detected_emotion = max(emotion_counter, key=emotion_counter.get)

    print(f"Detected emotions from NRCLex: {emotion_counter}")
    
    # Assign color and haptic feedback based on detected emotion
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

def detect_emotion_from_text(words):
    """
    Manually detects emotion by checking if any words in the list match known emotion keywords.
    """
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in keywords for word in words):  # Direct match
            return emotion
    return "neutral"


@app.route("/play-haptic-feedback", methods=["POST"])
def play_haptic_feedback():
    """
    Plays haptic feedback when a user clicks a highlighted text or note.
    """
    data = request.json
    text = data.get("text", "").strip()

    # Find the matching highlight/note
    matching_entry = next((item for item in highlighted_text_data if item["text"] == text or item["note"] == text), None)

    if not matching_entry:
        return jsonify({"error": "No matching highlight or note found"}), 400

    color = matching_entry.get("color", "yellow")  # Default to yellow if not found
    settings = next((v for k, v in EMOTION_HAPTIC_MAPPINGS.items() if v["color"] == color), None)

    if not settings:
        return jsonify({"error": "Invalid color"}), 400

    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    # Trigger haptic feedback on all devices
    for dot in devices:
        dot.set_led(*settings["led"])
        dot.registers.set_vibration_mode(1)
        dot.registers.set_vibration_frequency(settings["vibration"])
        dot.registers.set_vibration_intensity(1.0)

    time.sleep(1.5)  # Haptic feedback duration

    # Turn off haptics
    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        dot.set_led(*adjust_intensity(LED_NEUTRAL, 0.3))
        dot.registers.set_thermal_intensity(NEUTRAL_TEMP)

    return jsonify({
        "message": f"Haptic feedback played for highlighted text or note: {text}",
        "color": color
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)