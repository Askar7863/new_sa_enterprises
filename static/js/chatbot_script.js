// static/js/chatbot_script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Chatbot Logic ---
    const chatWindow = document.getElementById('chat-window');
    const userMessageInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-button');

    // Set the timestamp for the initial bot message on load
    const initialBotTimestamp = document.getElementById('initial-bot-timestamp');
    if (initialBotTimestamp) {
        initialBotTimestamp.textContent = new Date().toLocaleTimeString();
    }

    /**
     * Adds a message to the chat window.
     * @param {string} message - The message content.
     * @param {string} sender - 'user' or 'bot' to apply appropriate styling.
     */
    function addMessageToChat(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleTimeString()}</span>`;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the latest message
    }

    /**
     * Sends a user message to the chatbot backend and displays the response.
     */
    async function sendMessage() {
        const userMessage = userMessageInput.value.trim();
        if (userMessage === '') return; // Don't send empty messages

        addMessageToChat(userMessage, 'user');
        userMessageInput.value = ''; // Clear input field

        try {
            const response = await fetch('/company-chatbot/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userMessage })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            addMessageToChat(data.response, 'bot');
        } catch (error) {
            console.error('Error sending message to chatbot:', error);
            addMessageToChat("Oops! It seems there was an issue communicating with the assistant. Please try again later.", 'bot');
        }
    }

    // Event listeners for chatbot interaction
    sendButton.addEventListener('click', sendMessage);

    userMessageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // --- Report Section Logic ---
    const reportForm = document.getElementById('report-form');
    const reportSubjectInput = document.getElementById('report-subject');
    const reportDescriptionTextarea = document.getElementById('report-description');
    const reportStatusDiv = document.getElementById('report-status');

    /**
     * Displays a temporary status message for report submission.
     * @param {string} message - The message to display.
     * @param {string} type - 'success' or 'error' to apply appropriate styling.
     */
    function showStatusMessage(message, type) {
        reportStatusDiv.textContent = message;
        reportStatusDiv.className = `status-message ${type}`; // Add type class
        reportStatusDiv.style.display = 'block';
        setTimeout(() => {
            reportStatusDiv.style.display = 'none';
            reportStatusDiv.textContent = '';
            reportStatusDiv.className = 'status-message'; // Reset class
        }, 5000); // Hide after 5 seconds
    }

    // Event listener for report form submission
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default browser form submission

        const subject = reportSubjectInput.value.trim();
        const description = reportDescriptionTextarea.value.trim();

        if (subject === '' || description === '') {
            showStatusMessage('Please fill in both subject and description to submit a report.', 'error');
            return;
        }

        try {
            const response = await fetch('/company-chatbot/api/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ subject, description })
            });

            const data = await response.json();

            if (response.ok) {
                showStatusMessage(data.message, 'success');
                reportForm.reset(); // Clear form fields on successful submission
            } else {
                showStatusMessage(data.error || 'Failed to submit report. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error submitting report:', error);
            showStatusMessage('An unexpected network error occurred while submitting the report. Please check your connection.', 'error');
        }
    });
});
