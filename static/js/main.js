/**
 * AI Four-Wheel Drive Car Control Interface
 * Main JavaScript file
 */

// Initialize socket connection
const socket = io();

// DOM elements
const videoFeed = document.getElementById('video-feed');
const speedSlider = document.getElementById('speed-slider');
const speedValue = document.getElementById('speed-value');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const voiceButton = document.getElementById('voice-button');
const chatMessages = document.getElementById('chat-messages');
const voiceIndicator = document.getElementById('voice-indicator');

// Status elements
const robotStatus = document.getElementById('robot-status');
const cameraStatus = document.getElementById('camera-status');
const voiceStatus = document.getElementById('voice-status');
const aiStatus = document.getElementById('ai-status');

// Global variables
let isConnected = false;
let isStreaming = false;
let currentSpeed = 50;
let isChatVisible = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize the application
function initializeApp() {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize socket events
    setupSocketEvents();
    
    // Get initial status
    fetchStatus();
    
    // Add placeholder image for video feed
    videoFeed.src = videoFeed.src || 'static/img/placeholder.jpg';
    
    console.log('Application initialized');
}

// Set up event listeners
function setupEventListeners() {
    // Speed slider
    speedSlider.addEventListener('input', handleSpeedChange);
    
    // Chat input
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextCommand();
        }
    });
    
    // Send button
    sendButton.addEventListener('click', sendTextCommand);
    
    // Voice button
    voiceButton.addEventListener('click', toggleVoiceRecording);
    
    // Chat messages toggle
    chatInput.addEventListener('focus', () => {
        toggleChatMessages(true);
    });
    
    // Close chat when clicking outside
    document.addEventListener('click', (e) => {
        if (isChatVisible && 
            !chatMessages.contains(e.target) && 
            !chatInput.contains(e.target) && 
            e.target !== sendButton) {
            toggleChatMessages(false);
        }
    });
}

// Set up socket events
function setupSocketEvents() {
    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
        isConnected = true;
        updateStatus('robot', true);
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isConnected = false;
        updateStatus('robot', false);
        updateStatus('camera', false);
        updateStatus('voice', false);
        updateStatus('ai', false);
    });
    
    // Status events
    socket.on('status', (data) => {
        console.log('Status update:', data);
        if (data.robot !== undefined) updateStatus('robot', data.robot);
        if (data.camera !== undefined) updateStatus('camera', data.camera);
        if (data.voice !== undefined) updateStatus('voice', data.voice);
        if (data.ai !== undefined) updateStatus('ai', data.ai);
    });
    
    // Video frame events
    socket.on('video_frame', (data) => {
        if (data.frame) {
            videoFeed.src = 'data:image/jpeg;base64,' + data.frame;
        }
    });
    
    // Voice response events
    socket.on('voice_response', (data) => {
        console.log('Voice response:', data);
        if (data.success) {
            addMessage('user', data.text);
            addMessage('system', data.response);
        } else {
            addMessage('system', data.message || 'Error processing voice command');
        }
    });
    
    // Text response events
    socket.on('text_response', (data) => {
        console.log('Text response:', data);
        if (data.success) {
            addMessage('system', data.response);
        } else {
            addMessage('system', data.message || 'Error processing text command');
        }
    });
    
    // Error events
    socket.on('error', (data) => {
        console.error('Socket error:', data);
        addMessage('system', 'Error: ' + (data.message || 'Unknown error'));
    });
    
    // Stream status events
    socket.on('stream_status', (data) => {
        console.log('Stream status:', data);
        isStreaming = data.streaming;
        updateStatus('camera', isStreaming);
    });
}

// Fetch initial status from the server
function fetchStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            console.log('Initial status:', data);
            updateStatus('robot', data.robot);
            updateStatus('camera', data.camera);
            updateStatus('voice', data.voice);
            updateStatus('ai', data.ai);
            
            // Update speed
            if (data.speed !== undefined) {
                currentSpeed = data.speed;
                speedSlider.value = currentSpeed;
                speedValue.textContent = currentSpeed;
            }
            
            // Start video stream if available
            if (data.camera && !isStreaming) {
                startVideoStream();
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

// Update status indicators
function updateStatus(type, isConnected) {
    const element = document.getElementById(`${type}-status`);
    if (element) {
        element.textContent = isConnected ? 'Connected' : 'Disconnected';
        element.className = isConnected ? 'connected' : 'disconnected';
    }
}

// Handle speed change
function handleSpeedChange() {
    currentSpeed = parseInt(speedSlider.value);
    speedValue.textContent = currentSpeed;
    
    // Send speed update to server
    fetch('/api/speed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ speed: currentSpeed })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Speed updated:', data);
    })
    .catch(error => {
        console.error('Error updating speed:', error);
    });
}

// Start video stream
function startVideoStream() {
    if (!isStreaming) {
        socket.emit('start_stream');
    }
}

// Stop video stream
function stopVideoStream() {
    if (isStreaming) {
        socket.emit('stop_stream');
    }
}

// Send text command
function sendTextCommand() {
    const text = chatInput.value.trim();
    if (text) {
        // Add user message to chat
        addMessage('user', text);
        
        // Send command to server
        socket.emit('text_command', { text });
        
        // Clear input
        chatInput.value = '';
    }
}

// Toggle chat messages visibility
function toggleChatMessages(show) {
    isChatVisible = show !== undefined ? show : !isChatVisible;
    
    if (isChatVisible) {
        chatMessages.classList.add('active');
    } else {
        chatMessages.classList.remove('active');
    }
}

// Add message to chat
function addMessage(type, text) {
    const messageContainer = document.querySelector('.message-container');
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    messageContainer.appendChild(message);
    
    // Show chat messages
    toggleChatMessages(true);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Toggle voice recording
function toggleVoiceRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// Start voice recording
function startRecording() {
    if (isRecording) return;
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        addMessage('system', 'Voice recording is not supported in this browser');
        return;
    }
    
    // Request microphone access
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            isRecording = true;
            
            // Show recording indicator
            voiceIndicator.classList.add('active');
            voiceButton.style.backgroundColor = '#f44336';
            
            // Create media recorder
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            // Handle data available event
            mediaRecorder.ondataavailable = (e) => {
                audioChunks.push(e.data);
            };
            
            // Handle recording stop event
            mediaRecorder.onstop = () => {
                // Convert audio chunks to blob
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                
                // Convert blob to base64
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64Audio = reader.result.split(',')[1];
                    
                    // Send audio to server
                    socket.emit('voice_command', { audio: base64Audio });
                    
                    // Add user message to chat
                    addMessage('user', '🎤 Voice command sent');
                };
                
                // Reset recording state
                isRecording = false;
                voiceIndicator.classList.remove('active');
                voiceButton.style.backgroundColor = '';
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            // Start recording
            mediaRecorder.start();
            
            // Stop recording after 5 seconds
            setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 5000);
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            addMessage('system', 'Error accessing microphone: ' + error.message);
        });
}

// Stop voice recording
function stopRecording() {
    if (!isRecording || !mediaRecorder) return;
    
    if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// Handle window unload
window.addEventListener('beforeunload', () => {
    // Stop video stream
    stopVideoStream();
    
    // Disconnect socket
    if (socket) {
        socket.disconnect();
    }
}); 