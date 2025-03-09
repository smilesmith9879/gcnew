#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import time
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAssistant:
    """AI assistant class using Ollama with DeepSeekR1 for natural language processing."""
    
    def __init__(self):
        """Initialize the AI assistant with configuration settings."""
        self.config = Config()
        
        # Check if Ollama is available
        try:
            response = requests.get(f"{self.config.OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                logger.warning(f"Ollama server returned status code {response.status_code}")
            
            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            if self.config.OLLAMA_MODEL not in model_names:
                logger.warning(f"Model {self.config.OLLAMA_MODEL} not found in Ollama. Available models: {model_names}")
                logger.info(f"You may need to pull the model using: ollama pull {self.config.OLLAMA_MODEL}")
            
            logger.info(f"AI assistant initialized with model: {self.config.OLLAMA_MODEL}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            logger.info("Make sure Ollama is running and accessible")
            raise
    
    def process_command(self, text):
        """
        Process a command from text input.
        
        Args:
            text (str): The text command to process
            
        Returns:
            dict: Response containing text and optional command
        """
        try:
            # Prepare the prompt for the AI model
            system_prompt = """
            You are an AI assistant for a four-wheel drive robot car with a camera gimbal.
            
            Available commands:
            - Movement: forward, backward, left, right, moveLeft, moveRight, forwardLeft, forwardRight, backwardLeft, backwardRight, stop
            - Camera: Control horizontal (-45 to 45 degrees) and vertical (-10 to 30 degrees) angles
            
            When responding to commands, provide a friendly response and extract any commands for the robot.
            If the user asks for a movement or camera action, include the command in your response.
            """
            
            prompt = f"User: {text}\n\nRespond with a JSON object containing 'text' (your response) and optionally 'command' if there's an action to perform."
            
            # Call the Ollama API
            start_time = time.time()
            response = requests.post(
                f"{self.config.OLLAMA_URL}/api/generate",
                json={
                    "model": self.config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": system_prompt,
                    "format": "json",
                    "stream": False
                }
            )
            processing_time = time.time() - start_time
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {"text": "I'm sorry, I encountered an error processing your request."}
            
            # Parse the response
            result = response.json()
            response_text = result.get("response", "")
            
            # Try to parse the JSON response
            try:
                parsed_response = json.loads(response_text)
                logger.info(f"AI processed command in {processing_time:.2f}s")
                return parsed_response
            except json.JSONDecodeError:
                # If not valid JSON, just return the text
                logger.warning(f"AI response was not valid JSON: {response_text}")
                return {"text": response_text}
        
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {"text": "I'm sorry, I encountered an error processing your request."}

# For testing the AI assistant module directly
if __name__ == "__main__":
    try:
        ai = AIAssistant()
        print("AI assistant initialized. Enter commands (Ctrl+C to exit):")
        
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            response = ai.process_command(user_input)
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            print()
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}") 