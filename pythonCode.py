from flask import Flask, request, send_file, jsonify
from datafeel.device import discover_devices
from nrclex import NRCLex
import time
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import nltk
import speech_recognition as sr
import pyttsx3
import threading
import queue


# Ensure necessary NLTK data is downloaded
nltk.download('wordnet')
nltk.download('punkt')

lemmatizer = WordNetLemmatizer()

app = Flask(__name__)

# Emotion-to-color mapping for highlighting & haptic feedback
EMOTION_HAPTIC_MAPPINGS = {
    "anger": {"led": (255, 0, 0), "color": "red", "vibration": 200, "temperature": 40.0, "intensity": 1.0, "mode": 1},
    "fear": {"led": (128, 0, 128), "color": "blue", "vibration": 250, "temperature": 12.0, "intensity": 0.8, "mode": 1},
    "joy": {"led": (0, 255, 0), "color": "green", "vibration": 100, "temperature": 28.0, "intensity": 0.6, "mode": 1},
    "sadness": {"led": (0, 0, 255), "color": "blue", "vibration": 220, "temperature": 10.0, "intensity": 0.5, "mode": 1},
    "disgust": {"led": (255, 165, 0), "color": "yellow", "vibration": 180, "temperature": 29.0, "intensity": 0.7, "mode": 1},
    "surprise": {"led": (255, 255, 0), "color": "yellow", "vibration": 150, "temperature": 31.0, "intensity": 0.9, "mode": 1},
    "trust": {"led": (0, 255, 255), "color": "green", "vibration": 120, "temperature": 28.5, "intensity": 0.7, "mode": 1},
    "anticipation": {"led": (255, 192, 203), "color": "yellow", "vibration": 130, "temperature": 30.5, "intensity": 0.6, "mode": 1},
}

# color mapping for highlighting & haptic feedback
EMOTION_KEYWORDS = {
    "anger": [
        "angry", "mad", "furious", "rage", "irritated", "frustrated", "annoyed", "resentful",
        "offended", "outraged", "infuriated", "enraged", "cross", "fuming", "exasperated", "bitter"
    ],
    "fear": [
        "scared", "afraid", "terrified", "nervous", "anxious", "panicked", "alarmed", "horrified",
        "worried", "apprehensive", "uneasy", "frightened", "shaken", "startled", "intimidated"
    ],
    "joy": [
        "happy", "excited", "delighted", "joyful", "glad", "cheerful", "content", "elated",
        "ecstatic", "thrilled", "euphoric", "radiant", "overjoyed", "satisfied", "grateful", "optimistic"
    ],
    "sadness": [
        "sad", "unhappy", "depressed", "down", "miserable", "gloomy", "melancholy", "heartbroken",
        "sorrowful", "despondent", "grieving", "disheartened", "mournful", "dejected", "hopeless"
    ],
    "disgust": [
        "disgusted", "gross", "revolted", "sickened", "repulsed", "nauseated", "appalled",
        "abhorrent", "distasteful", "detestable", "loathsome", "horrid", "foul", "vile", "repugnant"
    ],
    "surprise": [
        "shocked", "amazed", "astonished", "surprised", "dumbfounded", "speechless", "stunned",
        "startled", "flabbergasted", "bewildered", "astounded", "aghast", "overwhelmed", "taken aback"
    ],
    "trust": [
        "trust", "confident", "assured", "reliable", "faithful", "dependable", "loyal",
        "secure", "steady", "hopeful", "unwavering", "devoted", "committed", "believing", "credible"
    ],
    "anticipation": [
        "eager", "expecting", "anticipating", "hopeful", "enthusiastic", "impatient",
        "excited", "aspiring", "optimistic", "restless", "prepared", "looking forward", "anxious"
    ]
}
color_rgb_mapping = {
        "yellow": (255, 255, 0),
        "red": (255, 0, 0),
        "blue": (0, 0, 255),
        "green": (0, 128, 0)  # Using the standard web-safe green
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
        dot.registers.set_vibration_intensity(settings["intensity"])
        dot.registers.set_thermal_intensity(settings["temperature"])

    highlighted_text_data.append({
    "text": text,
    "color": color,
    "note": None,
    "vibration": settings["vibration"],  # ✅ Store vibration settings
    "type": "normal",
    "temperature": settings["temperature"],
    "mode": settings["mode"],
    "intensity": settings["intensity"]
    })
    print(highlighted_text_data)


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
    This is taking the text in the notes, not the highlighted text
    """
    data = request.json
    text = data.get("text", "").strip().lower()
    curr_text = data.get("highlightedText", "").strip().lower()
    print("This is the curr before", curr_text)

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
    settings = EMOTION_HAPTIC_MAPPINGS.get(detected_emotion, {"led": (255, 255, 255), "color": "yellow", "vibration": 150, "mode": 1, "temperature": 28.0})

    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    for dot in devices:
        dot.set_led(*settings["led"])
        dot.registers.set_vibration_mode(1)
        dot.registers.set_vibration_frequency(settings["vibration"])
        dot.registers.set_vibration_intensity(1)
        dot.registers.set_thermal_intensity(settings["temperature"])
    print("This is the curr after", curr_text)
    
    
    time.sleep(1.5)
    
    dot.registers.set_vibration_intensity(0.0)  # Stop vibration
    
    for dot in devices:
        if detected_emotion == "neutral":
            dot.set_led(255, 255, 255)  # White, but turn it off quickly
            dot.registers.set_vibration_intensity(0.0)  # Stop vibration
            dot.registers.set_thermal_intensity(NEUTRAL_TEMP)
        else:
            dot.set_led(*settings["led"])
            dot.registers.set_vibration_mode(1)
            dot.registers.set_vibration_frequency(settings["vibration"])
            dot.registers.set_vibration_intensity(settings["intensity"])
            dot.registers.set_thermal_intensity(settings["temperature"])

        
    highlighted_text_data.append({
    "text": curr_text,
    "color": settings["color"],
    "note": text,
    "vibration": settings["vibration"],  # ✅ Store vibration settings
    "type": "sense",
    "emotion": detected_emotion,
    "temperature": settings["temperature"],
    "mode": settings["mode"],
    "intensity": settings["intensity"]
    })
    print(highlighted_text_data)

    time.sleep(1.5)

    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
        dot.set_led(*adjusted_led)
        dot.registers.set_thermal_intensity(NEUTRAL_TEMP)

    return jsonify({
        "message": f"Emotion detected: {detected_emotion}, color assigned: {settings['color']}, haptic feedback triggered.",
        "color": settings["color"],
        "emotion": detected_emotion, "temperature": settings["temperature"]
    })

def detect_emotion_from_text(words):
    """
    Manually detects emotion by checking if any words in the list match known emotion keywords.
    """
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in keywords for word in words):  # Direct match
            return emotion
    return "neutral"


@app.route("/replay-haptic", methods=["POST"])
def replay_haptic():


    data = request.json
    text = data.get("text", "").strip().lower()

    print(f"Received request to replay haptic for: '{text}'")  # Debugging
    print(f"Stored highlights: {highlighted_text_data}")  # Debugging

    # Find matching highlight
    highlight = next((item for item in highlighted_text_data if item["text"].strip().lower() == text), None)

    if not highlight:
        return jsonify({"error": "No haptic feedback found for the selected text."}), 400

    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No haptic devices found."}), 500

    if highlight.get("type") == "normal":
        color_settings = {"led": color_rgb_mapping.get(highlight["color"], (255, 255, 255))}
    else:
        emotion = highlight.get("emotion", "neutral")  # Default to "neutral" if no emotion found
        color_settings = EMOTION_HAPTIC_MAPPINGS.get(emotion, {"led": (255, 255, 255)})

    for dot in devices:
        dot.set_led(*color_settings["led"])
        dot.registers.set_vibration_mode(highlight["mode"])
        dot.registers.set_vibration_frequency(highlight["vibration"])
        dot.registers.set_vibration_intensity(highlight["intensity"])
        dot.registers.set_thermal_intensity(highlight["temperature"])

    time.sleep(1.5)

    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        adjusted_led = adjust_intensity(LED_NEUTRAL, .3)
        dot.set_led(*adjusted_led)

    return jsonify({"message": f"Replayed haptic feedback for '{text}' with color {highlight['color']}."})


# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 130)  # Slow down speech (default is ~200)
tts_engine.setProperty('voice', "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")

# Global Variables
tts_queue = queue.Queue()  # Speech queue
tts_running = False  # Flag for speech state
stop_tts = threading.Event()  # Event to stop speech immediately


def tts_worker():
    """ Background thread that reads aloud from the queue and triggers haptic feedback. """
    global tts_running
    while True:
        text = tts_queue.get()  # Get text to speak
        if text is None:
            break  # Stop worker if None received

        words = text.split()
        tts_running = True
        stop_tts.clear()  # Reset stop event

        devices = discover_devices(4)  # Find haptic devices
        if not devices:
            print("⚠️ No haptic devices found.")
        
        for word in words:
            if stop_tts.is_set():  # If stop requested, exit loop
                print("🛑 Speech stopped.")
                break
            
            print(f"🔊 Speaking: {word}")
            tts_engine.say(word)
            tts_engine.runAndWait()  # Process speech queue

            # Trigger haptic feedback if word was annotated
            highlight = next((item for item in highlighted_text_data if item["text"].strip().lower() == word.lower()), None)
            if highlight and devices:
                color = highlight["color"]
                vibration = highlight["vibration"]
                settings = EMOTION_HAPTIC_MAPPINGS.get(highlight.get("emotion", "neutral"), {"led": (255, 255, 255),  "vibration": 150, "mode": 1, "temperature": 28.0})

                for dot in devices:
                    dot.set_led(*settings["led"])
                    dot.registers.set_vibration_frequency(vibration)
                    dot.registers.set_vibration_intensity(1.0)

            time.sleep(0.4)  # Small delay to space out speech

            # Stop haptics after each word
            for dot in devices:
                dot.registers.set_vibration_intensity(0.0)
                dot.set_led(255, 255, 255)

        tts_running = False  # Mark speech as completed

# Start TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

@app.route("/speak-haptic", methods=["POST"])
def speak_haptic():
    print("I PASSED")
    """ Reads text aloud & triggers haptic feedback for highlighted words. """
    global tts_running

    if tts_running:  # If speech is running, stop it immediately
        stop_tts.set()
        tts_queue.queue.clear()  # Clear pending speech
        return jsonify({"message": "🔴 Speech stopped."})

    data = request.json
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "⚠️ No text provided."}), 400

    print(f"📢 Reading: {text}")
    tts_queue.put(text)  # Add text to queue
    return jsonify({"message": "🔊 Reading aloud with haptic feedback."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
