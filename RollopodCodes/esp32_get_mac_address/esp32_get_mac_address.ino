#include <WiFi.h>

void setup() {
  // Initialize Serial Monitor
  Serial.begin(115200);
  
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_MODE_STA);
  
  // Wait a moment for serial to initialize
  delay(1000);
  
  // Print the MAC Address
  Serial.print("ESP32 Board MAC Address: ");
  Serial.println(WiFi.macAddress());
}

void loop() {
  // Do nothing
}
