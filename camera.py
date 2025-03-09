#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import base64
import numpy as np
import cv2
from config import Config
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Camera:
    """Camera class for handling video streaming."""
    
    def __init__(self):
        """Initialize the camera with configuration settings."""
        self.config = Config()
        self.lock = Lock()
        self.camera = None
        self.is_running = False
        
        # Try to initialize the camera
        try:
            # Use OpenCV for non-Raspberry Pi systems
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, self.config.CAMERA_FRAMERATE)
                
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
                
            logger.info("OpenCV camera initialized successfully")
            self.is_raspberry_pi = False
            
            self.is_running = True
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.is_running = False
            raise
    
    
    def get_frame(self):
        """Get a frame from the camera and encode it as base64."""
        if not self.is_running:
            return None
        
        with self.lock:
            try:
             
                # Get frame from OpenCV
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("Failed to capture frame from camera")
                    return None
                
                # Add timestamp to the frame
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.8, (0, 255, 255), 2, cv2.LINE_AA)
                
                # Encode the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                
                # Convert to base64 for sending over WebSocket
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                return jpg_as_text
            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                return None
    
    def release(self):
        """Release camera resources."""
        with self.lock:
            if self.is_running:
                try:
                   
                    self.camera.release()
                    
                    self.is_running = False
                    logger.info("Camera resources released")
                except Exception as e:
                    logger.error(f"Error releasing camera resources: {e}")

# For testing the camera module directly
if __name__ == "__main__":
    try:
        camera = Camera()
        print("Camera initialized. Press Ctrl+C to exit.")
        
        # Display frames for testing
        
        while True:
            frame_base64 = camera.get_frame()
            if frame_base64:
                # Decode base64 to display with OpenCV
                jpg_original = base64.b64decode(frame_base64)
                jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
                frame = cv2.imdecode(jpg_as_np, flags=1)
                    
                # Display the frame
                cv2.imshow('Camera Test', frame)
                    
                # Break the loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.03)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if 'camera' in locals():
            camera.release()
        
        if not camera.is_raspberry_pi and cv2.getWindowProperty('Camera Test', cv2.WND_PROP_VISIBLE) >= 0:
            cv2.destroyAllWindows() 