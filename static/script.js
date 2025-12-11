document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const clearImageBtn = document.getElementById('clear-image');
    const usageBarFill = document.getElementById('usage-bar-fill');
    const usageText = document.getElementById('usage-text');

    // Modal elements
    const historyModal = document.getElementById('history-modal');
    const feedbackModal = document.getElementById('feedback-modal');
    const btnHistory = document.getElementById('btn-history');
    const btnFeedback = document.getElementById('btn-feedback');
    const closeModals = document.querySelectorAll('.close-modal');
    const submitFeedbackBtn = document.getElementById('submit-feedback');
    const stars = document.querySelectorAll('.star-rating i');
    let currentRating = 5;

    // --- Usage Stats ---
    function updateUsage() {
        if (!usageBarFill) return;
        fetch('/api/usage')
            .then(res => res.json())
            .then(data => {
                const percentage = (data.current_count / data.max_queries) * 100;
                usageBarFill.style.width = `${percentage}%`;
                usageText.innerText = data.status_text;

                if (!data.can_use) {
                    usageBarFill.style.backgroundColor = 'red';
                    userInput.disabled = true;
                    userInput.placeholder = "Daily limit reached.";
                }
            })
            .catch(err => console.error("Usage update failed:", err));
    }
    updateUsage();

    // --- Chat Logic ---
    function appendMessage(text, type, imgUrl = null) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', type === 'user' ? 'user-message' : 'bot-message');

        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('avatar');
        avatarDiv.innerHTML = type === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('bubble');

        if (imgUrl) {
            const img = document.createElement('img');
            img.src = imgUrl;
            img.classList.add('chat-image');
            bubbleDiv.appendChild(img);
        }

        if (text) {
            const textNode = document.createTextNode(text);
            bubbleDiv.appendChild(textNode);
        }

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);

        // --- NEW: Per-Message Speaker Button (Bot Only) ---
        if (type === 'bot' && text) {
            const speakBtn = document.createElement('button');
            speakBtn.className = 'msg-speak-btn';
            speakBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
            speakBtn.title = "Read Aloud";
            speakBtn.onclick = () => speak(text);
            msgDiv.appendChild(speakBtn);
        }

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const text = userInput.value.trim();
        const file = imageUpload.files[0];

        if (!text && !file) return;

        let imgUrl = null;
        if (file) {
            imgUrl = URL.createObjectURL(file);
        }
        appendMessage(text, 'user', imgUrl);

        const formData = new FormData();
        formData.append('message', text);
        if (file) {
            formData.append('image', file);
        }

        userInput.value = '';
        clearImage();

        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot-message', 'loading-msg');
        loadingDiv.innerHTML = `<div class="avatar"><i class="fa-solid fa-robot"></i></div><div class="bubble"><i class="fa-solid fa-circle-notch fa-spin"></i> Thinking...</div>`;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        fetch('/api/chat', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                loadingDiv.remove();

                if (data.error) {
                    appendMessage("Error: " + data.response, 'bot');
                } else {
                    let formattedResponse = data.response;
                    appendMessage(formattedResponse, 'bot');

                    if (data.sentiment) {
                        handleSentiment(data.sentiment);
                    }

                    if (data.image_data) {
                        appendMessage("Generated Image:", 'bot', data.image_data);
                    }
                }
                updateUsage();
            })
            .catch(err => {
                loadingDiv.remove();
                appendMessage("Network Error: " + err, 'bot');
            });
    }

    // --- TTS Logic (Simplified) ---
    function speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();

            // Text Cleaning
            let cleanText = text.replace(/[*_#`~]/g, '');
            let tempDiv = document.createElement("div");
            tempDiv.innerHTML = cleanText;
            cleanText = tempDiv.textContent || tempDiv.innerText || "";

            const utterance = new SpeechSynthesisUtterance(cleanText);
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v =>
                v.name.includes("Google US English") ||
                v.name.includes("Microsoft Zira") ||
                v.name.includes("Samantha")
            );
            if (preferredVoice) utterance.voice = preferredVoice;

            utterance.pitch = 1.0;
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        } else {
            console.error("TTS not supported");
            alert("Text-to-Speech is not supported in this browser.");
        }
    }

    // Voice Loading Hook
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = () => {
            console.log("Voices loaded");
        };
    }

    // --- Sentiment UI ---
    function handleSentiment(sentiment) {
        const root = document.documentElement;
        if (sentiment === 'positive') {
            root.style.setProperty('--accent-color', '#22c55e'); // Green
            root.style.setProperty('--accent-glow', 'rgba(34, 197, 94, 0.5)');
            root.style.setProperty('--user-msg-bg', 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)');
        } else if (sentiment === 'negative') {
            root.style.setProperty('--accent-color', '#ef4444'); // Red
            root.style.setProperty('--accent-glow', 'rgba(239, 68, 68, 0.5)');
            root.style.setProperty('--user-msg-bg', 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)');
        } else {
            root.style.setProperty('--accent-color', '#6366f1');
            root.style.setProperty('--accent-glow', 'rgba(99, 102, 241, 0.5)');
            root.style.setProperty('--user-msg-bg', 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                imagePreview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });

    function clearImage() {
        imageUpload.value = '';
        imagePreview.classList.add('hidden');
        previewImg.src = '';
    }

    clearImageBtn.addEventListener('click', clearImage);

    // --- Modals ---
    btnHistory.addEventListener('click', () => {
        historyModal.style.display = 'block';
        const contentDiv = document.getElementById('history-content');
        contentDiv.innerText = "Loading...";

        fetch('/api/history')
            .then(res => res.json())
            .then(data => {
                if (data.history && data.history.length > 0) {
                    contentDiv.innerHTML = "";
                    data.history.forEach(msg => {
                        const p = document.createElement('div');
                        p.innerHTML = `<strong>[${msg.role.toUpperCase()}]</strong>: ${msg.text}<br><br>`;
                        contentDiv.appendChild(p);
                    });
                } else {
                    contentDiv.innerText = "No history found or error loading.";
                }
            });
    });

    btnFeedback.addEventListener('click', () => {
        feedbackModal.style.display = 'block';
    });

    closeModals.forEach(span => {
        span.addEventListener('click', () => {
            historyModal.style.display = 'none';
            feedbackModal.style.display = 'none';
        });
    });

    window.onclick = (event) => {
        if (event.target == historyModal) historyModal.style.display = 'none';
        if (event.target == feedbackModal) feedbackModal.style.display = 'none';
    };

    // Rating Logic
    stars.forEach(star => {
        star.addEventListener('click', () => {
            currentRating = star.getAttribute('data-rating');
            updateStars(currentRating);
        });
    });

    function updateStars(rating) {
        stars.forEach(star => {
            if (star.getAttribute('data-rating') <= rating) {
                star.classList.remove('fa-solid');
                star.classList.add('fa-solid');
                star.style.color = '#ffd700';
            } else {
                star.classList.remove('fa-solid');
                star.classList.add('fa-regular');
                star.style.color = 'white';
            }
        });
    }

    submitFeedbackBtn.addEventListener('click', () => {
        const comment = document.getElementById('feedback-comment').value;
        fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating: currentRating, comment: comment })
        })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                feedbackModal.style.display = 'none';
            });
    });

    // --- Speech to Text ---
    const micBtn = document.getElementById('mic-btn');
    let recognition;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            micBtn.classList.add('listening');
            userInput.placeholder = "Listening...";
        };

        recognition.onend = () => {
            micBtn.classList.remove('listening');
            userInput.placeholder = "Type a message...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value += (userInput.value ? ' ' : '') + transcript;
            userInput.focus();
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            micBtn.classList.remove('listening');
            userInput.placeholder = "Error. Try again.";
        };

        micBtn.addEventListener('click', () => {
            if (micBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    } else {
        micBtn.style.display = 'none';
        console.log("Web Speech API not supported.");
    }
});
