import os
import datetime
import json
import threading
import pickle
import numpy as np
import nltk
from nltk.stem.lancaster import LancasterStemmer
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from PIL import Image
import io
import base64

# --- Configuration ---
API_KEY = "Enter your api key"
MAX_DAILY_QUERIES = 200
USAGE_FILE = 'data/usage_tracker.json'
FEEDBACK_FILE = 'data/feedback_log.txt'
MODEL_NAME = 'gemini-2.5-flash'
IMAGEN_MODEL = 'imagen-4.0-fast-generate-001'

app = Flask(__name__)

# --- NLTK Resource Check (Prevent Runtime Errors) ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# --- Sentiment Analysis Setup ---
from nltk.sentiment.vader import SentimentIntensityAnalyzer
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

# --- Global Variables ---
chat_session = None
client = None

# --- 1. Client Initialization ---
try:
    client = genai.Client(api_key=API_KEY)
    
    today_date = datetime.date.today().strftime("%B %d, %Y")
    
    chat_session = client.chats.create(
        model=MODEL_NAME,
        config=dict(
            system_instruction=(
                f"Current Date: {today_date}. "
                "You are a helpful and intelligent AI assistant for an AI Lab Project. "
                "Remember the user's name and details they provide. "
                "You are also capable of analyzing images provided by the user. "
                "Keep responses professional, clear, and concise. "
                "IMPORTANT: If the user explicitly asks you to GENERATE or CREATE an image, drawing, or picture, "
                "you must NOT refuse. Instead, you must reply with a special command format. "
                "Reply with EXACTLY the string 'GENERATE_IMAGE: ' followed by a detailed descriptive prompt for the image. "
                "For example: 'GENERATE_IMAGE: A futuristic city skyline at sunset in a cyberpunk style.' "
                "Do not add any other text when using this command."
            )
        )
    )
    print("Gemini Client Initialized Successfully.")
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini Client. Details: {e}")


# --- 2. Usage Tracking Functions ---
def check_usage():
    "Reads usage_tracker.json and returns (can_use, current_count, usage_data)."
    today = datetime.date.today().isoformat()
    usage_data = {'date': today, 'count': 0}
    
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, 'r') as f:
                loaded_data = json.load(f)
                if loaded_data.get('date') == today:
                    usage_data = loaded_data
        except (IOError, json.JSONDecodeError):
            pass
            
    current_count = usage_data['count']
    can_use = current_count < MAX_DAILY_QUERIES
    return can_use, current_count, usage_data

def update_usage(usage_data):
    "Increments the counter and saves to usage_tracker.json."
    usage_data['count'] += 1
    try:
        with open(USAGE_FILE, 'w') as f:
            json.dump(usage_data, f)
    except IOError as e:
        print(f"ERROR: Could not save usage tracker file: {e}")

# --- 3. Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/usage')
def get_usage():
    can_use, current_count, _ = check_usage()
    return jsonify({
        'can_use': can_use,
        'current_count': current_count,
        'max_queries': MAX_DAILY_QUERIES,
        'status_text': f"Usage: {current_count} / {MAX_DAILY_QUERIES} queries used today." if can_use else f"LIMIT REACHED: {current_count} queries used."
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    global chat_session
    
    if not client or not chat_session:
        return jsonify({'response': "CRITICAL ERROR: AI service is unavailable.", 'error': True})

    user_input = request.form.get('message', '').strip()
    image_file = request.files.get('image')

    # --- Sentiment Analysis ---
    sentiment_score = sia.polarity_scores(user_input)
    compound = sentiment_score['compound']
    sentiment_label = "neutral"
    if compound >= 0.05:
        sentiment_label = "positive"
    elif compound <= -0.05:
        sentiment_label = "negative"

    # --- 1. Local AI Check (Pure NumPy Hybrid Mode) ---
    try:
        # Check for image first, if image exists skip local AI
        if not image_file and user_input:
            if os.path.exists("data/chatbot_model.pkl"):
                # Lazy load to ensure we get fresh data
                with open("data/chatbot_model.pkl", "rb") as f:
                    model_weights = pickle.load(f)
                with open("data/training_data.pkl", "rb") as f:
                    training_data = pickle.load(f)
                    words = training_data['words']
                    labels = training_data['labels']
                    intents_local = training_data['data']
                
                stemmer = LancasterStemmer()
                
                # Tokenize & Stem
                s_words = nltk.word_tokenize(user_input)
                s_words = [stemmer.stem(word.lower()) for word in s_words]

                # Bag of Words
                bag = [0] * len(words)
                for s in s_words:
                    for i, w in enumerate(words):
                        if w == s:
                            bag[i] = 1
                
                # Forward Prop (Sigmoid)
                def sigmoid(x): return 1 / (1 + np.exp(-x))
                
                input_layer = np.array([bag])
                hidden_layer_input = np.dot(input_layer, model_weights['weights_input_hidden'])
                hidden_layer_output = sigmoid(hidden_layer_input)
                output_layer_input = np.dot(hidden_layer_output, model_weights['weights_hidden_output'])
                predicted_output = sigmoid(output_layer_input)
                
                results = predicted_output[0]
                result_index = np.argmax(results)
                confidence = results[result_index]
                
                # Threshold Check (> 0.70)
                if confidence > 0.70:
                    tag = labels[result_index]
                    
                    # --- Special Dynamic Tags ---
                    if tag == "time":
                        current_time = datetime.datetime.now().strftime("%I:%M %p")
                        response = f"The current time is {current_time}."
                        return jsonify({'response': f"[Local AI]: {response}", 'error': False, 'sentiment': sentiment_label})
                        
                    elif tag == "date":
                        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
                        response = f"Today is {current_date}."
                        return jsonify({'response': f"[Local AI]: {response}", 'error': False, 'sentiment': sentiment_label})

                    # --- Standard Tags ---
                    for intent in intents_local['intents']:
                        if intent['tag'] == tag:
                            response = np.random.choice(intent['responses'])
                            
                            # Standard Usage Update
                            can_use, current_count, usage_data = check_usage()
                            if can_use:
                                update_usage(usage_data)
                            
                            return jsonify({'response': f"[Local AI]: {response}", 'error': False, 'sentiment': sentiment_label})
    except Exception as e:
        print(f"Local AI Exception: {e}")

    # --- 2. Cloud AI (Gemini) ---
    can_use, current_count, usage_data = check_usage()
    if not can_use:
        return jsonify({'response': f"DAILY LIMIT REACHED: You have hit the {MAX_DAILY_QUERIES} request cap for today.", 'error': True})

    contents = []
    
    try:
        if image_file:
            # Convert uploaded file to PIL Image
            img_bytes = image_file.read()
            img = Image.open(io.BytesIO(img_bytes))
            contents.append(img)
            if not user_input:
                user_input = "Please analyze this image." # Default prompt if only image sent

        if user_input:
            contents.append(user_input)

        if not contents:
             return jsonify({'response': "Please provide text or an image.", 'error': True})

        response = chat_session.send_message(contents)
        response_text = response.text
        
        # Check for Image Generation Command
        if response_text.startswith("GENERATE_IMAGE:"):
            image_prompt = response_text.replace("GENERATE_IMAGE:", "").strip()
            print(f"Attempting to generate image with prompt: {image_prompt}")
            
            try:
                # Call Imagen API
                imagen_response = client.models.generate_images(
                    model=IMAGEN_MODEL,
                    prompt=image_prompt,
                    config=dict(number_of_images=1)
                )
                
                # Get image bytes
                generated_image = imagen_response.generated_images[0]
                img_bytes = generated_image.image.image_bytes
                
                # Encode to base64
                b64_img = base64.b64encode(img_bytes).decode('utf-8')
                image_data = f"data:image/png;base64,{b64_img}"
                
                response_text = f"I've generated an image for you based on: '{image_prompt}'"
                
                update_usage(usage_data)
                return jsonify({'response': response_text, 'image_data': image_data, 'error': False, 'sentiment': sentiment_label})

            except Exception as img_err:
                print(f"Image Generation Error: {img_err}")
                error_msg = str(img_err)
                if "billed users" in error_msg or "400" in error_msg:
                    response_text = "I'm sorry, but I cannot generate images right now because the AI service requires a paid account for this specific feature. I can still help you with text and image analysis!"
                elif "404" in error_msg:
                    response_text = "I'm sorry, but the image generation model is currently unavailable or not found."
                else:
                    response_text = f"I tried to generate that image, but encountered an error: {error_msg}"

        update_usage(usage_data)
        return jsonify({'response': response_text, 'error': False, 'sentiment': sentiment_label})

    except Exception as e:
        print(f"API Call Error: {e}")
        return jsonify({'response': f"API Error: {str(e)}", 'error': True})
        
@app.route('/api/history')
def get_history():
    if not chat_session:
         return jsonify({'history': []})
    
    try:
        history_data = []
        for message in chat_session.get_history():
            text_content = ""
            if message.parts:
                for part in message.parts:
                    if hasattr(part, 'text'):
                        text_content += part.text
            history_data.append({
                'role': message.role,
                'text': text_content
            })
        return jsonify({'history': history_data})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/feedback', methods=['POST'])
def save_feedback():
    data = request.json
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Rating: {rating}/5 | Comment: {comment.strip()}\n"
    
    try:
        with open(FEEDBACK_FILE, 'a') as f:
            f.write(log_entry)
        return jsonify({'message': "Feedback saved! Thank you."})
    except IOError:
        return jsonify({'message': "Error: Could not save feedback file.", 'error': True})

if __name__ == '__main__':
    # Ensure static/templates/data folders exist if not already
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, port=5000)
