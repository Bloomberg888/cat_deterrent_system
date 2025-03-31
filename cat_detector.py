import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import requests
import time
from datetime import datetime
import threading
import io
from collections import deque

# Path to the TensorFlow Lite model
model_path = 'ssd_mobilenet_v1.tflite'

# Load the TensorFlow Lite model
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels from the COCO dataset
label_map = {0: 'person', 16: 'cat'}

# Configure the Raspberry Pi camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Telegram configuration - replace with your own values
bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'  # Your Telegram bot token
chat_id = 'YOUR_TELEGRAM_CHAT_ID'      # Your Telegram chat ID

# ESP32 configuration - replace with your ESP32's IP address
esp_ip = 'http://YOUR_ESP32_IP'

# State variables
cat_detected = False
sound_start_time = None  # Timestamp when the vibromotor starts
min_sound_duration = 10  # Minimum duration for the vibromotor (in seconds)

# Queue to store detection history (5 frames)
history = deque(maxlen=5)

# Function to send photos to Telegram in a background thread
def send_photos_in_background(frames_with_boxes):
    """Send 3 photos to Telegram with bounding boxes and size annotations."""
    for frame in frames_with_boxes:
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            print("Error encoding image")
            continue
        image_bytes = io.BytesIO(encoded_image.tobytes())
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
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV

    # Resize the frame to 300x300, the expected input size for the model
    resized_frame = cv2.resize(frame, (300, 300))

    # Prepare the frame for the model
    input_data = np.expand_dims(resized_frame, axis=0)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]  # Bounding boxes
    classes = interpreter.get_tensor(output_details[1]['index'])[0]  # Class IDs
    scores = interpreter.get_tensor(output_details[2]['index'])[0]  # Confidence scores
    num_detections = int(interpreter.get_tensor(output_details[3]['index'])[0])  # Number of detections

    cat_in_frame = False
    person_in_frame = False
    cat_box = None  # To store bounding box of the detected cat

    # Analyze all detected objects in the frame
    for i in range(num_detections):
        class_id = int(classes[i])
        score = scores[i]

        if class_id == 0 and score > 0.5:  # Detect 'person' with confidence > 0.5
            person_in_frame = True
            print(f"Person detected with confidence {score:.2f}")
        elif class_id == 16 and score > 0.7:  # Detect 'cat' with confidence > 0.7
            # Get bounding box coordinates (normalized)
            ymin, xmin, ymax, xmax = boxes[i]
            # Convert to pixel coordinates for 300x300 image
            xmin = int(xmin * 300)
            xmax = int(xmax * 300)
            ymin = int(ymin * 300)
            ymax = int(ymax * 300)
            # Calculate width and height
            width = xmax - xmin
            height = ymax - ymin
            # Filter by size: typical cat size is 50-100 pixels in width and height
            if 50 <= width <= 100 and 50 <= height <= 100:
                cat_in_frame = True
                cat_box = (xmin, ymin, xmax, ymax, width, height, score)
                print(f"Cat detected with confidence {score:.2f}, size: {width}x{height} px")
            else:
                print(f"Object classified as cat but filtered out due to size: {width}x{height} px")

    # Add current frame result to history
    history.append((cat_in_frame, person_in_frame))

    # Check the last 5 frames
    cat_count = sum(1 for cat, person in history if cat and not person)
    person_in_history = any(person for cat, person in history)

    # Confirm cat presence if detected in 3+ frames and no person is present
    cat_present = cat_count >= 3 and not person_in_history

    current_time = time.time()  # Current timestamp for timing logic

    if cat_present and not cat_detected:
        # Cat detected for the first time
        cat_detected = True
        sound_start_time = current_time
        print("Cat confirmed!")

        # Get current date and time for the Telegram message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Cat detected! Date and time: {timestamp} with confidence {cat_box[6]:.2f}"

        # Send a text message to Telegram
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={'chat_id': chat_id, 'text': message}
        )
        if response.status_code == 200:
            print("Message with date and time sent to Telegram")
        else:
            print(f"Error sending message: {response.text}")

        # Prepare 3 frames with bounding boxes for Telegram
        frames_with_boxes = []
        for _ in range(3):
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            # Resize frame to 300x300 for consistency with detection
            frame_resized = cv2.resize(frame, (300, 300))
            if cat_box:
                xmin, ymin, xmax, ymax, width, height, score = cat_box
                # Draw bounding box
                cv2.rectangle(frame_resized, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                # Add text with size and confidence
                label = f"Cat: {width}x{height} px, {score:.2f}"
                cv2.putText(frame_resized, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            frames_with_boxes.append(frame_resized)
            time.sleep(1)  # Delay between captures

        # Send a start signal to the ESP32 to activate the vibromotor
        try:
            requests.get(f'{esp_ip}/start')
            print("Signal /start sent to ESP32")
        except requests.exceptions.RequestException as e:
            print(f"Error sending /start to ESP32: {e}")

        # Start sending photos in a background thread
        threading.Thread(target=send_photos_in_background, args=(frames_with_boxes,), daemon=True).start()

    elif cat_present and cat_detected:
        # Cat continues to be in the frame
        sound_start_time = current_time

    elif not cat_present and cat_detected:
        # Cat is no longer in the frame, check if 10 seconds have passed
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