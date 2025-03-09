#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Configuration settings for the application."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Camera settings
    CAMERA_ENABLED = os.environ.get('CAMERA_ENABLED', 'True').lower() in ('true', '1', 't')
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', 640))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', 480))
    CAMERA_FRAMERATE = int(os.environ.get('CAMERA_FRAMERATE', 30))
    
    # Robot settings
    ROBOT_ENABLED = os.environ.get('ROBOT_ENABLED', 'True').lower() in ('true', '1', 't')
    DEFAULT_SPEED = int(os.environ.get('DEFAULT_SPEED', 50))
    
    # Servo settings
    HORIZONTAL_SERVO_CHANNEL = int(os.environ.get('HORIZONTAL_SERVO_CHANNEL', 12))
    VERTICAL_SERVO_CHANNEL = int(os.environ.get('VERTICAL_SERVO_CHANNEL', 13))
    HORIZONTAL_SERVO_DEFAULT = int(os.environ.get('HORIZONTAL_SERVO_DEFAULT', 90))  # Center position
    VERTICAL_SERVO_DEFAULT = int(os.environ.get('VERTICAL_SERVO_DEFAULT', 90))      # Center position
    
    # Voice recognition settings
    VOICE_ENABLED = os.environ.get('VOICE_ENABLED', 'True').lower() in ('true', '1', 't')
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')
    
    # AI assistant settings
    AI_ENABLED = os.environ.get('AI_ENABLED', 'True').lower() in ('true', '1', 't')
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'deepseek-r1:1.7b')
    
    # WebRTC settings
    WEBRTC_ENABLED = os.environ.get('WEBRTC_ENABLED', 'True').lower() in ('true', '1', 't')
    STUN_SERVER = os.environ.get('STUN_SERVER', 'stun:stun.l.google.com:19302')
    
    # Static file settings
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates' 