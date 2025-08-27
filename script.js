// js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos do DOM
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const fileInput = document.getElementById('file-input');
    const fileListContainer = document.getElementById('file-list');

    let uploadedFiles = []; // Armazena objetos File
    const apiKey = "AIzaSyAXSx1rNsoFGmF7u5PoKQTZ35WrRq8IZCQ"; // A chave da API será injetada pelo ambiente

    // --- Funções de Manipulação da UI ---

    const addMessageToChat = (message, sender, isLoading = false) => {
        const messageId = `msg-${Date.now()}`;
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex mb-4 ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
        
        let loadingIndicator = isLoading ? '<span class="loading-dots"><span>.</span><span>.</span><span>.</span></span>' : '';
        
        const messageContent = document.createElement('div');
        messageContent.id = messageId;
        // CORREÇÃO DE COR APLICADA AQUI
        messageContent.className = `${sender === 'user' ? 'bg-stone-200 text-stone-800' : 'bg-emerald-100 text-emerald-900'} p-3 rounded-lg max-w-md`;
        messageContent.innerHTML = `<p>${message}${loadingIndicator}</p>`;

        messageDiv.appendChild(messageContent);
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return messageId;
    };

    const updateMessageInChat = (messageId, newMessage) => {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            messageElement.innerHTML = `<p>${newMessage.replace(/\n/g, '<br>')}</p>`;
        }
    };

    const updateFileListUI = () => {
        fileListContainer.innerHTML = '';
        uploadedFiles.forEach((file, index) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex justify-between items-center bg-stone-100 p-2 rounded-md text-sm';
            fileElement.innerHTML = `
                <span class="text-stone-600">${file.name}</span>
                <button data-index="${index}" class="remove-file-btn text-red-500 hover:text-red-700 font-bold text-lg">&times;</button>
            `;
            fileListContainer.appendChild(fileElement);
        });
    };

    // --- Funções de Lógica e API ---

    const fileToBase64 = (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = error => reject(error);
    });

    const callGeminiAPI = async (prompt, files) => {
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${apiKey}`;
        
        const fileParts = await Promise.all(
            files.map(async (file) => {
                const base64Data = await fileToBase64(file);
                return {
                    inlineData: {
                        mimeType: file.type,
                        data: base64Data
                    }
                };
            })
        );

        const payload = {
            contents: [{
                role: "user",
                parts: [{ text: prompt }, ...fileParts]
            }]
        };

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorBody = await response.json();
                throw new Error(`API Error: ${response.status} - ${errorBody.error.message}`);
            }

            const result = await response.json();
            if (result.candidates && result.candidates.length > 0 && result.candidates[0].content.parts.length > 0) {
                return result.candidates[0].content.parts[0].text;
            } else {
                return "Não consegui gerar uma resposta. Verifique os arquivos ou a pergunta e tente novamente.";
            }
        } catch (error) {
            console.error("Erro ao chamar a API Gemini:", error);
            return `Ocorreu um erro: ${error.message}`;
        }
    };
    
    // --- Lógica de Eventos ---

    fileInput.addEventListener('change', (event) => {
        Array.from(event.target.files).forEach(file => uploadedFiles.push(file));
        updateFileListUI();
        fileInput.value = '';
    });

    fileListContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-file-btn')) {
            const indexToRemove = parseInt(event.target.getAttribute('data-index'), 10);
            uploadedFiles.splice(indexToRemove, 1);
            updateFileListUI();
        }
    });

    const sendMessage = async () => {
        const userText = chatInput.value.trim();
        if (userText === '' && uploadedFiles.length === 0) return;

        const filesToSend = [...uploadedFiles];
        let userMessage = userText;
        if (filesToSend.length > 0) {
            userMessage += `<br><br><small class="italic">Anexos: ${filesToSend.map(f => f.name).join(', ')}</small>`;
        }

        addMessageToChat(userMessage, 'user');
        chatInput.value = '';
        uploadedFiles = [];
        updateFileListUI();

        const loadingMessageId = addMessageToChat("Processando...", 'bot', true);
        
        const botResponse = await callGeminiAPI(userText, filesToSend);
        
        updateMessageInChat(loadingMessageId, botResponse);
    };

    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Atualiza a mensagem inicial para usar as novas cores
    const initialBotMessage = document.querySelector('#chat-window .bg-emerald-600');
    if (initialBotMessage) {
        initialBotMessage.classList.remove('bg-emerald-600', 'text-white');
        initialBotMessage.classList.add('bg-emerald-100', 'text-emerald-900');
    }


    console.log("Intranet Genebra com integração Gemini carregada!");
});
