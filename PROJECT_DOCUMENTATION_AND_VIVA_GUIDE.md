# AI Chatbot Project Documentation & Viva Guide

## 1. Project Overview & Features
This project is an advanced, hybrid AI Chatbot that combines a **Local Neural Network** for specific commands with the **Google Gemini API** for general intelligence.

### Key Features Added:
*   **Hybrid Intelligence:** Automatically switches between a custom-trained local model (for exact control) and Gemini Cloud AI (for complex logic).
*   **Voice Interaction:**
    *   **Speech-to-Text (STT):** Users can speak their queries using the microphone button.
    *   **Text-to-Speech (TTS):** The AI can read responses aloud with a click of a button.
*   **Real-time Sentiment Analysis:** The UI changes color (Green/Red/Purple) based on the emotional tone of the AI's response using NLTK VADER.
*   **Image Generation:** Capable of generating images using Google's Imagen model when requested.
*   **Premium UI/UX:** A "Glassmorphism" design with dark mode, smooth animations, and responsive layout.
*   **Usage Tracking:** Monitors daily query limits to prevent API overuse.
*   **Feedback System:** Allows users to rate responses and provide comments.

---

## 2. Technical Architecture (How it Works)

### The Hybrid AI Approach
The system uses a "Confidence Threshold" strategy:
1.  **Step 1 (Local Model):** The user's input is first analyzed by our local Neural Network (built from scratch using NumPy).
    *   It looks for specific *intents* defined in `data/intents.json` (e.g., "greeting", "time", "date", "jokes").
    *   If the model is >75% confident it knows the answer, it responds instantly.
    *   **Benefit:** Fast, free, works offline for basic tasks, full control over specific answers.
2.  **Step 2 (Cloud Fallback):** If the local model is unsure, the query is sent to **Google Gemini**.
    *   Gemini handles complex questions ("Write a poem", "Explain quantum physics").
    *   **Benefit:** Infinite knowledge, handles context and creativity.

### Dynamic Context (Time/Date)
*   The system injects the current real-world time and date into the context before sending it to the AI, ensuring the bot always knows "now".

---

## 3. The Training Process (`legacy/train_chatbot.py`)
This script trains the Local AI model. It does not use TensorFlow or PyTorch; it uses **Pure Math (NumPy)** to build a Neural Network.

**Steps:**
1.  **Load Data:** Reads `data/intents.json`.
2.  **Preprocessing (NLTK):**
    *   **Tokenization:** Breaks sentences into words.
    *   **Stemming:** Reduces words to their root (e.g., "running" -> "run").
3.  **Feature Extraction (Bag of Words):** Converts text into a list of 0s and 1s representing which known words are present.
4.  **Training (Backpropagation):**
    *   The network creates random "Weights".
    *   It guesses the intent of a sentence.
    *   It calculates the error (Loss).
    *   It updates the weights to reduce the error (Gradient Descent).
5.  **Saving:** The learned weights are saved to `chatbot_model.pkl` to be loaded by the main app.

---

## 4. File Structure Explained

*   **`app.py` (The Brain):**
    *   The Flask Backend server.
    *   Loads the trained model (`pkl`).
    *   Handles API routes (`/api/chat`, `/api/usage`).
    *   Manages the logic for switching between Local AI and Gemini.
    *   Runs Sentiment Analysis using NLTK.
*   **`static/script.js` (The Behavior):**
    *   The Frontend Logic.
    *   Sends user messages to the server.
    *   Updates the chat UI (bubbles, avatars).
    *   Handles **Voice (Web Speech API)** and **TTS**.
    *   Updates colors based on sentiment.
*   **`static/style.css` (The Look):**
    *   Contains all styling rules (Colors, Glass effect, Animations, Responsive Design).
*   **`templates/index.html` (The Skeleton):**
    *   The main HTML page structure.
*   **`data/intents.json`:**
    *   The "textbook" for the local AI. Contains patterns ("Hi", "Hello") and responses ("Hey there!").
*   **`legacy/train_chatbot.py`:**
    *   The script used to teach the local AI new patterns from `intents.json`.

---

## 5. Startup Procedure (VS Code)

To run this project on a new machine or in VS Code:

**1. Open the Folder:**
Open VS Code -> File -> Open Folder -> Select the project folder.

**2. Create Virtual Environment (One time setup):**
```powershell
python -m venv ai_gui_env
```

**3. Activate Environment:**
```powershell
.\ai_gui_env\Scripts\activate
```

**4. Install Dependencies:**
```powershell
pip install flask google-genai nltk numpy pillow
```

**5. Train the Model (If you changed intents.json):**
```powershell
python legacy/train_chatbot.py
```

**6. Run the App:**
```powershell
python app.py
```
*Then open `http://127.0.0.1:5000` in your browser.*

---

## 6. Important Viva Questions & Answers

**Q1: Why did you use two different AIs (Hybrid)?**
**A:** To balance speed, cost, and capability. The Local AI is instant and free for basic commands (like "Hello" or "What time is it?"), saving API costs. Gemini is used only when superior intelligence is actually needed.

**Q2: How does the Sentiment Analysis work?**
**A:** We use **NLTK VADER**, a rule-based model that checks for positive/negative words. `app.py` calculates a "Compound Score" (-1 to +1).
*   > 0.05 = Positive (Green)
*   < -0.05 = Negative (Red)
*   Else = Neutral (Purple)

**Q3: Why doesn't the Voice features work on all browsers?**
**A:** We use the browser's built-in **Web Speech API**. This relies on the browser engine (Chrome/Edge support it best). It does not require an external heavy library, keeping the app lightweight.

**Q4: What is "Glassmorphism"?**
**A:** It's the design style used in the UI, characterized by translucent backgrounds (like frosted glass), slight borders, and shadows to create depth and hierarchy.

**Q5: How did you handle the API Key security?**
**A:** Currently, it is stored in the code for demonstration, but for production, we would move it to a `.env` file and use `os.getenv()` to keep it secret.

**Q6: What happens if the Gemini API is down?**
**A:** The `app.py` has error handling (try/except blocks). If Gemini fails, the bot will return a fallback message ("I'm having trouble connecting to the brain...") instead of crashing.
