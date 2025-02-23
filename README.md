# Text-to-Speech and Haptic Feedback Flask Application

## Overview
This is a Flask-based web application that provides text-to-speech functionality along with haptic feedback for highlighted text. The application integrates NLP for sentiment analysis and utilizes the DataFeel haptic hardware for tactile responses.

![image](https://github.com/user-attachments/assets/d212c791-c654-47df-bc38-6d8a5a801a66)


## Features
- **Text-to-Speech (TTS)**: Uses `pyttsx3` to read aloud selected text.
- **Haptic Feedback**: Triggers vibrations and LED colors based on detected emotions.
- **Sentiment Analysis**: Identifies emotions using NRCLex and predefined keyword lists.
- **Flask API Endpoints**: Provides RESTful API to handle requests from a frontend interface.
- **Multithreading Support**: Uses background threads for speech processing.
- **Interactive UI**: Built using HTML, CSS, and JavaScript.

## Technologies Used
- **Flask**: Web framework for handling API requests.
- **NLTK & NRCLex**: Natural Language Processing for sentiment analysis.
- **pyttsx3**: Offline text-to-speech conversion.
- **DataFeel SDK**: Haptic feedback via connected devices.
- **Threading & Queue**: Manages asynchronous speech synthesis.
- **JavaScript & CSS**: Frontend interaction and UI styling.

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

## Frontend (HTML & CSS)
The `website.html` file provides a user interface with interactive elements such as:
- **Text Highlighter**: Allows users to highlight text and trigger haptic feedback.
- **Read Aloud Button**: Sends selected text to the backend for text-to-speech processing.
- **Progress Indicator**: Displays reading progress.
- **Styled Layout**: Uses CSS for a visually appealing design with animated background and buttons.

### Key Features
- **Highlighting Text**: 
  - Users can select text and highlight it in different colors.
  - Highlighted text is sent to the backend for emotion analysis and haptic response.

- **Interactive Buttons**:
  - **✍️ Highlight Button**: Toggles highlight color options.
  - **💬 Add Note**: Allows users to annotate highlighted text.
  - **🔊 Read Aloud**: Initiates text-to-speech and haptic response.

- **JavaScript Enhancements**:
  - Handles AJAX requests for speech synthesis.
  - Provides smooth animations for alerts and modal popups.

![image](https://github.com/user-attachments/assets/493aadb7-a3f8-44ac-baf2-b830fc6dc046)


## Future Improvements
- **Speech-to-Text Integration**: Enable real-time voice input.
- **Improved Sentiment Analysis**: Utilize deep learning models for better accuracy.
- **UI Enhancements**: Improve frontend with interactive elements.
- 

## Our Creation Process

**Pre-build research**
Before the build starts, we conduct research on library advocacy and social issues, creating a research document, reading online, and even speaking to librarians at the Austin Public Library.

![image](https://github.com/user-attachments/assets/7ece9bab-d6e6-4be5-a5ef-5c47cb0d6548)
_The first tab of a long collaborative document_


**Friday: Team formation, brainstorming, and the beginnings**
A group of three and a group of two meet and combine! We learn about Datafeel tech, brain dump possible solutions, and present a "Wellness lab" idea during the gallery walk, sharing features meant to calm busy adults working in the ilbrary. Halfway through the presentation (and before we even get to feedback), we realize we don't like it. We spend the rest of the night spitballing ideas, converging on a desire for personal connection which feels all too lacking in this day and age. Additional feedback leads us to hone in on the ability for users to not only experience but also create haptic experiences, and we land on an annotation tool before heading out for the night. Meanwhile, our tech guru Cammi is starting on the basics on input and output to the Datafeel Dots.
![IMG_1208](https://github.com/user-attachments/assets/f905b821-69ed-4a5f-80b2-44561ca69c06)
![IMG_1214](https://github.com/user-attachments/assets/54b2bce6-54b5-4019-bd7b-382edb4856ff)



**Saturday: Build, build, build!**
Now that we have an idea, we dive into the mechanics of how it will work. Helen, Anooshka, and Maddie research connections between color, sound, temperature, and emotion, and Alana maps out a plan for linking sentiment parameters like valence, dominance, and arousal to vibration, color, and temperature. Cammi continues to code. 
![1618135506260521265](https://github.com/user-attachments/assets/07c2e030-b887-45e0-a4de-7ebcff32cabf)

Once that's mapped out, we split into working on slides and prototypes. We decide a chair would create a comfortable and engaging experience while encouraging interaction with libraries as a third space; this would especially enhance the objective of promoting discussion and thought. We begin work on designs, where to put the dots, and how to construct it.
![image](https://github.com/user-attachments/assets/bb106a41-357f-4cf3-b26f-97b42ff3dd36)
![image](https://github.com/user-attachments/assets/41a15fbc-2112-4c47-8c62-f209466e581e)


However, in making our presentation, we realize we need to hone in on our topic even more. How would this annotation technology be implemented to help libraries on a specific topic? After additional group discussion, we have our answer: the power of saving and sharing emotions through immersive haptic feedback could serve as a powerful tool to communicate the importance of literature on lives. By providing a platform for sharing the impact of books with less affected popualations like working adults, we can support library advocacy by creating cross-generational connections and empowering students to fight against book bans. 

![image](https://github.com/user-attachments/assets/af59c34e-a888-4d65-bbd6-bbef3dd3c644)
![IMG_9149](https://github.com/user-attachments/assets/0c35f483-259c-4b1d-97c7-21f4989eb7de)![IMG_9157](https://github.com/user-attachments/assets/a75896ed-0659-47ad-8544-fea428c0c210)

With a clear vision, we dive fully into our prototype and final presentation resources. As we create the prototype, we make small adjustments to accomodate the limitations of the dots, including moving them around to stay with our prototype. With one neck, one front, and two wrist dots, the code continuing to code, and the website UI designed, our project comes together, piece by piece. 


![image](https://github.com/user-attachments/assets/13b43711-2e4b-49ab-b997-e653710c2dc2)
![image](https://github.com/user-attachments/assets/4e912e96-1c27-4ec2-bb46-4af80a0b6c7d)

## License
This project is open-source under the MIT License.

## Contributors
- **Your Name** – Developer & Maintainer
