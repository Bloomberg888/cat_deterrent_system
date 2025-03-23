import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import requests
import time
from datetime import datetime
import threading
import io

# Path to the pre-trained TensorFlow Lite model
model_path = 'ssd_mobilenet_v1.tflite'

# Load the TensorFlow Lite model
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()  # Model input details
output_details = interpreter.get_output_details()  # Model output details

# Class labels from the COCO dataset
label_map = {0: 'person', 16: 'cat'}

# Configure the Raspberry Pi camera using picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Telegram configuration - replace with your own values
bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'  # Telegram bot token
chat_id = 'YOUR_TELEGRAM_CHAT_ID'      # Telegram chat ID

# ESP32 configuration - replace with your ESP32's IP address
esp_ip = 'http://YOUR_ESP32_IP'

# State variables
cat_detected = False            # Tracks if a cat is currently detected
sound_start_time = None         # Timestamp when the sound starts
min_sound_duration = 4          # Minimum duration for the sound (in seconds)
person_detected_time = None     # Timestamp of the last human detection
ignore_cat_duration = 15        # Duration to ignore cats after human detection (in seconds)

# Function to send photos to Telegram in a background thread
def send_photos_in_background():
    """Capture and send 3 photos to Telegram with a 1-second interval."""
    for _ in range(3):
        frame = picam2.capture_array()  # Capture a frame from the camera
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
        success, encoded_image = cv2.imencode('.jpg', frame)  # Encode frame as JPEG
        if not success:
            print("Error encoding image")
            continue
        image_bytes = io.BytesIO(encoded_image.tobytes())  # Convert to byte stream

        try:
            response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendPhoto',
                files={'photo': ('photo.jpg', image_bytes, 'image/jpeg')},
                data={'chat_id': chat_id}
            )
            if response.status_code == 200:
                print(f"Photo sent to Telegram (time: {datetime.now().strftime('%H:%M:%S')})")
            else:
                print(f"Error sending photo: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Network error while sending photo: {e}")
        time.sleep(1)  # Delay of 1 second between photos

# Main loop
while True:
    # Capture a frame from the camera
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV processing

    # Resize the frame to 300x300, the expected input size for the model
    resized_frame = cv2.resize(frame, (300, 300))

    # Prepare the frame for the model
    input_data = np.expand_dims(resized_frame, axis=0)  # Add batch dimension
    interpreter.set_tensor(input_details[0]['index'], input_data)  # Set input tensor
    interpreter.invoke()  # Run inference

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]  # Bounding boxes
    classes = interpreter.get_tensor(output_details[1]['index'])[0]  # Class IDs
    scores = interpreter.get_tensor(output_details[2]['index'])[0]  # Confidence scores
    num_detections = int(interpreter.get_tensor(output_details[3]['index'])[0])  # Number of detections

    cat_present = False    # Flag for cat presence
    person_present = False  # Flag for human presence
    current_time = time.time()  # Current timestamp for timing logic

    # Analyze all detected objects in the frame
    for i in range(num_detections):
        class_id = int(classes[i])
        score = scores[i]

        if class_id == 0 and score > 0.4:  # Detect 'person' with confidence > 0.4
            person_present = True
            person_detected_time = current_time  # Update last human detection time
            print(f"Person detected with confidence {score:.2f}")
        elif class_id == 16 and score > 0.6:  # Detect 'cat' with confidence > 0.6
            cat_present = True
            scoreInf = score
            print(f"Cat detected with confidence {score:.2f}")

    # Check if 15 seconds have passed since the last human detection
    if person_detected_time and (current_time - person_detected_time < ignore_cat_duration):
        cat_present = False  # Ignore cats if a human was recently detected
        print(f"Ignoring cats: {ignore_cat_duration - (current_time - person_detected_time):.1f} seconds remaining")

    # Logic: A cat is confirmed only if no human is present
    cat_present = cat_present and not person_present

    if cat_present and not cat_detected:
        # Cat detected for the first time
        cat_detected = True
        sound_start_time = current_time
        print("Cat confirmed!")

        # Get current date and time for the Telegram message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Cat detected! Date and time: {timestamp} with confidence {scoreInf}"

        # Send a text message to Telegram
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={'chat_id': chat_id, 'text': message}
        )
        if response.status_code == 200:
            print("Message with date and time sent to Telegram")
        else:
            print(f"Error sending message: {response.text}")

        # Send a start signal to the ESP32 to activate the vibromotor
        try:
            requests.get(f'{esp_ip}/start')
            print("Signal /start sent to ESP32")
        except requests.exceptions.RequestException as e:
            print(f"Error sending /start to ESP32: {e}")

        # Start sending photos in a background thread
        threading.Thread(target=send_photos_in_background, daemon=True).start()

    elif cat_present and cat_detected:
        # Cat continues to be in the frame, update sound start time
        sound_start_time = current_time

    elif not cat_present and cat_detected:
        # Cat is no longer in the frame, check if 4 seconds have passed
        if sound_start_time and (current_time - sound_start_time >= min_sound_duration):
            cat_detected = False
            sound_start_time = None
            print("Cat no longer in frame")

            # Send a stop signal to the ESP32 to deactivate the vibromotor
            try:
                requests.get(f'{esp_ip}/stop')
                print("Signal /stop sent to ESP32")
            except requests.exceptions.RequestException as e:
                print(f"Error sending /stop to ESP32: {e}")

    time.sleep(0.1)  # Reduce CPU load with a 100ms delay