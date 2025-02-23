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

# Initialize lemmatizer for word processing
lemmatizer = WordNetLemmatizer()

# Initialize Flask app
app = Flask(__name__)

# Mapping of emotions to LED colors and vibration intensities
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

# Function to adjust brightness of LED colors
def adjust_intensity(color, intensity):
    """Adjust LED brightness by scaling RGB values based on intensity (0.5 - 1.0)."""
    return tuple(int(c * intensity) for c in color)

# Function to retrieve synonyms using WordNet
def get_synonyms(word):
    """Find synonyms using WordNet to increase emotion detection accuracy."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return list(synonyms)

# Home route to serve the main HTML page
@app.route("/")
def home():
    return send_file("website.html")

# Endpoint to trigger haptic feedback based on text selection
@app.route("/haptic-feedback", methods=["POST"])
def haptic_feedback():
    """Triggers haptic feedback when highlighting text."""
    data = request.json
    text = data.get("text", "")
    color = data.get("color", "")

    if not text or not color:
        return jsonify({"error": "Invalid input"}), 400

    # Find the corresponding haptic settings
    settings = next((v for k, v in EMOTION_HAPTIC_MAPPINGS.items() if v["color"] == color), None)
    if not settings:
        return jsonify({"error": "Invalid color"}), 400

    # Discover connected haptic devices
    devices = discover_devices(4)
    if not devices:
        return jsonify({"error": "No dots found"}), 500

    # Apply LED and vibration settings to the devices
    for dot in devices:
        dot.set_led(*settings["led"])
        dot.registers.set_vibration_mode(1)
        dot.registers.set_vibration_frequency(settings["vibration"])
        dot.registers.set_vibration_intensity(1.0)

    time.sleep(1.5)

    # Turn off haptic feedback after a delay
    for dot in devices:
        dot.registers.set_vibration_intensity(0.0)
        adjusted_led = adjust_intensity((255, 255, 255), 0.3)  # Neutral color
        dot.set_led(*adjusted_led)

    return jsonify({"message": f"Haptic feedback triggered for {color}, then turned off."})

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 130)  # Adjust speech speed
tts_engine.setProperty('voice', "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")

# Initialize a queue and flags for handling speech requests
tts_queue = queue.Queue()
tts_running = False
stop_tts = threading.Event()

# Background thread to handle text-to-speech requests
def tts_worker():
    """Background thread that reads aloud text from the queue."""
    global tts_running
    while True:
        text = tts_queue.get()
        if text is None:
            break
        
        tts_running = True
        stop_tts.clear()
        print(f"🔊 Speaking: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
        tts_running = False

# Start the text-to-speech worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# Endpoint to process text and read it aloud
@app.route("/speak-haptic", methods=["POST"])
def speak_haptic():
    """Reads text aloud and optionally triggers haptic feedback."""
    global tts_running
    
    if tts_running:
        stop_tts.set()
        tts_queue.queue.clear()
        return jsonify({"message": "🔴 Speech stopped."})
    
    data = request.json
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "⚠️ No text provided."}), 400
    
    print(f"📢 Reading: {text}")
    tts_queue.put(text)
    return jsonify({"message": "🔊 Reading aloud with haptic feedback."})

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
