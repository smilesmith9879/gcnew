/**
 * AI Four-Wheel Drive Car Control Interface
 * Joystick Controller
 */

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
    const verticalAngle = Math.round(y * 20);
    
    // Update angle display
    document.getElementById('horizontal-angle').textContent = horizontalAngle + '°';
    document.getElementById('vertical-angle').textContent = verticalAngle + '°';
    
    // Send camera control command to server
    socket.emit('camera_control', {
        horizontal: horizontalAngle,
        vertical: verticalAngle
    });
} 