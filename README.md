# AI Four-Wheel Drive Car Comprehensive Solution

This project is based on the Raspberry Pi 5, integrating the official Raspberry Pi camera, a four-wheel-drive chassis, and PCA9685 servo control, creating an AI smart car that supports web remote control, visual SLAM, autonomous navigation, and voice interaction.

## Core Features

- **Web Control**: Web-based simulated joystick controls the car's movement, while another joystick adjusts the camera gimbal angle. The camera feed is displayed in real-time.
- **Real-time Video Streaming**: Uses WebRTC for low-latency video transmission, utilizing the Raspberry Pi Camera + libcamera.
- **Remote API Control**: Supports remote control of the car and camera via Flask API + WebSocket.
- **Voice Interaction**: Implements local voice recognition and interaction using Whisper + Ollama + DeepSeekR1 1.7B.

## Hardware Requirements

- **Computing Unit**: Raspberry Pi 5
- **Camera**: Official Raspberry Pi Camera
- **Car Chassis**: LOBOT Four-Wheel Drive Chassis
- **Motor Driver**: PCA9685 + L298N
- **Servo Gimbal**: MG996R + PCA9685
- **Voice Processing**: ReSpeaker 2-Mic / 4-Mic

## Software Requirements

- **Operating System**: Ubuntu Server 24.04 LTS
- **Core Control Program**: LOBOROBOT.py (responsible for car movement control)

## Installation

1. Clone this repository to your Raspberry Pi
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```

## Web Interface

The web interface is designed with a Zelda-inspired theme, featuring:
- Dual joystick control
- Real-time video streaming
- Voice command functionality
- Text command input

## HTTPS Requirements for Voice Recording

Modern browsers, especially Safari on iOS, require HTTPS for accessing the microphone for security reasons. To enable voice recording:

1. **Local Development**: When running on localhost, voice recording will work without HTTPS.

2. **Production Deployment**: For remote access, you must use HTTPS. Options include:

   a. **Using a Reverse Proxy with SSL**: 
      - Set up Nginx or Apache as a reverse proxy
      - Configure SSL certificates (Let's Encrypt is free)
      - Forward requests to the Flask application

   b. **Configure Flask with SSL directly**:
      ```python
      if __name__ == '__main__':
          socketio.run(app, 
                       host='0.0.0.0', 
                       port=5000, 
                       ssl_context=('cert.pem', 'key.pem'))
      ```

   c. **Self-signed certificates**:
      ```
      openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
      ```
      Note: Self-signed certificates will show security warnings in browsers.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 