/*
 * ESP32 Slave PCA9685 16-Channel Servo Controller (ESP-NOW Version)
 * 
 * Controls up to 16 servos via PCA9685 PWM driver board using direct PWM tick values
 * Receives commands via ESP-NOW from master ESP32 (connected to PC)
 * 
 * Setup Instructions:
 * 1. Upload this sketch to ESP32 Slave (on robot)
 * 2. Open Serial Monitor and note the MAC address displayed
 * 3. Copy this MAC address to the master ESP32 sketch
 * 4. This ESP32 will now receive commands wirelessly from the master
 * 
 * Requirements:
 * - ESP32 Arduino Core 2.0.0 or higher (3.0.0+ recommended)
 * - Adafruit PWM Servo Driver Library (for PCA9685)
 * - Wire library (I2C, included in Arduino)
 * 
 * Based on ESP-NOW best practices from:
 * https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/
 * 
 * Serial Commands (received via ESP-NOW):
 * - "TICK <channel> <value>"     : Set PWM tick value (0-4095) on channel (0-15)
 * - "ANGLE <channel> <angle>"    : Set servo angle (0.0-180.0) using calibrated tick values
 * - "CAL <channel> <min> <max>"  : Set tick calibration for channel (min/max ticks for 0/180 degrees)
 * - "CAL_ALL <min> <max>"        : Set tick calibration for all channels
 * - "GET_CAL <channel>"          : Get calibration values for a channel
 * - "GET_ALL_CAL"                : Get all calibration values
 * - "FREQ <frequency>"            : Set PWM frequency in Hz (40-1000, typical 50)
 * - "SLEEP"                       : Put PCA9685 in sleep mode
 * - "WAKE"                        : Wake PCA9685 from sleep mode
 * - "RESET"                       : Reset PCA9685 to default settings
 * - "INFO"                        : Print current configuration
 * 
 * Wiring:
 * PCA9685 SDA -> ESP32 GPIO21 (default I2C SDA)
 * PCA9685 SCL -> ESP32 GPIO22 (default I2C SCL)
 * PCA9685 VCC -> 5V
 * PCA9685 GND -> GND
 * PCA9685 V+  -> External 5-6V power supply for servos
 */

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <MPU6050_tockn.h>

// PCA9685 I2C address (default is 0x40)
#define PCA9685_ADDRESS 0x40

// Default PWM tick values (12-bit resolution: 0-4095)
// These are reasonable defaults for most servos at 50Hz
#define TICK_MIN_DEFAULT 102    // ~500us at 50Hz (102 ticks)
#define TICK_MAX_DEFAULT 512    // ~2500us at 50Hz (512 ticks)

// Default PWM frequency for servos (Hz)
#define SERVO_FREQ_DEFAULT 50

// Create PCA9685 driver object
Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(PCA9685_ADDRESS);

// MOSFET Power Control Pin (N-Channel low-side switch)
// Labeled D5 on schematic (GPIO 19)
#define MOSFET_PIN 19

// DC Motor Control Pins (Verified from schematic)
#define MOTOR_PWM_PIN 32
#define MOTOR_DIR_PIN 33

// MPU6050 Configuration & Variables
#define MPU6050_ADDRESS 0x68
MPU6050 mpu(Wire);
bool mpuInitialized = false;
float accelAngle = 0.0;
float gyroAngle = 0.0;
float filteredAngle = 0.0;
unsigned long lastMpuUpdate = 0;

// Telemetry & ESP-NOW target
uint8_t masterMac[6];
bool hasMasterMac = false;
bool telemetryEnabled = false;
unsigned long lastTelemetryTime = 0;
const unsigned long TELEMETRY_INTERVAL = 100; // 100 ms interval (10 Hz)

// ============================================================
// Data Structures for ESP-NOW (Match exactly with master)
// ============================================================

// Master -> Slave Command Structure
typedef struct cmd_struct {
  char command[16];
  int val1;
  int val2;
  float val3;
} cmd_struct;

// Slave -> Master Telemetry/Response Structure
typedef struct telemetry_struct {
  char type[10];
  char message[128];
  float pitch;
} telemetry_struct;

cmd_struct myCmd;
telemetry_struct myData;

// Servo configuration structure using tick values
struct ServoConfig {
  uint16_t tickMin;     // Minimum PWM tick value (0 degrees)
  uint16_t tickMax;     // Maximum PWM tick value (180 degrees)
  uint16_t currentTick; // Current PWM tick value
  float lastAngle;      // Last set angle (0.0-180.0)
};

// Configuration for all 16 channels
ServoConfig servoConfigs[16];
uint16_t pwmFrequency = SERVO_FREQ_DEFAULT;

// ESP-NOW command buffer
String commandBuffer = "";

// Function prototypes
void initESPNow();
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data, int len);
void sendResponse(const char* response, const uint8_t *mac_addr);
void printMacAddress();

void setServoPWM(uint8_t channel, uint16_t tickValue);
void setServoAngle(uint8_t channel, float angle);
void setPWMFrequency(uint16_t freq);
void setCalibration(uint8_t channel, uint16_t minTick, uint16_t maxTick);
void setAllCalibrations(uint16_t minTick, uint16_t maxTick);
void getCalibration(uint8_t channel, const uint8_t *senderMac);
void getAllCalibrations(const uint8_t *senderMac);
void resetToDefaults();
void printInfo(const uint8_t *senderMac);
void processCommand(String command, const uint8_t *senderMac);

// New Helper Functions
bool initMPU6050();
void updateMPU();
void setMotorSpeed(int speed);
void setTorque(int state);
void sendTelemetry();

void setup() {
  // Configure and turn on MOSFET power control pin
  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(MOSFET_PIN, LOW); // Start at No torque (fully off)
  delay(100); // Wait for power to stabilize

  // Configure DC Motor pins
  pinMode(MOTOR_DIR_PIN, OUTPUT);
  pinMode(MOTOR_PWM_PIN, OUTPUT);
  digitalWrite(MOTOR_DIR_PIN, LOW);
  analogWrite(MOTOR_PWM_PIN, 0); // Start with motor stopped

  // Initialize serial communication for debugging
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n========================================");
  Serial.println("ESP32 Slave PCA9685 Controller - ESP-NOW");
  Serial.println("========================================");
  
  // Print MAC address (needed for master configuration)
  Serial.print("\n*** SLAVE MAC ADDRESS: ");
  printMacAddress();
  Serial.println("*** Copy this MAC to master ESP32 sketch ***\n");
  
  // Initialize ESP-NOW
  initESPNow();
  
  // Initialize I2C
  Wire.begin();

  // Initialize MPU6050
  Serial.println("Initializing MPU6050...");
  mpuInitialized = initMPU6050();
  if (mpuInitialized) {
    Serial.println("MPU6050 initialized successfully");
    lastMpuUpdate = millis();
  } else {
    Serial.println("ERROR: MPU6050 not found on I2C bus!");
  }
  
  // Initialize PCA9685
  Serial.println("Initializing PCA9685...");
  pca.begin();
  
  // Set initial PWM frequency
  pca.setPWMFreq(SERVO_FREQ_DEFAULT);
  
  // Initialize all servo configurations to defaults
  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = TICK_MIN_DEFAULT;
    servoConfigs[i].tickMax = TICK_MAX_DEFAULT;
    servoConfigs[i].currentTick = (TICK_MIN_DEFAULT + TICK_MAX_DEFAULT) / 2;
    servoConfigs[i].lastAngle = 90.0;
    // Set all channels to center position (90 degrees)
    setServoAngle(i, 90.0);
  }
  
  Serial.println("PCA9685 initialized successfully");
  Serial.println("Default frequency: 50 Hz");
  Serial.println("Default tick range: 102-512 (approx 500-2500μs)");


  Serial.println("\nReady to receive ESP-NOW commands...");
  Serial.println("==========================================\n");
}

void loop() {
  // Update MPU6050 readings and complementary filter
  if (mpuInitialized) {
    updateMPU();
  }
  
  // Send periodic telemetry to Master
  if (telemetryEnabled && hasMasterMac && (millis() - lastTelemetryTime >= TELEMETRY_INTERVAL)) {
    lastTelemetryTime = millis();
    sendTelemetry();
  }
  
  delay(5);
}

// Initialize ESP-NOW
void initESPNow() {
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);
  
  WiFi.disconnect();

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW initialization failed!");
    return;
  }
  
  Serial.println("ESP-NOW initialized successfully");
  
  // Register receive callback (compatible with ESP32 Core 3.0.0+)
  esp_now_register_recv_cb(onDataRecv);
}

// Callback when data is received via ESP-NOW
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data, int len) {
  // Save master MAC address for telemetry
  if (!hasMasterMac) {
    memcpy(masterMac, recvInfo->src_addr, 6);
    hasMasterMac = true;
    Serial.printf("Master MAC locked: %02X:%02X:%02X:%02X:%02X:%02X\n",
                  masterMac[0], masterMac[1], masterMac[2],
                  masterMac[3], masterMac[4], masterMac[5]);
  }

  // Expect structured data packets per RNT strategy
  if (len == sizeof(cmd_struct)) {
    memcpy(&myCmd, data, sizeof(myCmd));
    
    // Reconstruct string to reuse our robust processCommand logic
    String cmdStr = String(myCmd.command);
    
    if (cmdStr == "MOTOR" || cmdStr == "TORQUE" || cmdStr == "FREQ" || cmdStr == "GET_CAL" || cmdStr == "TELEMETRY") {
      cmdStr += " " + String(myCmd.val1);
    } 
    else if (cmdStr == "ANGLE" || cmdStr == "CAL_ALL") {
      cmdStr += " " + String(myCmd.val1) + " " + String(myCmd.val3, 1);
    } 
    else if (cmdStr == "TICK") {
      cmdStr += " " + String(myCmd.val1) + " " + String(myCmd.val2);
    }
    else if (cmdStr == "CAL") {
      cmdStr += " " + String(myCmd.val1) + " " + String(myCmd.val2) + " " + String(myCmd.val3, 0);
    }
    
    // Debug output
    Serial.print("Received (Structured): ");
    Serial.println(cmdStr);
    
    // Process command
    processCommand(cmdStr, recvInfo->src_addr);
  }
}

// Send response back to master via ESP-NOW using struct
void sendResponse(const char* response, const uint8_t *mac_addr) {
  // Add peer if not already added
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, mac_addr, 6);
  peerInfo.channel = 0;      // Auto/default channel
  peerInfo.encrypt = false;
  
  // Try to add peer (will fail if already exists, which is fine)
  esp_now_add_peer(&peerInfo);
  
  // Pack into telemetry_struct
  memset(&myData, 0, sizeof(myData));
  strcpy(myData.type, "INFO");
  strncpy(myData.message, response, sizeof(myData.message) - 1);
  
  // Remove trailing newline if present since Master Serial.println adds it
  int len = strlen(myData.message);
  if (len > 0 && myData.message[len-1] == '\n') {
    myData.message[len-1] = '\0';
  }
  
  // Send structured response
  esp_now_send(mac_addr, (uint8_t *)&myData, sizeof(myData));
  
  // Also print to Serial for debugging
  Serial.print("Response: ");
  Serial.println(myData.message);
}

// Print this device's MAC address
void printMacAddress() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  for (int i = 0; i < 6; i++) {
    Serial.printf("%02X", mac[i]);
    if (i < 5) Serial.print(":");
  }
  Serial.println();
}

// ==================== Command Processing ====================

// Process received command (same logic as original Serial version)
void processCommand(String command, const uint8_t *senderMac) {
  command.toUpperCase();
  command.trim();
  
  char responseBuffer[256];
  
  // TICK command: "TICK <channel> <value>"
  if (command.startsWith("TICK ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (secondSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      int tickValue = command.substring(secondSpace + 1).toInt();
      
      if (channel >= 0 && channel < 16 && tickValue >= 0 && tickValue <= 4095) {
        setServoPWM(channel, tickValue);
        snprintf(responseBuffer, sizeof(responseBuffer), 
                 "OK: Channel %d set to tick %d\n", channel, tickValue);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid channel (0-15) or tick value (0-4095)\n", senderMac);
      }
    } else {
      sendResponse("ERROR: Invalid TICK command format. Use: TICK <channel> <value>\n", senderMac);
    }
  }
  
  // ANGLE command: "ANGLE <channel> <angle>"
  else if (command.startsWith("ANGLE ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (secondSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      float angle = command.substring(secondSpace + 1).toFloat();
      
      if (channel >= 0 && channel < 16 && angle >= 0.0 && angle <= 180.0) {
        setServoAngle(channel, angle);
        snprintf(responseBuffer, sizeof(responseBuffer), 
                 "OK: Channel %d set to %.1f degrees\n", channel, angle);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid channel (0-15) or angle (0.0-180.0)\n", senderMac);
      }
    } else {
      sendResponse("ERROR: Invalid ANGLE command format. Use: ANGLE <channel> <angle>\n", senderMac);
    }
  }
  
  // CAL command: "CAL <channel> <min_tick> <max_tick>"
  else if (command.startsWith("CAL ") && !command.startsWith("CAL_")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    int thirdSpace = command.indexOf(' ', secondSpace + 1);
    
    if (thirdSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      int minTick = command.substring(secondSpace + 1, thirdSpace).toInt();
      int maxTick = command.substring(thirdSpace + 1).toInt();
      
      if (channel >= 0 && channel < 16 && minTick >= 0 && maxTick > minTick && maxTick <= 4095) {
        setCalibration(channel, minTick, maxTick);
        snprintf(responseBuffer, sizeof(responseBuffer), 
                 "OK: Channel %d calibration set to %d-%d\n", channel, minTick, maxTick);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid channel or tick range (0 < min < max <= 4095)\n", senderMac);
      }
    } else {
      sendResponse("ERROR: Invalid CAL command format. Use: CAL <channel> <min> <max>\n", senderMac);
    }
  }
  
  // CAL_ALL command: "CAL_ALL <min_tick> <max_tick>"
  else if (command.startsWith("CAL_ALL ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (secondSpace > 0) {
      int minTick = command.substring(firstSpace + 1, secondSpace).toInt();
      int maxTick = command.substring(secondSpace + 1).toInt();
      
      if (minTick >= 0 && maxTick > minTick && maxTick <= 4095) {
        setAllCalibrations(minTick, maxTick);
        snprintf(responseBuffer, sizeof(responseBuffer), 
                 "OK: All channels calibration set to %d-%d\n", minTick, maxTick);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid tick range (0 < min < max <= 4095)\n", senderMac);
      }
    } else {
      sendResponse("ERROR: Invalid CAL_ALL command format. Use: CAL_ALL <min> <max>\n", senderMac);
    }
  }
  
  // GET_CAL command: "GET_CAL <channel>"
  else if (command.startsWith("GET_CAL ")) {
    int channel = command.substring(8).toInt();
    if (channel >= 0 && channel < 16) {
      getCalibration(channel, senderMac);
    } else {
      sendResponse("ERROR: Invalid channel (0-15)\n", senderMac);
    }
  }
  
  // GET_ALL_CAL command
  else if (command == "GET_ALL_CAL") {
    getAllCalibrations(senderMac);
  }
  
  // FREQ command: "FREQ <frequency>"
  else if (command.startsWith("FREQ ")) {
    int freq = command.substring(5).toInt();
    
    if (freq >= 40 && freq <= 1000) {
      setPWMFrequency(freq);
      snprintf(responseBuffer, sizeof(responseBuffer), 
               "OK: PWM frequency set to %d Hz\n", freq);
      sendResponse(responseBuffer, senderMac);
    } else {
      sendResponse("ERROR: Invalid frequency (40-1000 Hz)\n", senderMac);
    }
  }
  
  // SLEEP command
  else if (command == "SLEEP") {
    pca.sleep();
    sendResponse("OK: PCA9685 sleep mode enabled\n", senderMac);
  }
  
  // WAKE command
  else if (command == "WAKE") {
    pca.wakeup();
    sendResponse("OK: PCA9685 woken up\n", senderMac);
  }
  
  // RESET command
  else if (command == "RESET") {
    resetToDefaults();
    sendResponse("OK: Reset to default configuration\n", senderMac);
    printInfo(senderMac);
  }
  
  // MOTOR command: "MOTOR <speed>"
  else if (command.startsWith("MOTOR ")) {
    int speed = command.substring(6).toInt();
    if (speed >= -255 && speed <= 255) {
      setMotorSpeed(speed);
      snprintf(responseBuffer, sizeof(responseBuffer), "OK: Motor speed set to %d\n", speed);
      sendResponse(responseBuffer, senderMac);
    } else {
      sendResponse("ERROR: Speed must be between -255 and 255\n", senderMac);
    }
  }
  
  // TORQUE command: "TORQUE <1/0>"
  else if (command.startsWith("TORQUE ")) {
    int state = command.substring(7).toInt();
    if (state == 0 || state == 1) {
      setTorque(state);
      snprintf(responseBuffer, sizeof(responseBuffer), "OK: Torque set to %s\n", state ? "HIGH" : "LOW");
      sendResponse(responseBuffer, senderMac);
    } else {
      sendResponse("ERROR: Torque state must be 0 or 1\n", senderMac);
    }
  }
  
  // RESET_MPU command
  else if (command == "RESET_MPU") {
    gyroAngle = 0.0;
    if (mpuInitialized) {
      mpu.update();
      filteredAngle = atan2(mpu.getAccY(), mpu.getAccX()) * 180.0 / M_PI;
    } else {
      filteredAngle = 0.0;
    }
    sendResponse("OK: MPU6050 angles reset\n", senderMac);
  }
  
  // GET_MPU command
  else if (command == "GET_MPU") {
    if (!mpuInitialized) {
      sendResponse("ERROR: MPU6050 not initialized\n", senderMac);
    } else {
      char mpuBuffer[64];
      snprintf(mpuBuffer, sizeof(mpuBuffer), "MPU_DATA %.2f %.2f %.2f\n",
               filteredAngle, accelAngle, gyroAngle);
      sendResponse(mpuBuffer, senderMac);
    }
  }
  
  // TELEMETRY command: "TELEMETRY <1/0>"
  else if (command.startsWith("TELEMETRY ")) {
    int enable = command.substring(10).toInt();
    telemetryEnabled = (enable != 0);
    if (telemetryEnabled && !mpuInitialized) {
      sendResponse("WARNING: Telemetry ENABLED but MPU6050 not initialized!\n", senderMac);
    } else {
      snprintf(responseBuffer, sizeof(responseBuffer), "OK: Telemetry %s\n", telemetryEnabled ? "ENABLED" : "DISABLED");
      sendResponse(responseBuffer, senderMac);
    }
  }

  // INFO command
  else if (command == "INFO") {
    printInfo(senderMac);
  }
  
  // Unknown command
  else {
    sendResponse("ERROR: Unknown command\n", senderMac);
  }
}

// ==================== Servo Control Functions ====================

// Set PWM directly using tick value (0-4095)
void setServoPWM(uint8_t channel, uint16_t tickValue) {
  if (channel >= 16 || tickValue > 4095) {
    return;
  }
  
  // Store the current tick value
  servoConfigs[channel].currentTick = tickValue;
  
  // Set PWM on channel using setPWM(channel, on, off)
  // on=0 means pulse starts at beginning of cycle
  // off=tickValue means pulse ends at this tick count
  pca.setPWM(channel, 0, tickValue);
}

// Set servo angle using calibrated tick values
void setServoAngle(uint8_t channel, float angle) {
  if (channel >= 16 || angle < 0.0 || angle > 180.0) {
    return;
  }
  
  // Store the angle
  servoConfigs[channel].lastAngle = angle;
  
  // Map angle (0.0-180.0) to tick value using calibration
  uint16_t tickMin = servoConfigs[channel].tickMin;
  uint16_t tickMax = servoConfigs[channel].tickMax;
  
  // Linear interpolation: tick = tickMin + (angle/180.0) * (tickMax - tickMin)
  float tickFloat = tickMin + (angle / 180.0) * (tickMax - tickMin);
  uint16_t tickValue = (uint16_t)(tickFloat + 0.5); // Round to nearest integer
  
  // Clamp to valid range
  if (tickValue < tickMin) tickValue = tickMin;
  if (tickValue > tickMax) tickValue = tickMax;
  if (tickValue > 4095) tickValue = 4095;
  
  // Set the PWM
  setServoPWM(channel, tickValue);
}

// Set PWM frequency
void setPWMFrequency(uint16_t freq) {
  if (freq < 40 || freq > 1000) {
    return;
  }
  
  pwmFrequency = freq;
  pca.setPWMFreq(freq);
  
  // Re-apply all servo angles with new frequency
  for (int i = 0; i < 16; i++) {
    setServoAngle(i, servoConfigs[i].lastAngle);
  }
}

// Set calibration for a single channel
void setCalibration(uint8_t channel, uint16_t minTick, uint16_t maxTick) {
  if (channel >= 16 || minTick >= maxTick || maxTick > 4095) {
    return;
  }
  
  servoConfigs[channel].tickMin = minTick;
  servoConfigs[channel].tickMax = maxTick;
  
  // Re-apply the servo angle with new calibration
  setServoAngle(channel, servoConfigs[channel].lastAngle);
}

// Set calibration for all channels
void setAllCalibrations(uint16_t minTick, uint16_t maxTick) {
  if (minTick >= maxTick || maxTick > 4095) {
    return;
  }
  
  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = minTick;
    servoConfigs[i].tickMax = maxTick;
    setServoAngle(i, servoConfigs[i].lastAngle);
  }
}

// Get calibration for a specific channel
void getCalibration(uint8_t channel, const uint8_t *senderMac) {
  if (channel >= 16) {
    return;
  }
  
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "CAL_DATA %d %d %d\n",
           channel,
           servoConfigs[channel].tickMin,
           servoConfigs[channel].tickMax);
  sendResponse(buffer, senderMac);
}

// Get all calibrations
void getAllCalibrations(const uint8_t *senderMac) {
  sendResponse("ALL_CAL_DATA\n", senderMac);
  delay(10);
  
  for (int i = 0; i < 16; i++) {
    char buffer[128];
    snprintf(buffer, sizeof(buffer), "%d %d %d\n",
             i,
             servoConfigs[i].tickMin,
             servoConfigs[i].tickMax);
    sendResponse(buffer, senderMac);
    delay(10);
  }
  
  sendResponse("END_CAL_DATA\n", senderMac);
}

// Reset to default configuration
void resetToDefaults() {
  pwmFrequency = SERVO_FREQ_DEFAULT;
  pca.setPWMFreq(pwmFrequency);
  
  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = TICK_MIN_DEFAULT;
    servoConfigs[i].tickMax = TICK_MAX_DEFAULT;
    servoConfigs[i].lastAngle = 90.0;
    setServoAngle(i, 90.0);
  }
}

// Print current configuration
void printInfo(const uint8_t *senderMac) {
  char buffer[256];
  
  sendResponse("\n========== Current Configuration ==========\n", senderMac);
  delay(10);
  
  snprintf(buffer, sizeof(buffer), "PWM Frequency: %d Hz\n", pwmFrequency);
  sendResponse(buffer, senderMac);
  delay(10);
  
  sendResponse("\nChannel Configuration:\n", senderMac);
  delay(10);
  
  sendResponse("Ch  | Angle  | Curr Tick | Tick Min | Tick Max\n", senderMac);
  delay(10);
  
  sendResponse("----|--------|-----------|----------|----------\n", senderMac);
  delay(10);
  
  for (int i = 0; i < 16; i++) {
    snprintf(buffer, sizeof(buffer), "%2d  | %6.1f | %4d      | %4d     | %4d\n",
             i,
             servoConfigs[i].lastAngle,
             servoConfigs[i].currentTick,
             servoConfigs[i].tickMin,
             servoConfigs[i].tickMax);
    sendResponse(buffer, senderMac);
    delay(10);
  }
  
  sendResponse("==========================================\n\n", senderMac);
}

// ==================== New Helper Functions ====================

// Initialize MPU6050 using tockn library
bool initMPU6050() {
  mpu.begin();
  Serial.println("Calculating gyro offsets, keep the robot still...");
  mpu.calcGyroOffsets(true);
  Serial.println("Offsets calculated!");
  return true;
}

// Read sensor events and update complementary filter (Z-axis rotation / X-Y plane pitch)
void updateMPU() {
  unsigned long now = millis();
  float dt = (now - lastMpuUpdate) / 1000.0;
  lastMpuUpdate = now;
  if (dt <= 0.0) dt = 0.001; // Avoid divide by zero
  
  mpu.update();
  
  // Calculate accelerometer pitch angle (assuming rotation is around local Z-axis,
  // meaning gravity component rotates in local X-Y plane)
  float accX = mpu.getAccX();
  float accY = mpu.getAccY();
  accelAngle = atan2(accY, accX) * 180.0 / M_PI;
  
  // Gyroscope rate around Z axis
  float gyroRate = mpu.getGyroZ();
  
  // Integrate gyro rate
  gyroAngle += gyroRate * dt;
  
  // Complementary filter
  filteredAngle = 0.98 * (filteredAngle + gyroRate * dt) + 0.02 * accelAngle;
}

// Drive DC Motor with PWM and Direction
void setMotorSpeed(int speed) {
  if (speed > 255) speed = 255;
  if (speed < -255) speed = -255;
  
  if (speed >= 0) {
    digitalWrite(MOTOR_DIR_PIN, HIGH);
    analogWrite(MOTOR_PWM_PIN, speed);
  } else {
    digitalWrite(MOTOR_DIR_PIN, LOW);
    analogWrite(MOTOR_PWM_PIN, -speed);
  }
}

// Set MOSFET Torque control state (0 or 1)
void setTorque(int state) {
  digitalWrite(MOSFET_PIN, state ? HIGH : LOW);
}

// Send Live Telemetry to Master over ESP-NOW
void sendTelemetry() {
  if (!hasMasterMac) return;

  // Add peer if not already added
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterMac, 6);
  peerInfo.channel = 0;      // Auto/default channel
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo); // Fails gracefully if already added
  
  // Pack into telemetry_struct
  memset(&myData, 0, sizeof(myData));
  strcpy(myData.type, "MPU");
  myData.pitch = filteredAngle;
  
  esp_now_send(masterMac, (uint8_t *)&myData, sizeof(myData));
}

