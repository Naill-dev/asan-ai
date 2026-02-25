// Chat JavaScript - ASAN AI Assistant

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    const orgSelector = document.getElementById('orgSelector');
    const clearChatBtn = document.getElementById('clearChat');

    // Quick actions buttons (əgər varsa)
    const quickButtons = document.querySelectorAll('.quick-btn');

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = message ${sender};
        
        const time = new Date().toLocaleTimeString('az-AZ', { hour: '2-digit', minute: '2-digit' });
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content user-content">
                    <div class="message-text">${text}</div>
                    <span class="message-time">${time}</span>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content">
                    <div class="message-text">${text.replace(/\n/g, '<br>')}</div>
                    <span class="message-time">${time}</span>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        addMessage(message, 'user');
        userInput.value = '';
        
        typingIndicator.style.display = 'flex';
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    org_id: orgSelector ? orgSelector.value : 'asan_xidmet'
                })
            });
            
            const data = await response.json();
            typingIndicator.style.display = 'none';
            addMessage(data.answer, 'bot');
        } catch (error) {
            typingIndicator.style.display = 'none';
            addMessage('Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.', 'bot');
            console.error('Error:', error);
        }
    }

    // Event listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // Quick buttons
    if (quickButtons) {
        quickButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                userInput.value = btn.dataset.question;
                sendMessage();
            });
        });
    }

    // Clear chat
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            chatMessages.innerHTML = '';
            addMessage('Salam! Mən ASAN AI köməkçisiyəm. Sizə necə kömək edə bilərəm?', 'bot');
            
            // Quick actions-ı yenidən əlavə et (əgər index.html-də varsa)
            const quickActions = document.querySelector('.quick-actions');
            if (quickActions) {
                chatMessages.appendChild(quickActions.cloneNode(true));
            }
        });
    }

    // Organisation dəyişəndə xəbərdarlıq
    if (orgSelector) {
        orgSelector.addEventListener('change', () => {
            addMessage(Siz ${orgSelector.options[orgSelector.selectedIndex].text} üçün sorğu verə bilərsiniz., 'bot');
        });
    }

    // Feedback üçün (əlavə)
    window.rateMessage = function(messageId, rating) {
        fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message_id: messageId, rating: rating })
        });
    };
});
