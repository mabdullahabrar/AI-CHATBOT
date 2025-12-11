# train_chatbot.py (Hybrid AI with Pure NumPy)

import nltk
import json
import numpy as np
import pickle
from nltk.stem.lancaster import LancasterStemmer

# --- NLTK Checks ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    
stemmer = LancasterStemmer()

# --- Load Data ---
try:
    with open('data/intents.json') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: 'data/intents.json' not found.")
    exit()

words = []
labels = []
docs_x = []
docs_y = []

for intent in data['intents']:
    for pattern in intent['patterns']:
        wrds = nltk.word_tokenize(pattern) 
        words.extend(wrds)
        docs_x.append(wrds)
        docs_y.append(intent['tag'])
    if intent['tag'] not in labels:
        labels.append(intent['tag'])

words = [stemmer.stem(w.lower()) for w in words if w not in "?!."]
words = sorted(list(set(words)))
labels = sorted(labels)

training = []
output = []
out_empty = [0] * len(labels)

for x, doc in enumerate(docs_x):
    bag = []
    wrds = [stemmer.stem(w.lower()) for w in doc]
    for w in words:
        bag.append(1) if w in wrds else bag.append(0)
    output_row = list(out_empty)
    output_row[labels.index(docs_y[x])] = 1
    training.append(bag)
    output.append(output_row)

X = np.array(training)
y = np.array(output)

# --- Pure NumPy Neural Network ---
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    return x * (1 - x)

# Architecture: Input -> Hidden (12 neurons) -> Output
input_neurons = len(X[0])
hidden_neurons = 12
output_neurons = len(y[0])

# Initialize weights randomly
np.random.seed(42)
weights_input_hidden = 2 * np.random.random((input_neurons, hidden_neurons)) - 1
weights_hidden_output = 2 * np.random.random((hidden_neurons, output_neurons)) - 1

# Training
epochs = 20000
learning_rate = 0.1

print("Training Pure NumPy Neural Network...")
for epoch in range(epochs):
    # Forward Propagation
    hidden_layer_input = np.dot(X, weights_input_hidden)
    hidden_layer_output = sigmoid(hidden_layer_input)
    
    output_layer_input = np.dot(hidden_layer_output, weights_hidden_output)
    predicted_output = sigmoid(output_layer_input)
    
    # Backpropagation
    error = y - predicted_output
    d_predicted_output = error * sigmoid_derivative(predicted_output)
    
    error_hidden_layer = d_predicted_output.dot(weights_hidden_output.T)
    d_hidden_layer = error_hidden_layer * sigmoid_derivative(hidden_layer_output)
    
    # Update Weights
    weights_hidden_output += hidden_layer_output.T.dot(d_predicted_output) * learning_rate
    weights_input_hidden += X.T.dot(d_hidden_layer) * learning_rate

    if epoch % 5000 == 0:
        print(f"Epoch {epoch}: Error {np.mean(np.abs(error))}")

print("Training complete.")

# Save weights
model_data = {
    'weights_input_hidden': weights_input_hidden,
    'weights_hidden_output': weights_hidden_output,
    'input_neurons': input_neurons,
    'hidden_neurons': hidden_neurons,
    'output_neurons': output_neurons
}

with open("data/chatbot_model.pkl", "wb") as f:
    pickle.dump(model_data, f)

pickle.dump({'words':words, 'labels':labels, 'data':data}, open("data/training_data.pkl", "wb"))
print("Model saved to data/chatbot_model.pkl")
