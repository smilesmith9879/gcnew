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
    
    # Check if the model is ready
    if ai_assistant.is_model_ready():
        logger.info("DeepSeek R1 model is ready")
    else:
        logger.warning("DeepSeek R1 model is not fully ready yet")
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
ai_ready_announced = False  # Flag to track if we've announced AI readiness
ai_ready_check_thread = None  # Thread for checking AI readiness

# TTS settings with defaults
tts_settings = {
    'speech_rate': 130,
    'speech_volume': 200,
    'language': 'auto'  # 'auto', 'en', or 'zh'
}

# Function to announce AI readiness
def announce_ai_ready():
    global ai_ready_announced
    if ai_ready_announced:
        return
    
    ai_ready_announced = True
    ready_message = "Hello, I am ready."
    logger.info("Announcing AI ready: " + ready_message)
    
    # Speak the ready message (with is_announcement=True)
    if tts:
        try:
            # Use slightly slower rate for the announcement for better clarity
            announcement_rate = 120  # Even slower than the default 130
            tts.speak(
                ready_message, 
                is_announcement=True, 
                speech_rate=announcement_rate,
                speech_volume=tts_settings['speech_volume'],
                language='en'  # Always use English for system announcement
            )
        except Exception as e:
            logger.error(f"Error announcing AI ready via speech: {e}")
    
    # Send the ready message to all connected clients
    try:
        socketio.emit('ai_ready', {
            'message': ready_message
        })
    except Exception as e:
        logger.error(f"Error sending AI ready event: {e}")

# Function to periodically check if AI is ready
def check_ai_ready_task():
    global ai_ready_announced
    
    logger.info("Starting background task to check AI readiness")
    
    # Check every 5 seconds for up to 2 minutes (24 checks)
    for i in range(24):
        # If we've already announced or there's no AI assistant, stop checking
        if ai_ready_announced or not ai_assistant:
            break
            
        # Check if the model is ready
        if ai_assistant.is_model_ready():
            logger.info(f"DeepSeek R1 model is now ready after {i * 5} seconds")
            announce_ai_ready()
            break
            
        # Wait 5 seconds before next check
        time.sleep(5)
    
    logger.info("Completed background AI readiness check task")

# Start the AI ready check in the background
if ai_assistant and not ai_assistant.is_model_ready() and not ai_ready_announced:
    ai_ready_check_thread = threading.Thread(target=check_ai_ready_task)
    ai_ready_check_thread.daemon = True
    ai_ready_check_thread.start()
    logger.info("Started background thread to check for AI readiness")

@app.route('/')
def index():
    """Render the main web interface."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the robot."""
    global ai_ready_announced
    
    # Check if AI is ready but hasn't been announced yet
    if ai_assistant and ai_assistant.is_model_ready() and not ai_ready_announced:
        # Schedule the announcement to happen shortly after this request
        socketio.start_background_task(announce_ai_ready)
    
    status = {
        'robot': robot is not None,
        'camera': camera is not None,
        'voice': voice is not None,
        'ai': ai_assistant is not None and ai_assistant.is_model_ready(),
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
    
    # Check if AI is ready but hasn't been announced yet
    if ai_assistant and ai_assistant.is_model_ready() and not ai_ready_announced:
        # Schedule the announcement to happen shortly after connection
        socketio.start_background_task(announce_ai_ready)
    
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
        h_angle = 80 + horizontal  # Center is 90 degrees
        v_angle = 40 + vertical    # Center is 90 degrees
        
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
        if not audio_data:
            logger.error("No audio data received in voice command")
            emit('voice_response', {'success': False, 'message': 'No audio data received'})
            return
        
        logger.info(f"Received voice command audio data of length: {len(audio_data)}")
        
        # Process the audio data with voice recognition
        text = voice.recognize(audio_data)
        
        if not text:
            logger.error("Voice recognition failed to produce text")
            emit('voice_response', {'success': False, 'message': 'Could not recognize speech. Please try speaking more clearly.'})
            return
        
        logger.info(f"Recognized voice command: {text}")
        
        # Process the recognized text with AI assistant
        response = ai_assistant.process_command(text)
        
        # Response should always be a dict now due to our improvements in the AI assistant
        # But let's add a safety check just in case
        if not response or not isinstance(response, dict):
            logger.error(f"AI assistant returned unexpected response type: {type(response)}")
            emit('voice_response', {'success': False, 'message': 'AI assistant returned an invalid response'})
            return
        
        response_text = response.get('text', '')
        if not response_text:
            logger.warning("AI response contained no text")
            response_text = "I processed your request but didn't generate a proper response."
            
        logger.info(f"AI assistant response: {response_text[:100]}...")
        
        # Execute command if applicable
        if 'command' in response:
            command = response['command']
            logger.info(f"Executing command from voice: {command}")
            
            try:
                if command and isinstance(command, dict) and 'type' in command:
                    if command.get('type') == 'movement':
                        handle_movement({'direction': command.get('direction')})
                    elif command.get('type') == 'camera':
                        handle_camera_control({
                            'horizontal': command.get('horizontal', 0),
                            'vertical': command.get('vertical', 0)
                        })
                else:
                    logger.warning(f"Invalid command format: {command}")
            except Exception as cmd_err:
                logger.error(f"Error executing command: {cmd_err}")
        
        # Use text-to-speech to speak the response with current settings
        if tts and response_text:
            try:
                logger.info("Converting response to speech")
                # Set language based on settings or auto-detect
                language = tts_settings['language'] if tts_settings['language'] != 'auto' else None
                tts.speak(
                    response_text, 
                    speech_rate=tts_settings['speech_rate'], 
                    speech_volume=tts_settings['speech_volume'],
                    language=language
                )
            except Exception as tts_err:
                logger.error(f"Error using text-to-speech: {tts_err}")
        
        emit('voice_response', {
            'success': True,
            'text': text,
            'response': response_text,
            'tts_available': tts is not None
        })
    except Exception as e:
        logger.error(f"Voice command error: {e}", exc_info=True)
        emit('error', {'message': f'Voice command error: {str(e)}'})

@socketio.on('text_command')
def handle_text_command(data):
    """Process text commands."""
    if not ai_assistant:
        emit('error', {'message': 'AI assistant not available'})
        return
    
    try:
        text = data.get('text')
        if not text:
            emit('text_response', {'success': False, 'message': 'No text received'})
            return
            
        logger.info(f"Processing text command: {text}")
        
        # Process the text with AI assistant
        response = ai_assistant.process_command(text)
        
        # Response should always be a dict now due to our improvements in the AI assistant
        # But let's add a safety check just in case
        if not response or not isinstance(response, dict):
            logger.error(f"AI assistant returned unexpected response type: {type(response)}")
            emit('text_response', {'success': False, 'message': 'AI assistant returned an invalid response'})
            return
        
        response_text = response.get('text', '')
        if not response_text:
            logger.warning("AI response contained no text")
            response_text = "I processed your request but didn't generate a proper response."
        
        # Execute command if applicable
        if 'command' in response:
            command = response['command']
            logger.info(f"Executing command from text input: {command}")
            
            try:
                if command and isinstance(command, dict) and 'type' in command:
                    if command.get('type') == 'movement':
                        handle_movement({'direction': command.get('direction')})
                    elif command.get('type') == 'camera':
                        handle_camera_control({
                            'horizontal': command.get('horizontal', 0),
                            'vertical': command.get('vertical', 0)
                        })
                else:
                    logger.warning(f"Invalid command format: {command}")
            except Exception as cmd_err:
                logger.error(f"Error executing command: {cmd_err}")
        
        # Use text-to-speech to speak the response with current settings
        if tts and response_text:
            try:
                # Set language based on settings or auto-detect
                language = tts_settings['language'] if tts_settings['language'] != 'auto' else None
                tts.speak(
                    response_text, 
                    speech_rate=tts_settings['speech_rate'], 
                    speech_volume=tts_settings['speech_volume'],
                    language=language
                )
            except Exception as tts_err:
                logger.error(f"Error using text-to-speech: {tts_err}")
        
        emit('text_response', {
            'success': True,
            'response': response_text,
            'tts_available': tts is not None
        })
    except Exception as e:
        logger.error(f"Text command error: {e}", exc_info=True)
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

@socketio.on('update_tts_settings')
def handle_update_tts_settings(data):
    """Update text-to-speech settings."""
    global tts_settings
    
    # Get new settings with validation
    speech_rate = data.get('speech_rate', 130)
    speech_volume = data.get('speech_volume', 200)
    language = data.get('language', 'auto')
    
    # Apply range constraints
    speech_rate = max(80, min(200, speech_rate))
    speech_volume = max(0, min(200, speech_volume))
    
    # Validate language
    if language not in ['auto', 'en', 'zh']:
        language = 'auto'
    
    # Update settings
    tts_settings['speech_rate'] = speech_rate
    tts_settings['speech_volume'] = speech_volume
    tts_settings['language'] = language
    
    logger.info(f"Updated TTS settings: rate={speech_rate}, volume={speech_volume}, language={language}")

@socketio.on('get_tts_settings')
def handle_get_tts_settings():
    """Get current text-to-speech settings."""
    emit('tts_settings', tts_settings)

@socketio.on('test_tts')
def handle_test_tts(data):
    """Test text-to-speech with the given settings."""
    if not tts:
        emit('error', {'message': 'Text-to-speech not available'})
        return
    
    # Get settings from request or use current settings
    speech_rate = data.get('speech_rate', tts_settings['speech_rate'])
    speech_volume = data.get('speech_volume', tts_settings['speech_volume'])
    language = data.get('language', tts_settings['language'])
    custom_text = data.get('text', None)
    
    # Apply range constraints
    speech_rate = max(80, min(200, speech_rate))
    speech_volume = max(0, min(200, speech_volume))
    
    # Validate language
    if language not in ['auto', 'en', 'zh']:
        language = 'auto'
    
    try:
        # Choose appropriate test message based on language
        if custom_text:
            test_message = custom_text
        elif language == 'zh':
            test_message = "这是一个中文语音合成测试，当前使用的是设定好的语音参数。"
        elif language == 'en':
            test_message = "This is a test of the text-to-speech system with the current settings."
        else:
            # Auto-detect - use both languages to demonstrate
            test_message = "This is a bilingual test. 这是一个双语测试。"
        
        # Convert language setting for TTS function
        tts_language = None if language == 'auto' else language
        
        # Speak the test message
        tts.speak(
            test_message, 
            is_announcement=True, 
            speech_rate=speech_rate, 
            speech_volume=speech_volume,
            language=tts_language
        )
        
        emit('tts_test', {
            'success': True,
            'message': 'Text-to-speech test started',
            'text': test_message,
            'language': language
        })
    except Exception as e:
        logger.error(f"Error testing text-to-speech: {e}")
        emit('error', {'message': f'Text-to-speech test error: {str(e)}'})

if __name__ == '__main__':
    try:
        # Check if SSL certificates exist
        ssl_context = None
        cert_file = 'cert.pem'
        key_file = 'key.pem'
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            ssl_context = (cert_file, key_file)
            logger.info(f"SSL certificates found. Starting server with HTTPS support.")
        else:
            logger.info("SSL certificates not found. Starting server without HTTPS.")
            logger.info("Note: Voice recording may not work in Safari without HTTPS.")
            logger.info("To generate self-signed certificates:")
            logger.info("openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        
        # Start the Flask-SocketIO server
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, 
                    allow_unsafe_werkzeug=True, ssl_context=ssl_context)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        if robot:
            robot.t_stop(0)  # Stop the robot
        if camera:
            camera.release()  # Release camera resources 