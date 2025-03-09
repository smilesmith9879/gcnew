/**
 * AI Four-Wheel Drive Car Control Interface
 * Camera Handler
 */

// This file is intentionally minimal as most camera functionality
// is handled directly in main.js for simplicity.
// This file can be expanded for more complex camera processing if needed.

// Start the camera stream
function startCamera() {
    if (socket) {
        socket.emit('start_stream');
        console.log('Camera stream started');
    }
}

// Stop the camera stream
function stopCamera() {
    if (socket) {
        socket.emit('stop_stream');
        console.log('Camera stream stopped');
    }
}

// Update the video feed with a new frame
function updateVideoFeed(frameData) {
    const videoFeed = document.getElementById('video-feed');
    if (videoFeed && frameData) {
        videoFeed.src = 'data:image/jpeg;base64,' + frameData;
    }
} 