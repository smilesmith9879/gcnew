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
const ttsButton = document.getElementById('tts-button');

// Settings modal elements
const settingsButton = document.getElementById('settings-button');
const settingsModal = document.getElementById('settings-modal');
const closeButton = document.querySelector('.close-button');
const requestPermissionButton = document.getElementById('request-permission-button');
const permissionStatus = document.getElementById('permission-status');
const permissionInstructions = document.getElementById('permission-instructions');
const connectionStatus = document.getElementById('connection-status');
const httpsInstructions = document.getElementById('https-instructions');
const browserInstructions = document.getElementById('browser-instructions');

// TTS settings elements
const speechRateSlider = document.getElementById('speech-rate');
const speechRateValue = document.getElementById('speech-rate-value');
const speechVolumeSlider = document.getElementById('speech-volume');
const speechVolumeValue = document.getElementById('speech-volume-value');
const speechLanguageSelect = document.getElementById('speech-language');
const testTtsButton = document.getElementById('test-tts-button');
const testTtsChineseButton = document.getElementById('test-tts-chinese-button');

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
let ttsEnabled = true;
let micPermissionState = 'unknown'; // unknown, granted, denied, prompt
let speechRate = 130; // Default speech rate
let speechVolume = 200; // Default speech volume (max)
let speechLanguage = 'auto'; // Default language (auto-detect)

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
    
    // Check microphone permissions
    checkMicrophonePermission();
    
    // Check HTTPS connection
    checkHttpsConnection();
    
    // Check browser type and set instructions
    updateBrowserInstructions();
    
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
    
    // TTS button
    ttsButton.addEventListener('click', toggleTTS);
    
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
    
    // Settings button
    settingsButton.addEventListener('click', openSettingsModal);
    
    // Close button in settings modal
    closeButton.addEventListener('click', closeSettingsModal);
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeSettingsModal();
        }
    });
    
    // Request permission button
    requestPermissionButton.addEventListener('click', requestMicrophonePermission);
    
    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsModal.classList.contains('active')) {
            closeSettingsModal();
        }
    });
    
    // Speech rate slider
    speechRateSlider.addEventListener('input', handleSpeechRateChange);
    
    // Speech volume slider
    speechVolumeSlider.addEventListener('input', handleSpeechVolumeChange);
    
    // Speech language select
    speechLanguageSelect.addEventListener('change', handleSpeechLanguageChange);
    
    // Test TTS button
    testTtsButton.addEventListener('click', testTts);
    
    // Test Chinese TTS button
    testTtsChineseButton.addEventListener('click', testTtsChinese);
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
    
    // AI ready event
    socket.on('ai_ready', (data) => {
        console.log('AI ready event received:', data);
        
        // Show a notification about DeepSeek being ready
        if (data.message) {
            // Add AI ready message to chat with a robot icon
            addMessage('system', `🤖 ${data.message}`);
            
            // Make the AI status indicator pulse briefly to show it's ready
            const aiStatus = document.getElementById('ai-status');
            if (aiStatus) {
                aiStatus.classList.add('pulse-animation');
                setTimeout(() => {
                    aiStatus.classList.remove('pulse-animation');
                }, 3000);
            }
            
            // Show chat messages to ensure the user sees the notification
            toggleChatMessages(true);
            
            // After a short delay, allow the chat to be dismissed automatically
            setTimeout(() => {
                // Only auto-hide if user hasn't interacted with chat
                if (!chatInput.matches(':focus')) {
                    toggleChatMessages(false);
                }
            }, 5000);
        }
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
    
    // TTS status events
    socket.on('tts_status', (data) => {
        console.log('TTS status:', data);
        if (data.success) {
            addMessage('system', data.message);
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
    
    // TTS settings events
    socket.on('tts_settings', (data) => {
        console.log('TTS settings received:', data);
        
        // Update UI
        if (data.speech_rate !== undefined) {
            speechRate = data.speech_rate;
            speechRateSlider.value = speechRate;
            speechRateValue.textContent = speechRate;
        }
        
        if (data.speech_volume !== undefined) {
            speechVolume = data.speech_volume;
            speechVolumeSlider.value = speechVolume;
            const volumePercent = Math.round((speechVolume / 200) * 100);
            speechVolumeValue.textContent = volumePercent + '%';
        }
        
        if (data.language !== undefined) {
            speechLanguage = data.language;
            speechLanguageSelect.value = speechLanguage;
        }
    });
    
    // TTS test response
    socket.on('tts_test', (data) => {
        console.log('TTS test response:', data);
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
        // Show a notification about microphone access
        addMessage('system', 'Please allow microphone access when prompted');
        
        // Check if we're on HTTPS (required for Safari)
        if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            addMessage('system', 'Voice recording requires a secure connection (HTTPS). Please contact the administrator.');
            return;
        }
        
        // For Safari, we need to initiate recording with direct user interaction
        startRecording();
    }
}

// Start voice recording with enhanced permission handling
function startRecording() {
    if (isRecording) return;
    
    // Check for secure connection
    const isSecure = window.location.protocol === 'https:' || 
                    window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1';
    
    if (!isSecure) {
        addMessage('system', 'Voice recording requires a secure connection (HTTPS). This is a security requirement, especially for Safari browsers.');
        openSettingsModal(); // Show settings with HTTPS instructions
        return;
    }
    
    // Detect if we're on iOS Safari specifically
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    const isIOSSafari = isIOS && isSafari;
    
    console.log('Browser detection:', { isIOS, isSafari, isIOSSafari });
    
    // Add Safari-specific styling if needed
    if (isIOSSafari) {
        voiceButton.classList.add('safari-mode');
    }
    
    // Check if browser supports necessary APIs
    if (!navigator.mediaDevices) {
        console.log('No mediaDevices API available');
        // Some browsers (especially older Safari versions) need this polyfill
        navigator.mediaDevices = {};
    }
    
    if (!navigator.mediaDevices.getUserMedia) {
        console.log('No getUserMedia method available, trying fallbacks');
        navigator.mediaDevices.getUserMedia = function(constraints) {
            // First, try the older vendor-prefixed versions
            const getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
            
            // If no prefixed versions exist, reject with error
            if (!getUserMedia) {
                console.error('No getUserMedia implementation available');
                addMessage('system', 'Voice recording is not supported in this browser');
                return Promise.reject(new Error('getUserMedia is not implemented in this browser'));
            }
            
            // Otherwise, wrap the old API with a Promise
            return new Promise(function(resolve, reject) {
                getUserMedia.call(navigator, constraints, resolve, reject);
            });
        };
    }
    
    // Safari requires simpler constraints
    const constraints = { audio: true };
    
    // Show a visual indicator that we're trying to access the microphone
    voiceButton.classList.add('requesting');
    
    // Special Safari instruction
    if (isIOSSafari) {
        addMessage('system', 'Safari requires permission to access your microphone. Please tap "Allow" when prompted.');
    }
    
    console.log('Requesting microphone access with constraints:', constraints);
    
    // Request microphone access
    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            // Permission was granted
            micPermissionState = 'granted';
            
            console.log('Microphone access granted');
            isRecording = true;
            
            // Hide the requesting indicator
            voiceButton.classList.remove('requesting');
            
            // Show recording indicator
            voiceIndicator.classList.add('active');
            voiceButton.style.backgroundColor = '#f44336';
            
            try {
                // For Safari, use simple initialization without MIME types
                if (isIOSSafari) {
                    console.log('Using Safari-specific MediaRecorder initialization');
                    mediaRecorder = new MediaRecorder(stream);
                } else {
                    // For other browsers, try to detect supported MIME types
                    console.log('Detecting supported MIME types');
                    let options = {};
                    
                    if (MediaRecorder.isTypeSupported) {
                        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                            options = { mimeType: 'audio/webm;codecs=opus' };
                        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                            options = { mimeType: 'audio/webm' };
                        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                            options = { mimeType: 'audio/mp4' };
                        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
                            options = { mimeType: 'audio/ogg' };
                        }
                    }
                    
                    console.log('Using options:', options);
                    mediaRecorder = new MediaRecorder(stream, options);
                }
            } catch (e) {
                console.error('MediaRecorder initialization error:', e);
                
                // Try without options as a last resort
                try {
                    console.log('Trying MediaRecorder without options');
                    mediaRecorder = new MediaRecorder(stream);
                } catch (err) {
                    console.error('MediaRecorder fallback error:', err);
                    stopRecording();
                    addMessage('system', 'Your browser does not support audio recording. Please try a different browser.');
                    return;
                }
            }
            
            console.log('MediaRecorder initialized successfully');
            audioChunks = [];
            
            // Handle data available event
            mediaRecorder.ondataavailable = (e) => {
                console.log('Audio data available:', e.data.size, 'bytes');
                if (e.data && e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };
            
            // Handle recording stop event
            mediaRecorder.onstop = () => {
                console.log('Recording stopped, processing', audioChunks.length, 'chunks');
                
                // Check if we have audio data
                if (audioChunks.length === 0 || (audioChunks.length === 1 && audioChunks[0].size === 0)) {
                    console.error('No audio data recorded');
                    addMessage('system', 'No audio data recorded. Please try again.');
                    
                    // Reset recording state
                    isRecording = false;
                    voiceIndicator.classList.remove('active');
                    voiceButton.style.backgroundColor = '';
                    
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                    return;
                }
                
                // Try to determine the appropriate MIME type
                let mimeType = 'audio/webm';
                if (audioChunks[0].type) {
                    mimeType = audioChunks[0].type;
                }
                
                console.log('Creating audio blob with MIME type:', mimeType);
                // Convert audio chunks to blob
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                console.log('Audio blob created, size:', audioBlob.size, 'bytes');
                
                // Convert blob to base64
                audioToBase64(audioBlob)
                    .then(base64Audio => {
                        console.log('Audio converted to base64, length:', base64Audio.length);
                        // Send audio to server
                        socket.emit('voice_command', { audio: base64Audio });
                        
                        // Add user message to chat
                        addMessage('user', '🎤 Voice command sent');
                    })
                    .catch(error => {
                        console.error('Error converting audio to base64:', error);
                        addMessage('system', 'Error processing audio: ' + error.message);
                    });
                
                // Reset recording state
                isRecording = false;
                voiceIndicator.classList.remove('active');
                voiceButton.style.backgroundColor = '';
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            // Start recording with special handling for Safari
            console.log('Starting MediaRecorder');
            
            // Safari sometimes works better with requestData
            if (isIOSSafari) {
                mediaRecorder.start(100); // Request data every 100ms for Safari
            } else {
                mediaRecorder.start();
            }
            
            console.log('MediaRecorder state:', mediaRecorder.state);
            
            // Stop recording after 5 seconds
            setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    console.log('Stopping recording after timeout');
                    mediaRecorder.stop();
                }
            }, 5000);
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            
            // Hide the requesting indicator
            voiceButton.classList.remove('requesting');
            voiceButton.classList.remove('safari-mode');
            
            // Show a more user-friendly error message with instructions
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                micPermissionState = 'denied';
                
                // Show specific instructions for iOS
                if (isIOS) {
                    const message = 'Microphone access was denied. Please go to Settings → Safari → Camera & Microphone Access, and enable access for this site.';
                    addMessage('system', message);
                    
                    // Open settings modal to show detailed instructions
                    openSettingsModal();
                } else {
                    addMessage('system', 'Microphone access was denied. Please check your browser settings and ensure microphone access is allowed for this site.');
                    
                    // Open settings modal to show detailed instructions
                    openSettingsModal();
                }
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                addMessage('system', 'No microphone found. Please connect a microphone and try again.');
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                addMessage('system', 'Could not access microphone. It may be in use by another application.');
            } else if (error.name === 'SecurityError') {
                addMessage('system', 'Security error when accessing microphone. This site must be accessed via HTTPS.');
                
                // Open settings modal to show HTTPS instructions
                openSettingsModal();
            } else {
                addMessage('system', 'Error accessing microphone: ' + error.message);
            }
            
            // Update permission status in case modal is open
            checkMicrophonePermission();
        });
}

// Stop voice recording
function stopRecording() {
    if (!isRecording || !mediaRecorder) return;
    
    // Remove Safari mode indicator
    voiceButton.classList.remove('safari-mode');
    
    if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// Toggle text-to-speech
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    
    // Update button appearance
    if (ttsEnabled) {
        ttsButton.classList.add('active');
    } else {
        ttsButton.classList.remove('active');
    }
    
    // Send toggle to server
    socket.emit('toggle_tts', { enabled: ttsEnabled });
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

// Open the settings modal
function openSettingsModal() {
    settingsModal.classList.add('active');
    
    // Refresh statuses when opening modal
    fetchStatus();
    
    // Refresh permission status when opening modal
    checkMicrophonePermission();
    checkHttpsConnection();
    updateBrowserInstructions();
    
    // Get current TTS settings from server
    socket.emit('get_tts_settings');
}

// Close the settings modal
function closeSettingsModal() {
    settingsModal.classList.remove('active');
}

// Check microphone permission status
function checkMicrophonePermission() {
    if (!navigator.permissions || !navigator.permissions.query) {
        // Browser doesn't support permissions API
        permissionStatus.textContent = 'Unable to check microphone permission status';
        permissionStatus.className = 'status-warning';
        updatePermissionInstructions('unknown');
        return;
    }
    
    navigator.permissions.query({ name: 'microphone' })
        .then(permissionStatus => {
            micPermissionState = permissionStatus.state;
            
            switch(permissionStatus.state) {
                case 'granted':
                    updatePermissionStatus('Microphone access is allowed', 'success');
                    break;
                case 'denied':
                    updatePermissionStatus('Microphone access is blocked', 'error');
                    break;
                case 'prompt':
                    updatePermissionStatus('Microphone permission not yet requested', 'warning');
                    break;
                default:
                    updatePermissionStatus('Unknown permission state', 'warning');
            }
            
            updatePermissionInstructions(permissionStatus.state);
            
            // Listen for permission changes
            permissionStatus.onchange = function() {
                checkMicrophonePermission();
            };
        })
        .catch(error => {
            console.error('Error checking permission:', error);
            permissionStatus.textContent = 'Unable to check microphone permission status';
            permissionStatus.className = 'status-warning';
            updatePermissionInstructions('unknown');
        });
}

// Update permission status display
function updatePermissionStatus(message, type) {
    permissionStatus.textContent = message;
    permissionStatus.className = 'status-' + type;
}

// Update permission instructions based on state
function updatePermissionInstructions(state) {
    let instructions = '';
    
    switch(state) {
        case 'granted':
            instructions = 'You have allowed microphone access. Voice commands are enabled.';
            requestPermissionButton.disabled = true;
            break;
        case 'denied':
            instructions = `
                <strong>Microphone access is blocked.</strong> To enable voice commands:
                <ol>
                    <li>Click the lock/info icon in your browser's address bar</li>
                    <li>Look for "Microphone" permissions and change to "Allow"</li>
                    <li>Refresh this page after changing the setting</li>
                </ol>
                <p>On Safari iOS: Go to Settings → Safari → Camera & Microphone Access → Find this website and allow</p>
            `;
            requestPermissionButton.disabled = false;
            break;
        case 'prompt':
            instructions = 'Click the "Request Microphone Access" button below to enable voice commands.';
            requestPermissionButton.disabled = false;
            break;
        default:
            instructions = `
                <strong>Your browser may require manual microphone permission.</strong>
                <p>If voice recording doesn't work, check your browser's site settings and ensure microphone access is allowed for this site.</p>
                <p>Click the button below to try requesting permission.</p>
            `;
            requestPermissionButton.disabled = false;
    }
    
    permissionInstructions.innerHTML = instructions;
}

// Request microphone permission explicitly
function requestMicrophonePermission() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        addMessage('system', 'Your browser does not support microphone access.');
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Permission granted
            updatePermissionStatus('Microphone access is now allowed', 'success');
            updatePermissionInstructions('granted');
            
            // Stop the tracks to release the microphone
            stream.getTracks().forEach(track => track.stop());
            
            addMessage('system', 'Microphone access granted successfully! You can now use voice commands.');
        })
        .catch(error => {
            console.error('Error requesting microphone permission:', error);
            
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                updatePermissionStatus('Microphone access was denied', 'error');
                updatePermissionInstructions('denied');
                addMessage('system', 'Microphone access was denied. Please check browser settings.');
            } else {
                updatePermissionStatus('Error accessing microphone', 'error');
                addMessage('system', 'Error accessing microphone: ' + error.message);
            }
        });
}

// Check if connection is HTTPS
function checkHttpsConnection() {
    const isSecure = window.location.protocol === 'https:' || 
                     window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1';
    
    if (isSecure) {
        connectionStatus.textContent = 'Secure connection established';
        connectionStatus.className = 'status-success';
        httpsInstructions.innerHTML = 'Your connection is secure. Voice recording is available.';
    } else {
        connectionStatus.textContent = 'Insecure connection detected';
        connectionStatus.className = 'status-error';
        httpsInstructions.innerHTML = `
            <strong>Safari requires HTTPS for voice recording.</strong>
            <p>Voice recording is disabled because this site is not accessed over HTTPS.</p>
            <p>Please contact the administrator to enable HTTPS, or access this site with a secure URL starting with https://</p>
        `;
        
        // Disable voice button if not secure
        voiceButton.disabled = true;
        voiceButton.title = 'Voice recording requires HTTPS';
        voiceButton.classList.add('disabled');
    }
}

// Update browser-specific instructions
function updateBrowserInstructions() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    const isIOSSafari = isIOS && isSafari;
    const isChrome = /chrome/i.test(navigator.userAgent) && !/edge|edg/i.test(navigator.userAgent);
    const isFirefox = /firefox/i.test(navigator.userAgent);
    const isEdge = /edge|edg/i.test(navigator.userAgent);
    
    let instructions = '<strong>Browser detected: ';
    
    if (isIOSSafari) {
        instructions += 'Safari on iOS</strong>';
        instructions += `
            <ul>
                <li>Safari on iOS requires HTTPS for microphone access</li>
                <li>If permission was denied: Go to Settings → Safari → Camera & Microphone Access</li>
                <li>Find this website in the list and toggle to allow microphone access</li>
                <li>Return to this page and refresh</li>
            </ul>
        `;
    } else if (isSafari) {
        instructions += 'Safari on macOS</strong>';
        instructions += `
            <ul>
                <li>Safari requires HTTPS for microphone access</li>
                <li>Click Safari → Preferences → Websites → Microphone</li>
                <li>Find this website and select "Allow"</li>
            </ul>
        `;
    } else if (isChrome) {
        instructions += 'Google Chrome</strong>';
        instructions += `
            <ul>
                <li>Click the lock/info icon in the address bar</li>
                <li>Select "Site settings"</li>
                <li>Find "Microphone" and change to "Allow"</li>
            </ul>
        `;
    } else if (isFirefox) {
        instructions += 'Firefox</strong>';
        instructions += `
            <ul>
                <li>Click the lock/info icon in the address bar</li>
                <li>Click "Connection secure" → "More Information" → "Permissions"</li>
                <li>Find "Use the Microphone" and change to "Allow"</li>
            </ul>
        `;
    } else if (isEdge) {
        instructions += 'Microsoft Edge</strong>';
        instructions += `
            <ul>
                <li>Click the lock/info icon in the address bar</li>
                <li>Select "Site permissions"</li>
                <li>Find "Microphone" and change to "Allow"</li>
            </ul>
        `;
    } else {
        instructions += 'Other browser</strong>';
        instructions += `
            <ul>
                <li>Check your browser settings to allow microphone access for this site</li>
                <li>Look for site permissions or privacy settings in your browser menu</li>
            </ul>
        `;
    }
    
    browserInstructions.innerHTML = instructions;
}

// Handle speech rate change
function handleSpeechRateChange() {
    speechRate = parseInt(speechRateSlider.value);
    speechRateValue.textContent = speechRate;
    
    // Send updated settings to server
    updateTtsSettings();
}

// Handle speech volume change
function handleSpeechVolumeChange() {
    speechVolume = parseInt(speechVolumeSlider.value);
    const volumePercent = Math.round((speechVolume / 200) * 100);
    speechVolumeValue.textContent = volumePercent + '%';
    
    // Send updated settings to server
    updateTtsSettings();
}

// Handle speech language change
function handleSpeechLanguageChange() {
    speechLanguage = speechLanguageSelect.value;
    
    // Send updated settings to server
    updateTtsSettings();
}

// Test text-to-speech with current settings
function testTts() {
    socket.emit('test_tts', {
        speech_rate: speechRate,
        speech_volume: speechVolume,
        language: speechLanguage
    });
    
    addMessage('system', 'Testing text-to-speech with current settings...');
}

// Test Chinese text-to-speech specifically
function testTtsChinese() {
    socket.emit('test_tts', {
        speech_rate: speechRate,
        speech_volume: speechVolume,
        language: 'zh',
        text: "这是中文语音合成测试。当前的语音速度和音量设置已应用。"
    });
    
    addMessage('system', '正在测试中文语音合成...');
}

// Update TTS settings on server
function updateTtsSettings() {
    socket.emit('update_tts_settings', {
        speech_rate: speechRate,
        speech_volume: speechVolume,
        language: speechLanguage
    });
} 