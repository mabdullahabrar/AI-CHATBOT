import os
import tkinter as tk
from tkinter import *
from tkinter import ttk 
from tkinter import filedialog 
import datetime
import json
import threading
from ttkthemes import ThemedTk
from PIL import Image, ImageTk 

# --- Third-party Library Imports ---
try:
    from google import genai
except ImportError:
    print("FATAL ERROR: The 'google-genai' library is required. Please run: pip install google-genai")
    exit()


# --- 0. PREMIUM COLOR SCHEME DEFINITION (OBSIDIAN DARK THEME) ---
BG_COLOR = "#2C313C"        # Deep Charcoal background
CHAT_LOG_BG = "#22252C"     # Slightly darker background for the ChatLog area
BOT_TEXT_COLOR = "#E6EBF2"  # Off-White text for bot/readability
USER_COLOR = "#90CAF9"      # Light Blue for user chat bubbles
INPUT_TEXT_COLOR = "#101010" # Black text for input box
ACCENT_COLOR = "#00FF7F"    # Bright Spring Green for the button


# --- Configuration ---
API_KEY = "Enter you api here" 
MAX_DAILY_QUERIES = 200  
USAGE_FILE = 'usage_tracker.json'
model_name = 'gemini-2.5-flash'


# --- Global Variables ---
chat_session = None
client = None
usage_status_var = None
ChatLog = None
image_path = None 


# --- 1. Client Initialization ---

try:
    client = genai.Client(api_key=API_KEY)
    
    chat_session = client.chats.create(
        model=model_name,
        config=dict(
            system_instruction="You are a helpful and intelligent AI assistant for an AI Lab Project. Remember the user's name and details they provide. You are also capable of analyzing images provided by the user. Keep responses professional, clear, and concise."
        )
    )
    
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini Client. Details: {e}")


# --- 2. Usage Tracking Functions (Unchanged) ---
def check_usage():
    "Reads usage_tracker.json and returns (can_use, current_count, usage_data)."
    today = datetime.date.today().isoformat()
    usage_data = {}
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, 'r') as f:
                usage_data = json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
    if usage_data.get('date') != today:
        usage_data = {'date': today, 'count': 0}
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

def update_usage_display():
    "Updates the usage status label in the GUI."
    global usage_status_var
    if usage_status_var is None: return
    can_use, current_count, _ = check_usage()
    if can_use:
        status_text = f"Usage: {current_count} / {MAX_DAILY_QUERIES} queries used today. | Project: AI Lab Chatbot"
    else:
        status_text = f"LIMIT REACHED: {current_count} queries used. Waiting for tomorrow."
    usage_status_var.set(status_text)


# --- 3. Chat Logic Functions (Multimodal/Threading) ---

def select_image():
    "Opens a file dialog to select an image for multimodal input."
    global image_path
    f_types = [('Jpg Files', '*.jpg'), ('Png Files', '*.png'),('Jpeg Files', '*.jpeg')]
    path = filedialog.askopenfilename(filetypes=f_types)
    if path:
        image_path = path
        display_image_in_chat(path)

def display_image_in_chat(path):
    "Displays a simple marker for the selected image in the chat log."
    try:
        ChatLog.config(state=NORMAL)
        ChatLog.insert(END, "You: [Image Attached] " + os.path.basename(path) + '\n\n', 'user')
        ChatLog.config(state=DISABLED)
        ChatLog.yview(END)
    except Exception as e:
        print(f"Error displaying image in chat log: {e}")


def api_call_thread(user_input, can_use, current_count, usage_data, img_path):
    "Function run in a separate thread for the API call and final display."
    
    if not client or not chat_session:
        response_text = "CRITICAL ERROR: AI service is unavailable (Initialization failed)."
    elif not can_use:
        response_text = f"DAILY LIMIT REACHED: You have hit the {MAX_DAILY_QUERIES} request cap for today. Try again tomorrow."
    else:
        response_text = "API connection failed. Check your key."
        
        try:
            contents = []
            if img_path:
                img = Image.open(img_path)
                contents.append(img)
            contents.append(user_input)
            
            response = chat_session.send_message(contents)
            response_text = response.text
            update_usage(usage_data)
            
        except Exception as e:
            print(f"API Call Error: {e}")
            response_text = f"API Error: {e}. Check key/network."

    ChatLog.config(state=NORMAL)
    try:
        ChatLog.delete("end-3l", END)
    except:
        pass 

    ChatLog.insert(END, "Bot: " + response_text + '\n\n', 'bot') 
    ChatLog.config(state=DISABLED)
    ChatLog.yview(END) 
    
    update_usage_display()

# --- FUNCTION MOVED HERE TO AVOID NAME ERROR ---
def bind_enter_key(event):
    "Event handler to send message when the Enter key is pressed."
    if event.keysym == 'Return':
        chat()
        return "break" # Stops Tkinter from inserting a newline
# --- END FUNCTION MOVE ---

def chat():
    "Starts the API call in a background thread and shows a loading message."
    global image_path
    
    user_input = EntryBox.get("1.0",'end-1c').strip()
    EntryBox.delete("0.0",END)

    if user_input or image_path:
        ChatLog.config(state=NORMAL)
        
        if not user_input and image_path:
            user_input = "Please analyze this image."
        elif user_input and not image_path:
            ChatLog.insert(END, "You: " + user_input + '\n\n', 'user')
        
        ChatLog.insert(END, "Bot: Thinking... Please wait.\n\n", 'system') 
        ChatLog.config(state=DISABLED)
        ChatLog.yview(END) 
        
        can_use, current_count, usage_data = check_usage()
        
        t = threading.Thread(target=api_call_thread, 
                             args=(user_input, can_use, current_count, usage_data, image_path))
        t.start()
        
        image_path = None


# --- 4. Evaluation and Feedback (Unchanged) ---
def show_chat_history():
    "Retrieves and displays the full internal conversation history from the Gemini API."
    history_win = Toplevel()
    history_win.title("Internal Conversation History")
    history_win.geometry("600x400")
    
    history_log = Text(history_win, wrap=WORD, font=('Courier New', 10), bg='#1e1e1e', fg='#00FF7F')
    history_log.pack(fill=BOTH, expand=TRUE)
    
    if not chat_session:
        history_log.insert(END, "Error: Chat session not initialized.")
        return

    history = chat_session.get_history()
    
    formatted_history = "--- Full Gemini API History ---\n\n"
    for message in history:
        text_content = ""
        if message.parts:
            for part in message.parts:
                if hasattr(part, 'text'):
                    text_content += part.text
        
        # FIX: Ensure replacement is outside f-string expression
        padded_text = text_content.replace('\n', '\n  ')
        
        formatted_history += f"[{message.role.upper()}]:\n"
        formatted_history += f"  {padded_text}\n\n"
        
    history_log.insert(END, formatted_history)
    history_log.config(state=DISABLED)


def save_feedback(rating, comment):
    "Saves user satisfaction feedback to a local log file."
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Rating: {rating}/5 | Comment: {comment.strip()}\n"
    
    try:
        with open('feedback_log.txt', 'a') as f:
            f.write(log_entry)
        return "Feedback saved! Thank you."
    except IOError:
        return "Error: Could not save feedback file."


def show_feedback_window():
    "Creates a secondary window for collecting user feedback."
    feedback_win = Toplevel()
    feedback_win.title("Rate Conversational Quality")
    feedback_win.geometry("350x250")
    feedback_win.resizable(FALSE, FALSE)
    feedback_win.configure(bg=BG_COLOR)
    
    Label(feedback_win, text="Rate the last conversation (1-5):", bg=BG_COLOR, font=('Segoe UI', 10, 'bold'), fg=BOT_TEXT_COLOR).pack(pady=10)
    
    rating_var = IntVar(value=5)
    
    scale = Scale(feedback_win, from_=1, to=5, orient=HORIZONTAL, variable=rating_var, length=250, bg=BG_COLOR, troughcolor="#CCCCCC", fg=BOT_TEXT_COLOR)
    scale.pack()
    
    Label(feedback_win, text="Comments (Optional):", bg=BG_COLOR, font=('Segoe UI', 10), fg=BOT_TEXT_COLOR).pack(pady=5)
    comment_entry = Entry(feedback_win, width=40)
    comment_entry.pack()

    def submit_and_close():
        rating = rating_var.get()
        comment = comment_entry.get()
        message = save_feedback(rating, comment)
        
        ChatLog.config(state=NORMAL)
        ChatLog.insert(END, f"Bot: [SYSTEM MESSAGE] {message}\n\n", 'system')
        ChatLog.config(state=DISABLED)
        
        feedback_win.destroy()

    Button(feedback_win, text="Submit Feedback", command=submit_and_close, 
           bg=ACCENT_COLOR, fg="white", bd=0, font=('Segoe UI', 10, 'bold')).pack(pady=10)


# --- 5. Main GUI Setup ---

def main():
    global usage_status_var
    global ChatLog
    global EntryBox
    
    try:
        base = ThemedTk(theme='scidark') 
        base.title("AI Lab Project")
        base.geometry("480x600") 
        base.resizable(width=TRUE, height=TRUE)
        
        # --- Custom Style Configuration ---
        base.style = ttk.Style(base)
        base.style.configure('TFrame', background=BG_COLOR)
        
        usage_status_var = StringVar()
        
        main_frame = ttk.Frame(base, padding="10 10 10 10", style='TFrame')
        main_frame.pack(fill=BOTH, expand=TRUE)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1) 
        
        # --- Menu Bar (History & Feedback) ---
        menubar = Menu(base)
        base.config(menu=menubar)
        options_menu = Menu(menubar, tearoff=0)
        options_menu.add_command(label="Show Chat History", command=show_chat_history)
        options_menu.add_command(label="Submit Feedback", command=show_feedback_window)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        # --- Usage Status Label (Row 0) ---
        usage_label = ttk.Label(main_frame, textvariable=usage_status_var, 
                                font=('Segoe UI', 8, 'italic'), foreground="#888888", 
                                background=BG_COLOR)
        usage_label.grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=0)
        update_usage_display() 

        # --- Chat Log (Row 1, Column 0-1) ---
        ChatLog = Text(main_frame, bd=0, bg=CHAT_LOG_BG, height="8", font=("Segoe UI", 10), 
                       wrap=WORD, relief=FLAT, padx=15, pady=10, fg=BOT_TEXT_COLOR)
        ChatLog.insert(END, "Bot: Hello! I am a powerful Gemini AI assistant. Ask me anything!\n\n")
        ChatLog.config(state=DISABLED)
        ChatLog.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # --- Define Premium Chat Tags for Bubble Effect ---
        ChatLog.tag_configure('user', foreground=USER_COLOR, font=("Segoe UI", 10, 'bold'), 
                              lmargin1=200, lmargin2=200, rmargin=10) 
        ChatLog.tag_configure('bot', foreground=BOT_TEXT_COLOR, font=("Segoe UI", 10), 
                              lmargin1=10, lmargin2=10, rmargin=200)
        ChatLog.tag_configure('system', foreground="#888888", font=("Segoe UI", 10, 'italic'))
        
        # --- Scrollbar (Row 1, Column 2) ---
        scrollbar = ttk.Scrollbar(main_frame, command=ChatLog.yview)
        ChatLog['yscrollcommand'] = scrollbar.set
        scrollbar.grid(row=1, column=2, sticky="ns", pady=5)

        # --- Input Area (Row 2) ---
        input_frame = ttk.Frame(main_frame, style='TFrame')
        input_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        # --- Image Button (Row 2, Column 0 - Premium Icon) ---
        image_button = Button(input_frame, text="📸", command=select_image, 
                              font=("Segoe UI", 16), bg=BG_COLOR, fg=ACCENT_COLOR, 
                              activebackground=BG_COLOR, bd=0, padx=5)
        image_button.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=10)


        # --- Input Box (Row 2, Column 1 - CRITICAL FIX) ---
        EntryBox = Text(input_frame, bd=1, bg="white", height="3", font=("Segoe UI", 10), 
                        wrap=WORD, relief=FLAT, highlightthickness=1, highlightbackground="#555555", fg=INPUT_TEXT_COLOR)
        EntryBox.grid(row=0, column=1, sticky="ew", padx=2, pady=10) 
        EntryBox.bind("<Return>", bind_enter_key) # BIND THE ENTER KEY HERE

        # --- Send Button (Row 2, Column 2 - Guaranteed Visibility) ---
        SendButton = Button(input_frame, text="Send", font=("Segoe UI", 10, 'bold'),
                            bg=ACCENT_COLOR, fg="white", 
                            activebackground="#3e8e41", 
                            bd=0,
                            command=chat) 
        SendButton.grid(row=0, column=2, sticky="nsew", padx=(2, 5), pady=10) 

        base.mainloop()

    except TclError as e:
        print(f"\n--- TKINTER ERROR ---")
        print(f"Failed to launch GUI due to a system error (TclError). Error: {e}")
    except Exception as e:
        print(f"\n--- GENERAL LAUNCH ERROR ---")
        print(f"An unexpected error occurred during GUI launch: {e}")

if __name__ == "__main__":
    main()