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
import json
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
            audio_data (str): Base64 encoded audio data
            
        Returns:
            str: Recognized text
        """
        try:
            # Log the first few bytes for debugging
            logger.info(f"Processing audio data, first 20 chars: {audio_data[:20]}...")
            
            # Decode base64 audio data
            try:
                audio_bytes = base64.b64decode(audio_data)
                logger.info(f"Decoded audio size: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.error(f"Base64 decoding error: {e}")
                return None
            
            # Check for very small audio files (likely empty or corrupted)
            if len(audio_bytes) < 100:
                logger.error(f"Audio data too small: {len(audio_bytes)} bytes")
                return None
                
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
                logger.info(f"Saved audio to temporary file: {temp_file_path}")
            
            # First try to process directly with Whisper (it can handle various formats)
            try:
                logger.info("Attempting direct processing with Whisper")
                start_time = time.time()
                result = self.model.transcribe(temp_file_path, language="en")
                processing_time = time.time() - start_time
                
                # Log results
                recognized_text = result["text"].strip()
                logger.info(f"Speech recognized in {processing_time:.2f}s: {recognized_text}")
                
                # Clean up
                os.unlink(temp_file_path)
                return recognized_text
            except Exception as direct_error:
                logger.warning(f"Direct Whisper processing failed: {direct_error}")
                # Continue to conversion attempts
            
            # If direct processing failed, try various conversions
            # 1. First, try to convert to WAV using scipy or numpy if available
            try:
                import scipy.io.wavfile as wavfile
                
                logger.info("Converting audio using scipy")
                # Convert to WAV using scipy
                wav_path = temp_file_path + ".wav"
                
                # Try to read as raw PCM data
                try:
                    # Assuming 16kHz, 16-bit, mono PCM data
                    pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    wavfile.write(wav_path, 16000, pcm_data)
                    
                    # Use the converted WAV file
                    temp_file_path = wav_path
                    logger.info(f"Converted to WAV: {wav_path}")
                except Exception as pcm_error:
                    logger.warning(f"PCM conversion failed: {pcm_error}")
            except ImportError:
                logger.warning("scipy not available for audio conversion")
            
            # 2. Try manual WAV conversion as a last resort
            if not os.path.exists(wav_path if 'wav_path' in locals() else "nonexistent"):
                try:
                    logger.info("Attempting manual WAV conversion")
                    wav_path = temp_file_path + ".manual.wav"
                    
                    with open(wav_path, 'wb') as wav_file:
                        # Create a basic WAV header
                        sample_rate = 16000
                        channels = 1
                        bits_per_sample = 16
                        
                        # RIFF header
                        wav_file.write(b'RIFF')
                        wav_file.write((36 + len(audio_bytes)).to_bytes(4, 'little'))
                        wav_file.write(b'WAVE')
                        
                        # fmt chunk
                        wav_file.write(b'fmt ')
                        wav_file.write((16).to_bytes(4, 'little'))  # chunk size
                        wav_file.write((1).to_bytes(2, 'little'))   # PCM format
                        wav_file.write(channels.to_bytes(2, 'little'))  # channels
                        wav_file.write(sample_rate.to_bytes(4, 'little'))  # sample rate
                        wav_file.write((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little'))  # byte rate
                        wav_file.write((channels * bits_per_sample // 8).to_bytes(2, 'little'))  # block align
                        wav_file.write((bits_per_sample).to_bytes(2, 'little'))  # bits per sample
                        
                        # data chunk
                        wav_file.write(b'data')
                        wav_file.write(len(audio_bytes).to_bytes(4, 'little'))
                        wav_file.write(audio_bytes)
                    
                    # Use the converted WAV file
                    temp_file_path = wav_path
                    logger.info(f"Manual WAV conversion completed: {wav_path}")
                except Exception as wav_error:
                    logger.error(f"Manual WAV conversion failed: {wav_error}")
            
            # Try processing with Whisper again
            try:
                logger.info(f"Processing with converted file: {temp_file_path}")
                start_time = time.time()
                result = self.model.transcribe(temp_file_path, language="en")
                processing_time = time.time() - start_time
                
                # Log results
                recognized_text = result["text"].strip()
                logger.info(f"Speech recognized in {processing_time:.2f}s: {recognized_text}")
                
                # Clean up temporary files
                for file_path in [temp_file_path, wav_path if 'wav_path' in locals() else None]:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.unlink(file_path)
                        except Exception:
                            pass
                
                return recognized_text
            except Exception as whisper_error:
                logger.error(f"Whisper processing error: {whisper_error}")
                
                # Clean up temporary files
                for file_path in [temp_file_path, wav_path if 'wav_path' in locals() else None]:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.unlink(file_path)
                        except Exception:
                            pass
                
                return None
            
        except Exception as e:
            logger.error(f"Error recognizing speech: {e}", exc_info=True)
            # Clean up any temporary files if they exist
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
            if 'wav_path' in locals() and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass
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