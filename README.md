да# Automated Cat Deterrent System for Kitchen Counters

## Overview

This project implements an automated system to deter cats from jumping onto kitchen counters. It uses a Raspberry Pi 4B with a camera to detect the presence of cats and triggers a deterrent action (sound playback via ESP32 and vibration motor) and sends Telegram notifications with images.

The system utilizes object detection (TensorFlow Lite with a COCO-SSD model) to identify cats in the camera's field of view. Upon detection, it sends a signal to an ESP32, which controls a sound module (MAX98357A with speakers) to play a sound aimed at deterring the cat. Simultaneously, it sends a notification with captured images to a Telegram chat.

## Features

- Real-time cat detection using Raspberry Pi and TensorFlow Lite.
- Triggering of a deterrent sound via ESP32 upon cat detection (while no human is detected).
- Sending of notifications with images to a Telegram chat when a cat is detected.
- Sound playback stops when the cat leaves the camera's view.
- Detection logic to avoid triggering when a person is present.

## Prerequisites

### Hardware

- Raspberry Pi 4B
- Raspberry Pi OS 64-bit (Bookworm recommended)
- OV5647 3.6mm IR 1080p Camera with Night Vision Module
- ESP32 WROOM 32U
- MAX98357A Amplifier Module
- Two 1W 8 Ohm Speakers
- Jumper wires for connections

### Software

#### Raspberry Pi

- Python 3
- pip
- tflite-runtime
- opencv-python
- picamera2
- requests

#### ESP32

- Arduino IDE with ESP32 board support
- ESP32 Audio library (for sound playback)
- WiFi library

## Installation and Setup

Follow these steps to set up the project:

### Raspberry Pi Setup

1. **Install Raspberry Pi OS:** Flash Raspberry Pi OS 64-bit (Bookworm recommended) onto an SD card.
2. **Enable Camera:** Use `sudo raspi-config` to enable the camera interface (if 'Legacy Camera' option is available, enable it. For newer versions, the camera is often enabled by default).
3. **Clone Repository:** Clone this GitHub repository to your Raspberry Pi.
4. **Install Dependencies:** Navigate to the repository directory on the Raspberry Pi and install the required Python packages using pip:
   ``bash

   sudo apt update

   sudo apt install python3-opencv python3-libcamera

   sudo apt install libcap-dev  # For picamera2 dependency

   python3 -m venv venv

   source venv/bin/activate

   pip install tflite-runtime opencv-python picamera2 requests
   ``
5. **Download TensorFlow Lite Model:** Download a COCO-SSD MobileNet V1 model (`ssd_mobilenet_v1.tflite`) and place it in the same directory as the Python script or update the `model_path` variable in `cat_detector.py`. You can download it using `wget`:
   ``bash
   wget https://tfhub.dev/tensorflow/lite-model/ssd_mobilenet_v1/1/metadata/2?lite-format=tflite -O ssd_mobilenet_v1.tflite
   ``
6. **Telegram Bot Setup:**
   - Create a new bot on Telegram using BotFather (@BotFather).
   - Obtain the bot token.
   - Get your Telegram chat ID using UserInfoBot (@userinfobot).
   - Update the `bot_token` and `chat_id` variables in `cat_detector.py`.
7. **ESP32 IP Address:** Set the correct IP address of your ESP32 in the `esp_ip` variable in `cat_detector.py`.

### ESP32 Setup

1. **Install Arduino IDE and ESP32 Core:** Follow the instructions on the Arduino website to install the Arduino IDE and add support for the ESP32 board.
2. **Install ESP32 Audio Library:** Install the ESP32 Audio library via the Arduino Library Manager.
3. **Connect Hardware:** Connect the MAX98357A amplifier and speakers to the ESP32 according to the MAX98357A datasheet.
4. **Upload Sketch:** Open the `esp32_sound_player.ino` sketch in the Arduino IDE, update the `ssid` and `password` with your WiFi credentials, and upload the sketch to your ESP32. Ensure the sound file (e.g., `sound.mp3`) is uploaded to the ESP32's file system (SPIFFS or LittleFS) and the `sound_file` variable in the sketch is updated accordingly. For simplicity, the provided ESP32 sketch uses a vibration motor as a placeholder for the sound system. You will need to adapt it for the MAX98357A.

## Usage

1. **Run Raspberry Pi Script:** Activate the virtual environment (if you created one) and run the `cat_detector.py` script on the Raspberry Pi:
   ``bash
   cd your_repository_directory
   source venv/bin/activate
   python3 cat_detector.py
   ``
2. **Ensure ESP32 is Running:** Make sure the ESP32 is powered on and connected to the WiFi network.

The system will now monitor the camera feed for cats. When a cat is detected (and no person is detected), a signal will be sent to the ESP32 (triggering the deterrent action), and you will receive a notification with images on Telegram.

## Code Structure

### Raspberry Pi (`cat_detector.py`)

- Imports necessary libraries (cv2, numpy, tflite_runtime, picamera2, requests, time, threading, io, datetime).
- Loads the TensorFlow Lite model for object detection.
- Initializes the Raspberry Pi camera using picamera2.
- Continuously captures frames, performs object detection, and checks for the presence of cats (while ensuring no person is detected).
- Sends HTTP GET requests to the ESP32 to start and stop the deterrent action.
- Sends notifications with images to a Telegram chat using the Telegram Bot API.
- Uses threading for sending images to Telegram without blocking the main detection loop.

### ESP32 (`esp32_sound_player.ino`)

- Connects to the specified WiFi network.
- Sets up a simple web server to listen for `/start` and `/stop` commands.
- Controls a vibration motor (placeholder for sound system) based on the received commands. **Note:** This sketch needs to be adapted to control the MAX98357A and play a sound file.

## Further Improvements

- Implement actual sound playback on the ESP32 using the MAX98357A.
- Fine-tune the object detection model for better accuracy.
- Add more sophisticated deterrent actions.
- Create a user interface for configuration and monitoring.
- Optimize performance for lower resource usage.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open-source and available under the MIT license.