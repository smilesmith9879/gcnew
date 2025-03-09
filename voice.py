#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import logging
import tempfile
import numpy as np
import whisper
import base64
import wave
import time
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceRecognition:
    """Voice recognition class using Whisper for speech-to-text."""
    
    def __init__(self):
        """Initialize the voice recognition with configuration settings."""
        self.config = Config()
        
        # Load Whisper model
        try:
            logger.info(f"Loading Whisper model: {self.config.WHISPER_MODEL}")
            self.model = whisper.load_model(self.config.WHISPER_MODEL)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def recognize(self, audio_data):
        """
        Recognize speech from audio data.
        
        Args:
            audio_data (str): Base64 encoded audio data (WAV format)
            
        Returns:
            str: Recognized text
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Process with Whisper
            start_time = time.time()
            result = self.model.transcribe(temp_file_path, language="en")
            processing_time = time.time() - start_time
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Log results
            recognized_text = result["text"].strip()
            logger.info(f"Speech recognized in {processing_time:.2f}s: {recognized_text}")
            
            return recognized_text
        except Exception as e:
            logger.error(f"Error recognizing speech: {e}")
            return None
    
    def recognize_from_file(self, file_path):
        """
        Recognize speech from an audio file.
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            str: Recognized text
        """
        try:
            # Process with Whisper
            start_time = time.time()
            result = self.model.transcribe(file_path, language="en")
            processing_time = time.time() - start_time
            
            # Log results
            recognized_text = result["text"].strip()
            logger.info(f"Speech recognized in {processing_time:.2f}s: {recognized_text}")
            
            return recognized_text
        except Exception as e:
            logger.error(f"Error recognizing speech from file: {e}")
            return None

# For testing the voice recognition module directly
if __name__ == "__main__":
    try:
        voice = VoiceRecognition()
        print("Voice recognition initialized. Testing with a sample file...")
        
        # Test with a sample file if available
        sample_file = "sample_audio.wav"
        if os.path.exists(sample_file):
            text = voice.recognize_from_file(sample_file)
            print(f"Recognized text: {text}")
        else:
            print(f"Sample file {sample_file} not found. Please provide an audio file for testing.")
    
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}") 