# Automated Cat Deterrent System for Kitchen Counters

## Overview

This project implements an automated system to deter cats from jumping onto kitchen counters. It uses a Raspberry Pi 4B with a camera to detect the presence of cats and triggers a deterrent action (vibration via ESP32 and vibration motor) and sends Telegram notifications with images.

The system utilizes object detection (TensorFlow Lite with a COCO-SSD model) to identify cats in the camera's field of view. Upon detection, it sends a signal to an ESP32, which controls a vibration motor to deter the cat. Simultaneously, it sends a notification with captured images to a Telegram chat.

## Features

- Real-time cat detection using Raspberry Pi and TensorFlow Lite.
- Triggering of a deterrent vibration via ESP32 upon cat detection (while no human is detected).
- Sending of notifications with images to a Telegram chat when a cat is detected.
- Vibration stops when the cat leaves the camera's view.
- Detection logic to avoid triggering when a person is present.

## Prerequisites

### Hardware

- Raspberry Pi 4B
- Raspberry Pi OS 64-bit (Bookworm recommended)
- OV5647 3.6mm IR 1080p Camera with Night Vision Module
- ESP32 WROOM 32U
- Vibration Motor (e.g., 10mm coin vibration motor)
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
- WiFi library

## Installation and Setup

Follow these steps to set up the project:

### Raspberry Pi Setup

1. **Install Raspberry Pi OS:** Flash Raspberry Pi OS 64-bit (Bookworm recommended) onto an SD card.
2. **Enable Camera:** Use `sudo raspi-config` to enable the camera interface (if 'Legacy Camera' option is available, enable it. For newer versions, the camera is often enabled by default).
3. **Clone Repository:** Clone this GitHub repository to your Raspberry Pi:
   ```bash
   git clone https://github.com/Bloomberg888/cat_deterrent_system.git
   cd cat_deterrent_system