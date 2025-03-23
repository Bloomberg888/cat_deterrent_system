#include <WiFi.h>
#include <WebServer.h>
#include "Audio.h" // Assuming ESP32 Audio library

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Web server port
WebServer server(80);

// Audio object
Audio audio;

// Path to the sound file on ESP32 (e.g., on SD card or SPIFFS)
const char* sound_file = "/sounds/deterrent_sound.mp3"; // Adjust path

// Define I2S pins for MAX98357A (adjust according to your wiring)
const int bckPin = 25;
const int lrckPin = 26;
const int dataPin = 27;

void handleStart() {
  Serial.println("Received /start command - Playing sound");
  audio.connecttoFS(SD, sound_file); // Or audio.connecttoSPIFFS(sound_file); depending on where the file is
  audio.loop = true; // Loop the sound
  server.send(200, "text/plain", "Sound started");
}

void handleStop() {
  Serial.println("Received /stop command - Stopping sound");
  audio.stopSong();
  server.send(200, "text/plain", "Sound stopped");
}

void handleNotFound() {
  server.send(404, "text/plain", "Not found");
}

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Sound Player");

  // Initialize SD card (if used)
  // if (!SD.begin()) {
  //   Serial.println("SD Card Mount Failed");
  //   return;
  // }

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Configure I2S for MAX98357A
  audio.setPinout(bckPin, lrckPin, dataPin);
  audio.setVolume(21); // Adjust volume (0-21)

  // Set up web server routes
  server.on("/start", HTTP_GET, handleStart);
  server.on("/stop", HTTP_GET, handleStop);
  server.onNotFound(handleNotFound);

  // Start the server
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  audio.loopSong(); // Keep the audio stream going if playing
}