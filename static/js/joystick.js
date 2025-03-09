/**
 * AI Four-Wheel Drive Car Control Interface
 * Joystick Controller
 */

// Joystick parameters
const JOYSTICK_UPDATE_INTERVAL = 100; // Send commands every 100ms
const DEAD_ZONE = 0.1; // 10% dead zone - we don't move until beyond this

// Joystick state
let movementJoystickActive = false;
let cameraJoystickActive = false;
let movementJoystickX = 0;
let movementJoystickY = 0;
let cameraJoystickX = 0;
let cameraJoystickY = 0;
let lastDirection = '';
let movementIntervalId = null;
let cameraIntervalId = null;

// Initialize joysticks when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize movement joystick
    const movementJoystick = new Joystick('movement-joystick', handleMovementJoystick);
    
    // Initialize camera joystick
    const cameraJoystick = new Joystick('camera-joystick', handleCameraJoystick);
});

/**
 * Joystick class for handling joystick controls
 */
class Joystick {
    constructor(elementId, callback) {
        this.elementId = elementId;
        this.callback = callback;
        this.container = document.getElementById(elementId);
        this.base = this.container.querySelector('.joystick-base');
        this.handle = this.container.querySelector('.joystick-handle');
        
        this.active = false;
        this.baseRect = this.base.getBoundingClientRect();
        this.baseX = this.baseRect.left + this.baseRect.width / 2;
        this.baseY = this.baseRect.top + this.baseRect.height / 2;
        this.maxDistance = this.baseRect.width / 2 - this.handle.offsetWidth / 2;
        
        this.currentX = 0;
        this.currentY = 0;
        
        this.init();
    }
    
    init() {
        // Center the handle initially
        this.updateHandlePosition(0, 0);
        
        // Mouse events
        this.base.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Touch events
        this.base.addEventListener('touchstart', this.handleTouchStart.bind(this));
        document.addEventListener('touchmove', this.handleTouchMove.bind(this));
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Window resize event
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    handleMouseDown(e) {
        e.preventDefault();
        this.active = true;
        this.baseRect = this.base.getBoundingClientRect();
        this.baseX = this.baseRect.left + this.baseRect.width / 2;
        this.baseY = this.baseRect.top + this.baseRect.height / 2;
        this.maxDistance = this.baseRect.width / 2 - this.handle.offsetWidth / 2;
        this.updateJoystickPosition(e.clientX, e.clientY);
    }
    
    handleMouseMove(e) {
        if (this.active) {
            e.preventDefault();
            this.updateJoystickPosition(e.clientX, e.clientY);
        }
    }
    
    handleMouseUp(e) {
        if (this.active) {
            e.preventDefault();
            this.active = false;
            this.resetHandlePosition();
        }
    }
    
    handleTouchStart(e) {
        e.preventDefault();
        this.active = true;
        this.baseRect = this.base.getBoundingClientRect();
        this.baseX = this.baseRect.left + this.baseRect.width / 2;
        this.baseY = this.baseRect.top + this.baseRect.height / 2;
        this.maxDistance = this.baseRect.width / 2 - this.handle.offsetWidth / 2;
        this.updateJoystickPosition(e.touches[0].clientX, e.touches[0].clientY);
    }
    
    handleTouchMove(e) {
        if (this.active) {
            e.preventDefault();
            this.updateJoystickPosition(e.touches[0].clientX, e.touches[0].clientY);
        }
    }
    
    handleTouchEnd(e) {
        if (this.active) {
            e.preventDefault();
            this.active = false;
            this.resetHandlePosition();
        }
    }
    
    handleResize() {
        this.baseRect = this.base.getBoundingClientRect();
        this.baseX = this.baseRect.left + this.baseRect.width / 2;
        this.baseY = this.baseRect.top + this.baseRect.height / 2;
        this.maxDistance = this.baseRect.width / 2 - this.handle.offsetWidth / 2;
        this.updateHandlePosition(this.currentX, this.currentY);
    }
    
    updateJoystickPosition(clientX, clientY) {
        // Calculate distance from center
        let deltaX = clientX - this.baseX;
        let deltaY = clientY - this.baseY;
        
        // Calculate distance from center
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // Limit distance to max radius
        if (distance > this.maxDistance) {
            const angle = Math.atan2(deltaY, deltaX);
            deltaX = Math.cos(angle) * this.maxDistance;
            deltaY = Math.sin(angle) * this.maxDistance;
        }
        
        // Update handle position
        this.updateHandlePosition(deltaX, deltaY);
        
        // Normalize values to -1 to 1 range
        const normalizedX = deltaX / this.maxDistance;
        const normalizedY = deltaY / this.maxDistance;
        
        // Call the callback with normalized values
        if (this.callback) {
            this.callback(normalizedX, normalizedY);
        }
    }
    
    updateHandlePosition(deltaX, deltaY) {
        this.currentX = deltaX;
        this.currentY = deltaY;
        this.handle.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
    }
    
    resetHandlePosition() {
        this.updateHandlePosition(0, 0);
        
        // Call the callback with zeros
        if (this.callback) {
            this.callback(0, 0);
        }
    }
}

/**
 * Handle movement joystick input
 * @param {number} x - Normalized X position (-1 to 1)
 * @param {number} y - Normalized Y position (-1 to 1)
 */
function handleMovementJoystick(x, y) {
    // Threshold for detecting movement
    const threshold = 0.3;
    
    // Determine direction based on joystick position
    let direction = null;
    
    // Calculate absolute values
    const absX = Math.abs(x);
    const absY = Math.abs(y);
    
    // Check if joystick is in neutral position
    if (absX < threshold && absY < threshold) {
        direction = 'stop';
    }
    // Check if movement is primarily horizontal
    else if (absX > absY) {
        if (x > threshold) {
            direction = 'moveRight';
        } else if (x < -threshold) {
            direction = 'moveLeft';
        }
    }
    // Check if movement is primarily vertical
    else if (absY > absX) {
        if (y < -threshold) {
            direction = 'forward';
        } else if (y > threshold) {
            direction = 'backward';
        }
    }
    // Check for diagonal movement
    else {
        if (x > threshold && y < -threshold) {
            direction = 'forwardRight';
        } else if (x < -threshold && y < -threshold) {
            direction = 'forwardLeft';
        } else if (x > threshold && y > threshold) {
            direction = 'backwardRight';
        } else if (x < -threshold && y > threshold) {
            direction = 'backwardLeft';
        }
    }
    
    // Send movement command to server if direction is determined
    if (direction) {
        socket.emit('movement', { direction, duration: 0.1 });
    }
}

/**
 * Handle camera joystick input
 * @param {number} x - Normalized X position (-1 to 1)
 * @param {number} y - Normalized Y position (-1 to 1)
 */
function handleCameraJoystick(x, y) {
    // Map joystick position to camera angles
    // X: -45 to 45 degrees (horizontal)
    // Y: -10 to 30 degrees (vertical)
    const horizontalAngle = Math.round(x * 45);
    const verticalAngle = Math.round(y * 45);
    
    // Update angle display
    document.getElementById('horizontal-angle').textContent = horizontalAngle + '°';
    document.getElementById('vertical-angle').textContent = verticalAngle + '°';
    
    // Send camera control command to server
    socket.emit('camera_control', {
        horizontal: horizontalAngle,
        vertical: verticalAngle
    });
}

// Initialize joysticks
function initializeJoysticks() {
    // Get DOM elements
    const movementJoystick = document.getElementById('movement-joystick');
    const movementBase = movementJoystick.querySelector('.joystick-base');
    const movementHandle = movementJoystick.querySelector('.joystick-handle');
    
    const cameraJoystick = document.getElementById('camera-joystick');
    const cameraBase = cameraJoystick.querySelector('.joystick-base');
    const cameraHandle = cameraJoystick.querySelector('.joystick-handle');
    
    // Set up movement joystick events
    setupJoystick(movementJoystick, movementBase, movementHandle, 
        (x, y) => { // move callback
            movementJoystickActive = true;
            movementJoystickX = x;
            movementJoystickY = y;
            
            if (!movementIntervalId) {
                movementIntervalId = setInterval(sendMovementCommand, JOYSTICK_UPDATE_INTERVAL);
            }
        },
        () => { // release callback
            movementJoystickActive = false;
            movementJoystickX = 0;
            movementJoystickY = 0;
            
            // Send stop command
            sendMovementCommand('stop');
            
            // Clear interval after stopping
            if (movementIntervalId) {
                clearInterval(movementIntervalId);
                movementIntervalId = null;
            }
        }
    );
    
    // Set up camera joystick events
    setupJoystick(cameraJoystick, cameraBase, cameraHandle, 
        (x, y) => { // move callback
            cameraJoystickActive = true;
            cameraJoystickX = x;
            cameraJoystickY = y;
            
            if (!cameraIntervalId) {
                cameraIntervalId = setInterval(sendCameraCommand, JOYSTICK_UPDATE_INTERVAL);
            }
        },
        () => { // release callback
            cameraJoystickActive = false;
            cameraJoystickX = 0;
            cameraJoystickY = 0;
            
            // Clear interval
            if (cameraIntervalId) {
                clearInterval(cameraIntervalId);
                cameraIntervalId = null;
            }
        }
    );
}

// Set up joystick events - works for both touch and mouse
function setupJoystick(joystickElement, baseElement, handleElement, moveCallback, releaseCallback) {
    const baseRect = baseElement.getBoundingClientRect();
    const baseRadius = baseRect.width / 2;
    const handleRadius = handleElement.offsetWidth / 2;
    const maxDistance = baseRadius - handleRadius;
    
    let isDragging = false;
    
    // Get the center point of the joystick base
    function getBaseCenter() {
        const rect = baseElement.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
    }
    
    // Calculate joystick position and process movement
    function processJoystickPosition(clientX, clientY) {
        const center = getBaseCenter();
        
        // Calculate the distance from center
        let deltaX = clientX - center.x;
        let deltaY = clientY - center.y;
        
        // Calculate the distance from center (Pythagorean theorem)
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // Normalize to -1 to 1 range
        let normalizedX = deltaX / maxDistance;
        let normalizedY = deltaY / maxDistance;
        
        // If outside the max distance, scale back
        if (distance > maxDistance) {
            normalizedX = (normalizedX * maxDistance) / distance;
            normalizedY = (normalizedY * maxDistance) / distance;
            
            // Recalculate deltaX and deltaY for handle positioning
            deltaX = normalizedX * maxDistance;
            deltaY = normalizedY * maxDistance;
        }
        
        // Apply dead zone
        if (Math.abs(normalizedX) < DEAD_ZONE) normalizedX = 0;
        if (Math.abs(normalizedY) < DEAD_ZONE) normalizedY = 0;
        
        // Move handle
        handleElement.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        
        // Call the move callback with normalized coordinates
        moveCallback(normalizedX, normalizedY);
    }
    
    // Mouse events
    joystickElement.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isDragging = true;
        processJoystickPosition(e.clientX, e.clientY);
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            e.preventDefault();
            processJoystickPosition(e.clientX, e.clientY);
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            handleElement.style.transform = 'translate(0px, 0px)';
            releaseCallback();
        }
    });
    
    // Touch events for mobile
    joystickElement.addEventListener('touchstart', (e) => {
        e.preventDefault();
        isDragging = true;
        processJoystickPosition(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: false });
    
    document.addEventListener('touchmove', (e) => {
        if (isDragging) {
            e.preventDefault();
            processJoystickPosition(e.touches[0].clientX, e.touches[0].clientY);
        }
    }, { passive: false });
    
    document.addEventListener('touchend', () => {
        if (isDragging) {
            isDragging = false;
            handleElement.style.transform = 'translate(0px, 0px)';
            releaseCallback();
        }
    });
    
    // Safari specific fixes
    joystickElement.addEventListener('touchcancel', () => {
        if (isDragging) {
            isDragging = false;
            handleElement.style.transform = 'translate(0px, 0px)';
            releaseCallback();
        }
    });
}

// Send movement command based on joystick position
function sendMovementCommand(overrideDirection = null) {
    if (!movementJoystickActive && !overrideDirection) return;
    
    let direction;
    
    if (overrideDirection) {
        direction = overrideDirection;
    } else {
        // Calculate movement direction based on joystick position
        const x = movementJoystickX;
        const y = -movementJoystickY; // Invert Y so up is positive
        
        if (Math.abs(x) < DEAD_ZONE && Math.abs(y) < DEAD_ZONE) {
            direction = 'stop';
        } else if (Math.abs(y) > Math.abs(x)) {
            // More vertical than horizontal movement
            if (y > 0) {
                // Forward
                if (x > 0.5) direction = 'forwardRight';
                else if (x < -0.5) direction = 'forwardLeft';
                else direction = 'forward';
            } else {
                // Backward
                if (x > 0.5) direction = 'backwardRight';
                else if (x < -0.5) direction = 'backwardLeft';
                else direction = 'backward';
            }
        } else {
            // More horizontal than vertical movement
            if (x > 0) direction = 'right';
            else direction = 'left';
        }
    }
    
    // Only send if different from last direction
    if (direction !== lastDirection) {
        lastDirection = direction;
        socket.emit('movement', { direction });
    }
}

// Send camera control commands
function sendCameraCommand() {
    if (!cameraJoystickActive) return;
    
    // Map joystick position to camera angles
    const horizontalAngle = Math.round(cameraJoystickX * 45); // -45 to 45 degrees
    const verticalAngle = Math.round(-cameraJoystickY * 20); // -20 to 20 degrees
    
    socket.emit('camera_control', {
        horizontal: horizontalAngle,
        vertical: verticalAngle
    });
}

// Export functions
window.initializeJoysticks = initializeJoysticks; 