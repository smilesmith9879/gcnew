#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import time
from LOBOROBOT import LOBOROBOT
from config import Config
from camera import Camera
from voice import VoiceRecognition
from ai_assistant import AIAssistant
from speech import TextToSpeech

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize robot controller
try:
    robot = LOBOROBOT()
    logger.info("Robot controller initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize robot controller: {e}")
    robot = None

# Initialize camera
try:
    camera = Camera()
    logger.info("Camera initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize camera: {e}")
    camera = None

# Initialize voice recognition
try:
    voice = VoiceRecognition()
    logger.info("Voice recognition initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize voice recognition: {e}")
    voice = None

# Initialize AI assistant
try:
    ai_assistant = AIAssistant()
    logger.info("AI assistant initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI assistant: {e}")
    ai_assistant = None

# Initialize text-to-speech
try:
    tts = TextToSpeech()
    logger.info("Text-to-speech initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize text-to-speech: {e}")
    tts = None

# Global variables
current_speed = 50  # Default speed (0-100)
is_streaming = False
streaming_thread = None

@app.route('/')
def index():
    """Render the main web interface."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the robot."""
    status = {
        'robot': robot is not None,
        'camera': camera is not None,
        'voice': voice is not None,
        'ai': ai_assistant is not None,
        'speed': current_speed,
        'streaming': is_streaming
    }
    return jsonify(status)

@app.route('/api/speed', methods=['POST'])
def set_speed():
    """Set the movement speed of the robot."""
    global current_speed
    data = request.json
    if 'speed' in data:
        speed = int(data['speed'])
        if 0 <= speed <= 100:
            current_speed = speed
            return jsonify({'success': True, 'speed': current_speed})
    return jsonify({'success': False, 'message': 'Invalid speed value'}), 400

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'connected': True})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    if robot:
        robot.t_stop(0)  # Stop the robot when client disconnects

@socketio.on('movement')
def handle_movement(data):
    """Handle movement commands from the joystick."""
    if not robot:
        emit('error', {'message': 'Robot controller not available'})
        return
    
    try:
        direction = data.get('direction')
        duration = data.get('duration', 0.1)  # Default duration of 0.1 seconds
        
        if direction == 'forward':
            robot.t_up(current_speed, duration)
        elif direction == 'backward':
            robot.t_down(current_speed, duration)
        elif direction == 'left':
            robot.turnLeft(current_speed, duration)
        elif direction == 'right':
            robot.turnRight(current_speed, duration)
        elif direction == 'moveLeft':
            robot.moveLeft(current_speed, duration)
        elif direction == 'moveRight':
            robot.moveRight(current_speed, duration)
        elif direction == 'forwardLeft':
            robot.forward_Left(current_speed, duration)
        elif direction == 'forwardRight':
            robot.forward_Right(current_speed, duration)
        elif direction == 'backwardLeft':
            robot.backward_Left(current_speed, duration)
        elif direction == 'backwardRight':
            robot.backward_Right(current_speed, duration)
        elif direction == 'stop':
            robot.t_stop(duration)
        else:
            emit('error', {'message': f'Unknown direction: {direction}'})
            return
        
        emit('movement_status', {'success': True, 'direction': direction})
    except Exception as e:
        logger.error(f"Movement error: {e}")
        emit('error', {'message': f'Movement error: {str(e)}'})

@socketio.on('camera_control')
def handle_camera_control(data):
    """Handle camera gimbal control commands."""
    if not robot:
        emit('error', {'message': 'Robot controller not available'})
        return
    
    try:
        horizontal = data.get('horizontal', 0)  # -45 to 45 degrees
        vertical = data.get('vertical', 0)      # -10 to 30 degrees
        
        # Map the values to the servo channels
        # Assuming channel 12 for horizontal and channel 13 for vertical
        # Adjust the angle mapping as needed
        h_angle = 90 + horizontal  # Center is 90 degrees
        v_angle = 90 + vertical    # Center is 90 degrees
        
        # Set servo angles
        robot.set_servo_angle(9, h_angle)
        robot.set_servo_angle(10, v_angle)
        
        emit('camera_status', {'success': True, 'horizontal': horizontal, 'vertical': vertical})
    except Exception as e:
        logger.error(f"Camera control error: {e}")
        emit('error', {'message': f'Camera control error: {str(e)}'})

@socketio.on('start_stream')
def handle_start_stream():
    """Start the video stream."""
    global is_streaming, streaming_thread
    
    if not camera:
        emit('error', {'message': 'Camera not available'})
        return
    
    if not is_streaming:
        is_streaming = True
        streaming_thread = threading.Thread(target=stream_video)
        streaming_thread.daemon = True
        streaming_thread.start()
        emit('stream_status', {'streaming': True})
    else:
        emit('stream_status', {'streaming': True, 'message': 'Stream already running'})

@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop the video stream."""
    global is_streaming
    
    if is_streaming:
        is_streaming = False
        emit('stream_status', {'streaming': False})
    else:
        emit('stream_status', {'streaming': False, 'message': 'Stream not running'})

def stream_video():
    """Stream video frames to connected clients."""
    global is_streaming
    
    while is_streaming:
        if camera:
            try:
                frame = camera.get_frame()
                socketio.emit('video_frame', {'frame': frame})
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                logger.error(f"Video streaming error: {e}")
                socketio.emit('error', {'message': f'Video streaming error: {str(e)}'})
                is_streaming = False
                break

@socketio.on('voice_command')
def handle_voice_command(data):
    """Process voice commands."""
    if not voice or not ai_assistant:
        emit('error', {'message': 'Voice recognition or AI assistant not available'})
        return
    
    try:
        audio_data = data.get('audio')
        if audio_data:
            # Process the audio data with voice recognition
            text = voice.recognize(audio_data)
            
            if text:
                # Process the recognized text with AI assistant
                response = ai_assistant.process_command(text)
                response_text = response.get('text', '')
                
                # Execute command if applicable
                if 'command' in response:
                    command = response['command']
                    if command.get('type') == 'movement':
                        handle_movement({'direction': command.get('direction')})
                    elif command.get('type') == 'camera':
                        handle_camera_control({
                            'horizontal': command.get('horizontal', 0),
                            'vertical': command.get('vertical', 0)
                        })
                
                # Use text-to-speech to speak the response
                if tts:
                    tts.speak(response_text)
                
                emit('voice_response', {
                    'success': True,
                    'text': text,
                    'response': response_text,
                    'tts_available': tts is not None
                })
            else:
                emit('voice_response', {'success': False, 'message': 'Could not recognize speech'})
        else:
            emit('voice_response', {'success': False, 'message': 'No audio data received'})
    except Exception as e:
        logger.error(f"Voice command error: {e}")
        emit('error', {'message': f'Voice command error: {str(e)}'})

@socketio.on('text_command')
def handle_text_command(data):
    """Process text commands."""
    if not ai_assistant:
        emit('error', {'message': 'AI assistant not available'})
        return
    
    try:
        text = data.get('text')
        if text:
            # Process the text with AI assistant
            response = ai_assistant.process_command(text)
            response_text = response.get('text', '')
            
            # Execute command if applicable
            if 'command' in response:
                command = response['command']
                if command.get('type') == 'movement':
                    handle_movement({'direction': command.get('direction')})
                elif command.get('type') == 'camera':
                    handle_camera_control({
                        'horizontal': command.get('horizontal', 0),
                        'vertical': command.get('vertical', 0)
                    })
            
            # Use text-to-speech to speak the response
            if tts:
                tts.speak(response_text)
            
            emit('text_response', {
                'success': True,
                'response': response_text,
                'tts_available': tts is not None
            })
        else:
            emit('text_response', {'success': False, 'message': 'No text received'})
    except Exception as e:
        logger.error(f"Text command error: {e}")
        emit('error', {'message': f'Text command error: {str(e)}'})

# Add a new endpoint to toggle text-to-speech
@socketio.on('toggle_tts')
def handle_toggle_tts(data):
    """Toggle text-to-speech on/off."""
    enabled = data.get('enabled', True)
    message = "Text-to-speech enabled" if enabled else "Text-to-speech disabled"
    
    # Here you could store the state in a global variable if needed
    # global tts_enabled
    # tts_enabled = enabled
    
    emit('tts_status', {
        'success': True,
        'enabled': enabled,
        'message': message
    })

if __name__ == '__main__':
    try:
        # Start the Flask-SocketIO server
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        if robot:
            robot.t_stop(0)  # Stop the robot
        if camera:
            camera.release()  # Release camera resources 