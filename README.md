# Text-to-Speech and Haptic Feedback Flask Application

## Overview
This is a Flask-based web application that provides text-to-speech functionality along with haptic feedback for highlighted text. The application integrates NLP for sentiment analysis and utilizes the DataFeel haptic hardware for tactile responses.

## Features
- **Text-to-Speech (TTS)**: Uses `pyttsx3` to read aloud selected text.
- **Haptic Feedback**: Triggers vibrations and LED colors based on detected emotions.
- **Sentiment Analysis**: Identifies emotions using NRCLex and predefined keyword lists.
- **Flask API Endpoints**: Provides RESTful API to handle requests from a frontend interface.
- **Multithreading Support**: Uses background threads for speech processing.

## Technologies Used
- **Flask**: Web framework for handling API requests.
- **NLTK & NRCLex**: Natural Language Processing for sentiment analysis.
- **pyttsx3**: Offline text-to-speech conversion.
- **DataFeel SDK**: Haptic feedback via connected devices.
- **Threading & Queue**: Manages asynchronous speech synthesis.

## Installation
### Prerequisites
Ensure Python is installed on your system. Install dependencies using:
```sh
pip install flask nrclex nltk pyttsx3 speechrecognition
```

### Run the Application
Start the Flask server with:
```sh
python pythonCode.py
```

Access the application via:
```
http://127.0.0.1:5000
```

## API Endpoints
### Home Route
**`GET /`**
- Serves the `website.html` frontend.

### Haptic Feedback
**`POST /haptic-feedback`**
- Triggers haptic feedback for highlighted text.
- **Request Body:**
  ```json
  {"text": "example text", "color": "red"}
  ```

### Analyze Sentiment
**`POST /analyze-sentiment`**
- Analyzes text sentiment and applies corresponding haptic feedback.
- **Request Body:**
  ```json
  {"text": "this is amazing!", "highlightedText": "amazing!"}
  ```

### Read Aloud & Haptic
**`POST /speak-haptic`**
- Reads aloud provided text and applies haptic feedback.
- **Request Body:**
  ```json
  {"text": "Hello, world!"}
  ```

### Stop Speech
**`POST /speak-haptic`** (if already speaking)
- Stops the current text-to-speech playback immediately.

## File Structure
```
project/
│── pythonCode.py    # Main Flask application
│── website.html     # Frontend UI
│── README.md        # Documentation
```

## Future Improvements
- **Speech-to-Text Integration**: Enable real-time voice input.
- **Improved Sentiment Analysis**: Utilize deep learning models for better accuracy.
- **UI Enhancements**: Improve frontend with interactive elements.

## License
This project is open-source under the MIT License.

## Contributors
- **Your Name** – Developer & Maintainer
