#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import threading
import pyttsx3
import re
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextToSpeech:
    """Text-to-speech class using pyttsx3 for speech output."""
    
    def __init__(self):
        """Initialize the text-to-speech with configuration settings."""
        self.config = Config()
        
        # Initialize the TTS engine
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to set a female voice if available
                female_voice = None
                for voice in voices:
                    if 'female' in voice.name.lower():
                        female_voice = voice.id
                        break
                
                if female_voice:
                    self.engine.setProperty('voice', female_voice)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 150)  # 150 words per minute
            self.engine.setProperty('volume', 0.9)  # 90% volume
            
            logger.info("Text-to-speech initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize text-to-speech: {e}")
            self.engine = None
            raise
    
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
            r"I need to.*?(?=\n\n|\Z)"
        ]
        
        cleaned_text = text
        for pattern in thinking_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.DOTALL)
        
        # Remove multiple consecutive newlines
        cleaned_text = re.sub(r'\n{2,}', '\n\n', cleaned_text)
        
        # Trim whitespace
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def speak(self, text):
        """
        Convert text to speech.
        
        Args:
            text (str): The text to convert to speech
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.engine:
            logger.error("TTS engine not initialized")
            return False
        
        try:
            # Remove thinking part from the response
            cleaned_text = self.remove_thinking_part(text)
            
            # Start a new thread for speech to avoid blocking
            threading.Thread(target=self._speak_thread, args=(cleaned_text,)).start()
            return True
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return False
    
    def _speak_thread(self, text):
        """Thread function for speaking text."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in speech thread: {e}")

# For testing the text-to-speech module directly
if __name__ == "__main__":
    try:
        tts = TextToSpeech()
        print("Text-to-speech initialized. Enter text to speak (Ctrl+C to exit):")
        
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            tts.speak(user_input)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}") 