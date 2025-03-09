/**
 * AI Four-Wheel Drive Car Control Interface
 * Voice Recording Handler
 */

// This file is intentionally minimal as most voice recording functionality
// is handled directly in main.js for simplicity.
// This file can be expanded for more complex voice processing if needed.

// Check if browser supports audio recording
function checkVoiceSupport() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Voice recording is not supported in this browser');
        return false;
    }
    return true;
}

// Convert audio blob to base64
function audioToBase64(audioBlob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            resolve(base64Audio);
        };
        reader.onerror = reject;
        reader.readAsDataURL(audioBlob);
    });
} 