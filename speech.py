#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import threading
import subprocess
import tempfile
import re
import langid  # For language detection
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextToSpeech:
    """Text-to-speech class with multiple fallback methods for speech output."""
    
    def __init__(self):
        """Initialize the text-to-speech with configuration settings."""
        self.config = Config()
        self.engine = None
        self.use_pyttsx3 = False
        self.use_espeak = False
        self.use_aplay = False
        
        # Chinese voice settings
        self.chinese_voice_pyttsx3 = None
        self.english_voice_pyttsx3 = None
        
        # Try different TTS engines in order of preference
        self._try_initialize_engines()
        
        if not (self.use_pyttsx3 or self.use_espeak or self.use_aplay):
            logger.warning("No text-to-speech engines available. Speech output will be disabled.")
    
    def _try_initialize_engines(self):
        """Try to initialize various TTS engines with fallbacks."""
        # First try pyttsx3
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find both English and Chinese voices
                for voice in voices:
                    voice_name = voice.name.lower()
                    voice_id = voice.id
                    
                    # Check for Chinese voices
                    if any(lang in voice_name for lang in ['chinese', 'mandarin', 'cmn', 'zh', 'zh-cn']):
                        self.chinese_voice_pyttsx3 = voice_id
                        logger.info(f"Found Chinese voice: {voice.name}")
                    
                    # Check for female English voice
                    if 'female' in voice_name and any(lang in voice_name for lang in ['english', 'en', 'en-us']):
                        self.english_voice_pyttsx3 = voice_id
                
                # Fallback to any English voice if no specific female voice found
                if not self.english_voice_pyttsx3:
                    for voice in voices:
                        if any(lang in voice.name.lower() for lang in ['english', 'en', 'en-us']):
                            self.english_voice_pyttsx3 = voice.id
                            break
                
                # If no Chinese voice found, log it
                if not self.chinese_voice_pyttsx3:
                    logger.warning("No Chinese voice found in pyttsx3. Will use espeak for Chinese.")
            
            # Set speech rate and volume - adjusted for better clarity
            self.engine.setProperty('rate', 130)  # Reduced from 150 to 130 words per minute
            self.engine.setProperty('volume', 1.0)  # Increased from 0.9 to 1.0 (maximum volume)
            
            # Test the engine
            try:
                # Just get the available voices to see if it works
                self.engine.getProperty('voices')
                self.use_pyttsx3 = True
                logger.info("pyttsx3 text-to-speech initialized successfully")
            except Exception as e:
                logger.warning(f"pyttsx3 engine initialized but test failed: {e}")
                self.engine = None
        except ImportError:
            logger.warning("pyttsx3 is not installed. Falling back to other TTS methods.")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {e}")
        
        # If pyttsx3 failed, try espeak directly
        if not self.use_pyttsx3:
            try:
                # Check if espeak is available
                result = subprocess.run(['which', 'espeak'], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
                if result.returncode == 0:
                    self.use_espeak = True
                    logger.info("espeak text-to-speech available")
                else:
                    logger.warning("espeak not found in system")
            except Exception as e:
                logger.warning(f"Failed to check for espeak: {e}")
        
        # As a last resort, check if aplay is available for playing audio files
        try:
            result = subprocess.run(['which', 'aplay'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            if result.returncode == 0:
                self.use_aplay = True
                logger.info("aplay available for audio playback")
            else:
                logger.warning("aplay not found in system")
        except Exception as e:
            logger.warning(f"Failed to check for aplay: {e}")
    
    def detect_language(self, text):
        """
        Detect the language of the text.
        
        Args:
            text (str): The text to detect language for
            
        Returns:
            str: Language code ('en' for English, 'zh' for Chinese, etc.)
        """
        try:
            lang, confidence = langid.classify(text)
            logger.info(f"Language detected: {lang} (confidence: {confidence:.2f})")
            return lang
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            # Default to English if detection fails
            return 'en'
    
    def remove_thinking_part(self, text):
        """
        Remove the thinking part from DeepSeek's response.
        
        Args:
            text (str): The complete response text
            
        Returns:
            str: Response text without the thinking part
        """
        # Remove thinking part if it exists
        # Look for patterns like "Let me think...", "Thinking:", etc.
        thinking_patterns = [
            r"Let me think.*?(?=\n\n|\Z)",
            r"Thinking:.*?(?=\n\n|\Z)",
            r"Let's analyze.*?(?=\n\n|\Z)",
            r"Hmm, let.*?(?=\n\n|\Z)",
            r"I need to.*?(?=\n\n|\Z)",
            # Chinese thinking patterns
            r"让我思考.*?(?=\n\n|\Z)",
            r"思考中:.*?(?=\n\n|\Z)",
            r"我需要.*?(?=\n\n|\Z)",
            r"让我分析.*?(?=\n\n|\Z)"
        ]
        
        cleaned_text = text
        for pattern in thinking_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.DOTALL)
        
        # Remove multiple consecutive newlines
        cleaned_text = re.sub(r'\n{2,}', '\n\n', cleaned_text)
        
        # Trim whitespace
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def speak(self, text, is_announcement=False, speech_rate=None, speech_volume=None, language=None):
        """
        Convert text to speech using available methods.
        
        Args:
            text (str): The text to convert to speech
            is_announcement (bool): Whether this is a direct announcement (skip thinking part removal)
            speech_rate (int): Optional speech rate in words per minute (80-200)
            speech_volume (int): Optional volume level (0-200)
            language (str): Optional language code override ('en', 'zh')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not (self.use_pyttsx3 or self.use_espeak or self.use_aplay):
            logger.error("No TTS engines available")
            return False
        
        try:
            # Process the text
            if is_announcement:
                # Use the text directly for announcements
                cleaned_text = text
            else:
                # Remove thinking part from AI responses
                cleaned_text = self.remove_thinking_part(text)
            
            # Set default values if not specified
            if speech_rate is None:
                speech_rate = 130
            if speech_volume is None:
                speech_volume = 200
                
            # Apply range constraints
            speech_rate = max(80, min(200, speech_rate))
            speech_volume = max(0, min(200, speech_volume))
            
            # Detect language if not specified
            if language is None:
                language = self.detect_language(cleaned_text)
            
            logger.info(f"Speaking: '{cleaned_text[:50]}...' (rate={speech_rate}, volume={speech_volume}, language={language})")
            
            # Start a new thread for speech to avoid blocking
            threading.Thread(
                target=self._speak_thread, 
                args=(cleaned_text, speech_rate, speech_volume, language)
            ).start()
            return True
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return False

    def _speak_thread(self, text, speech_rate=130, speech_volume=200, language='en'):
        """Thread function for speaking text using available methods."""
        # Try different methods in order of preference
        success = False
        
        # First try pyttsx3 if available
        if self.use_pyttsx3 and not success:
            try:
                logger.info(f"Using pyttsx3 for speech (rate={speech_rate}, volume={speech_volume/200}, language={language})")
                
                # Update engine properties for this specific speech
                self.engine.setProperty('rate', speech_rate)
                self.engine.setProperty('volume', speech_volume / 200)  # Convert to 0-1 range
                
                # Select voice based on language
                if language == 'zh' and self.chinese_voice_pyttsx3:
                    logger.info(f"Using Chinese voice: {self.chinese_voice_pyttsx3}")
                    self.engine.setProperty('voice', self.chinese_voice_pyttsx3)
                elif self.english_voice_pyttsx3:
                    logger.info(f"Using English voice: {self.english_voice_pyttsx3}")
                    self.engine.setProperty('voice', self.english_voice_pyttsx3)
                
                self.engine.say(text)
                self.engine.runAndWait()
                success = True
            except Exception as e:
                logger.error(f"Error with pyttsx3 speech: {e}")
                # If pyttsx3 fails, try the next method
        
        # If pyttsx3 failed, try espeak
        if self.use_espeak and not success:
            try:
                logger.info(f"Using espeak for speech (rate={speech_rate}, volume={speech_volume}, language={language})")
                
                # Set voice based on language
                voice = 'en+f3'  # Default female English voice
                if language == 'zh':
                    voice = 'zh'  # Chinese voice
                
                # Run espeak with the text - adjusted for better clarity
                subprocess.run([
                    'espeak', 
                    '-v', voice,              # Language-appropriate voice
                    '-s', str(speech_rate),   # Speech rate
                    '-a', str(speech_volume), # Amplitude (volume)
                    text
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                success = True
            except Exception as e:
                logger.error(f"Error with espeak speech: {e}")
        
        # As a last resort, try to generate speech and play with aplay
        if self.use_aplay and not success:
            try:
                logger.info(f"Using espeak + aplay for speech (rate={speech_rate}, volume={speech_volume}, language={language})")
                # Create a temporary wav file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Set voice based on language
                voice = 'en+f3'  # Default female English voice
                if language == 'zh':
                    voice = 'zh'  # Chinese voice
                
                # Generate speech to wav file
                try:
                    subprocess.run([
                        'espeak', 
                        '-v', voice,               # Language-appropriate voice
                        '-s', str(speech_rate),    # Speech rate
                        '-a', str(speech_volume),  # Amplitude (volume)
                        '-w', temp_path, 
                        text
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Play with aplay at maximum volume
                    subprocess.run([
                        'aplay', 
                        '-D', 'default',  # Default audio device
                        '--buffer-size=4096',  # Larger buffer for smoother playback
                        temp_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    success = True
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            except Exception as e:
                logger.error(f"Error with aplay speech: {e}")
        
        if not success:
            logger.error("All speech methods failed")

# For testing the text-to-speech module directly
if __name__ == "__main__":
    try:
        tts = TextToSpeech()
        print("Text-to-speech initialized. Enter text to speak (Ctrl+C to exit):")
        print("Type ':zh' before text to speak in Chinese")
        print("Type ':en' before text to speak in English")
        
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Check if language is specified
            language = None
            if user_input.startswith(':zh '):
                language = 'zh'
                user_input = user_input[4:]
            elif user_input.startswith(':en '):
                language = 'en'
                user_input = user_input[4:]
            
            tts.speak(user_input, language=language)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}") 