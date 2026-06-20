# 🤖 Hybrid AI Chatbot — Local Neural Network + Gemini API

A hybrid conversational AI system that combines a **custom-built neural network** (trained from scratch using only NumPy — no deep learning libraries) with the **Google Gemini API**, routing each query to the fastest, cheapest path capable of answering it well.

Instant, offline-capable responses for common intents. Full LLM power for everything else. Built with real-time sentiment analysis and voice interaction on top.

---

## 🎯 Why This Project Exists

Most chatbots fall into one of two camps: simple rule-based bots with no real understanding, or cloud LLMs that are slow and expensive for even the simplest "hello." This project bridges that gap with a **confidence-based routing system**:

- If the local neural network is confident (≥75%) → respond instantly, offline, for free
- If it isn't → fall back to Gemini for full reasoning power

The result: common queries respond in **under 50ms** instead of the ~1.5s a cloud API call takes — while still handling complex, open-ended questions through Gemini.

---

## ✨ Features

- 🧠 **Custom Neural Network from Scratch** — feed-forward network with backpropagation, implemented using pure NumPy (no TensorFlow/PyTorch), trained on a Bag-of-Words intent classifier
- ☁️ **Hybrid Local + Cloud Routing** — confidence-threshold system automatically decides between the local model and Google Gemini 1.5 Flash
- 😊 **Real-Time Sentiment Analysis** — NLTK VADER scores conversation tone and dynamically shifts the UI color (green/red/purple) to reflect sentiment
- 🎙️ **Voice Interaction** — full Speech-to-Text and Text-to-Speech support via the Web Speech API
- 🖼️ **AI Image Generation** — integrated with Google's Imagen model for image generation from chat
- 💎 **Glassmorphism UI** — modern, responsive frontend built with vanilla HTML5, CSS3, and JavaScript

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.x, Flask |
| Local ML | NumPy (custom neural network, backpropagation) |
| NLP | NLTK (tokenization, Lancaster stemming, VADER sentiment) |
| Cloud AI | Google Gemini API (text + Imagen for images) |
| Frontend | HTML5, CSS3 (Glassmorphism), JavaScript, Web Speech API |

---

## 📊 Results

- **Local model accuracy:** >90% validation accuracy on trained intents
- **Latency:** <50ms for local responses vs. ~1.5s for cloud API calls
- **Sentiment detection:** >80% correct positive/negative classification in test interactions
- Training: 1000 epochs, batch size 8, on a custom `intents.json` dataset

---

## 🏗️ Architecture

```
User Input
    │
    ▼
Bag-of-Words Vectorization
    │
    ▼
Local Neural Network (NumPy) ── confidence ≥ 75%? ──► Instant Response
    │
    │ confidence < 75%
    ▼
Google Gemini API ──► Generated Response
    │
    ▼
NLTK VADER Sentiment Analysis ──► UI Color Update
```

---

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/mabdullahabrar/AI-CHATBOT.git
cd AI-CHATBOT

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key
# (set GEMINI_API_KEY in your environment or a .env file)

# Run the app
python app.py
```

Then open `http://localhost:5000` in your browser.

---

## 📁 Project Structure

```
AI-CHATBOT/
├── data/                 # intents.json — training data for the local model
├── legacy/               # train_chatbot.py — neural network training script
├── static/               # CSS, JS, frontend assets
├── templates/            # HTML templates
└── app.py                # Flask app & routing logic
```

---

## 🔮 Future Improvements

- Replace Bag-of-Words with TF-IDF or a lightweight embedding layer for better semantic understanding
- Local RAG (Retrieval-Augmented Generation) support to query PDF documents without sending data to the cloud
- Expand intent dataset for broader local coverage

---

## 👤 Author

**Muhammad Abdullah Abrar**
CS Undergraduate, Bahria University Islamabad
[LinkedIn](https://linkedin.com/in/mabdullahabrar) · [GitHub](https://github.com/mabdullahabrar)
