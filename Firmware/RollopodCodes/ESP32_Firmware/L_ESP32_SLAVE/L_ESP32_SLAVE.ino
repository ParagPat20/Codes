/*
 * ESP32 Slave PCA9685 16-Channel Servo Controller & Closed-Loop Motor PID
 * (ESP-NOW Version)
 *
 * Controls up to 16 servos via PCA9685 PWM driver board.
 * Receives commands via ESP-NOW from master ESP32 (connected to PC).
 * Includes Closed-Loop PID Motor Speed Control & Active Zero-Speed Position
 * Hold using Quadrature Encoder on GPIO 1 (Encoder A) and GPIO 0 (Encoder B).
 *
 * Wiring:
 * ENCODER A  -> GPIO 1 (Input Pullup, Interrupt)
 * ENCODER B  -> GPIO 0 (Input Pullup, Interrupt)
 * MOSFET PIN -> GPIO 18 (IRL84132PBF 12V Rail Gate Control)
 * MOTOR PWM  -> GPIO 19 (MD13S PWM)
 * MOTOR DIR  -> GPIO 17 (MD13S DIR)
 * I2C SDA    -> GPIO 21 (PCA9685 & MPU6050 SDA)
 * I2C SCL    -> GPIO 22 (PCA9685 & MPU6050 SCL)
 */

#include <Adafruit_PWMServoDriver.h>
#include <ArduinoOTA.h>
#include <MPU6050_tockn.h>
#include <WiFi.h>
#include <Wire.h>
#include <esp_idf_version.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ============================================================
// WIRELESS ARDUINOTA OVER-THE-AIR CONFIGURATION (SSID: MIBEE)
// ============================================================
bool otaModeActive = false;
const char *OTA_WIFI_SSID = "MIBEE";
const char *OTA_WIFI_PASS = ""; // Open Network (No Password)

void enableWirelessOTA(const char *hostname) {
  Serial.printf("\n[OTA] Switching to Wi-Fi STA mode and connecting to %s...\n", OTA_WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(OTA_WIFI_SSID, OTA_WIFI_PASS);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 6000) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[OTA] Connected! IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[OTA WARNING] Could not connect to MIBEE network within 6s");
  }

  ArduinoOTA.setHostname(hostname);
  ArduinoOTA.onStart([]() { Serial.println("[OTA] Wireless Update Starting..."); });
  ArduinoOTA.onEnd([]() { Serial.println("\n[OTA] Update Complete! Rebooting..."); });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("[OTA] Error[%u]\n", error);
  });

  ArduinoOTA.begin();
  otaModeActive = true;
  Serial.printf("[OTA] Wireless ArduinoOTA Ready! Hostname: %s.local\n", hostname);
}

#define PCA9685_ADDRESS 0x40
#define TICK_MIN_DEFAULT 102
#define TICK_MAX_DEFAULT 512
#define SERVO_FREQ_DEFAULT 50

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(PCA9685_ADDRESS);

// ============================================================
// PIN ASSIGNMENTS (Seeed Studio XIAO ESP32-C6 / EasyEDA Schematic)
// ============================================================
#define ENCODER_A_PIN 1
#define ENCODER_B_PIN 0
#define MOSFET_PIN 18
#define MOTOR_PWM_PIN 19
#define MOTOR_DIR_PIN 17
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// ============================================================
// QUADRATURE ENCODER & CLOSED-LOOP PID MOTOR CONTROLLER
// ============================================================
volatile long encoderTicks = 0;
volatile int encoderState = 0;

void IRAM_ATTR encoderISR() {
  int a = digitalRead(ENCODER_A_PIN);
  int b = digitalRead(ENCODER_B_PIN);
  int currState = (a << 1) | b;
  int sum = (encoderState << 2) | currState;

  if (sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011)
    encoderTicks++;
  if (sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000)
    encoderTicks--;

  encoderState = currState;
}

// Closed-Loop PID Parameters & Control Variables (Rhino IG32 Planetary Motor 9048 CPR @ 12V)
float Kp = 1.8f;
float Ki = 0.25f;
float Kd = 0.03f;
float encoderCPR = 9048.0f; // High Torque Quad Encoder CPR

bool closedLoopEnabled = true;
float targetRPM = 0.0f;
float measuredRPM = 0.0f;
long lastEncoderTicks = 0;
unsigned long lastPidTime = 0;

float pidIntegral = 0.0f;
float lastPidError = 0.0f;
long targetHoldPos = 0;
bool isHoldingPosition = false;
int currentMotorPWM = 0;

// Stall detection & thermal protection
unsigned long stallStartTime = 0;
bool stallDetected = false;
const unsigned long STALL_TIMEOUT_MS = 400;  // Cut output after 400ms stall
const int STALL_PWM_THRESHOLD = 60;          // PWM above this = actively trying to move
const float STALL_RPM_THRESHOLD = 2.0f;      // RPM below this = considered stalled

void setMotorHardwareSpeed(int speed) {
  speed = constrain(speed, -255, 255);
  currentMotorPWM = speed;
  if (speed == 0) {
    digitalWrite(MOTOR_DIR_PIN, LOW);
    analogWrite(MOTOR_PWM_PIN, 0);
  } else if (speed > 0) {
    digitalWrite(MOTOR_DIR_PIN, HIGH);
    analogWrite(MOTOR_PWM_PIN, speed);
  } else {
    digitalWrite(MOTOR_DIR_PIN, LOW);
    analogWrite(MOTOR_PWM_PIN, -speed);
  }
}

void updateClosedLoopControl() {
  unsigned long now = millis();
  float dt = (now - lastPidTime) / 1000.0f;
  if (dt < 0.02f)
    return; // 50Hz update loop (every 20ms)
  lastPidTime = now;

  long currentTicks;
  noInterrupts();
  currentTicks = encoderTicks;
  interrupts();

  long dTicks = currentTicks - lastEncoderTicks;
  lastEncoderTicks = currentTicks;

  // Calculate actual measured RPM from High-Resolution 9048 CPR Encoder (GPIO 0 & 1)
  measuredRPM = ((float)dTicks / encoderCPR) * (60.0f / dt);

  // Active Zero-Speed High-Resolution Encoder Position Lock (Degree-Scaled Instant Response)
  if (targetRPM == 0.0f) {
    if (!isHoldingPosition) {
      targetHoldPos = currentTicks;
      isHoldingPosition = true;
      pidIntegral = 0.0f;
      lastPidError = 0.0f;
      stallDetected = false;
      stallStartTime = 0;
    }

    long posError = targetHoldPos - currentTicks;

    // Deadband: 20 ticks (~0.8 deg) — avoids micro-corrections that heat the motor
    if (labs(posError) <= 20) {
      setMotorHardwareSpeed(0);
      pidIntegral = 0.0f;
      lastPidError = 0.0f;
      stallDetected = false;
      stallStartTime = 0;
      return;
    }

    // Convert encoder ticks error directly into degrees of rotation
    float degError = (float)posError / (encoderCPR / 360.0f);

    pidIntegral += degError * dt;
    pidIntegral = constrain(pidIntegral, -50.0f, 50.0f); // Anti-heating integral cap
    float dError = (degError - lastPidError) / dt;
    lastPidError = degError;

    float dirSign = (degError > 0) ? 1.0f : -1.0f;
    float baseFrictionPWM = dirSign * 35.0f; // Continuous breakaway threshold for 5kg wheel

    // High-sensitivity position counter-torque using GUI Kp, Ki, Kd gains on degrees of error!
    float outputPWM = baseFrictionPWM + (degError * Kp) + (pidIntegral * Ki) + (dError * Kd);
    outputPWM = constrain(outputPWM, -255.0f, 255.0f);

    // --- STALL DETECTION & THERMAL PROTECTION ---
    // If we're pushing hard but motor isn't moving = stall = dangerous heat buildup
    bool isStalling = (abs((int)outputPWM) >= STALL_PWM_THRESHOLD) &&
                      (fabs(measuredRPM) < STALL_RPM_THRESHOLD);
    if (isStalling) {
      if (stallStartTime == 0) {
        stallStartTime = now; // Start stall timer
      } else if ((now - stallStartTime) >= STALL_TIMEOUT_MS) {
        // Stalled too long — cut power to protect motor from overheating
        setMotorHardwareSpeed(0);
        stallDetected = true;
        // Snap hold position forward to reduce the error so we don't immediately retry
        targetHoldPos = currentTicks;
        pidIntegral = 0.0f;
        return;
      }
    } else {
      // Motor is moving — reset stall state
      stallStartTime = 0;
      stallDetected = false;
    }

    // Don't try again immediately after a stall — give motor 200ms cool-down
    if (stallDetected) {
      return;
    }

    setMotorHardwareSpeed((int)outputPWM);
    return;
  } else {
    isHoldingPosition = false;
    stallDetected = false;
    stallStartTime = 0;
  }

  if (!closedLoopEnabled) {
    setMotorHardwareSpeed((int)targetRPM);
    return;
  }

  // Closed-Loop Encoder Speed Control for Target RPM (With Feedforward for 100RPM/255PWM)
  float error = targetRPM - measuredRPM;
  pidIntegral += error * dt;
  pidIntegral = constrain(pidIntegral, -150.0f, 150.0f); // Anti-windup

  float dError = (error - lastPidError) / dt;
  lastPidError = error;

  float feedforwardPWM = targetRPM * 2.1f; // ~2.1 PWM units per RPM feedforward
  float outputPWM = feedforwardPWM + (Kp * error) + (Ki * pidIntegral) + (Kd * dError);
  outputPWM = constrain(outputPWM, -255.0f, 255.0f);

  setMotorHardwareSpeed((int)outputPWM);
}

void setupAntenna() {
#if defined(CONFIG_IDF_TARGET_ESP32C6) ||                                      \
    defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW);
  delay(100);
  pinMode(14, OUTPUT);
  digitalWrite(14, LOW);
  Serial.println("[ANTENNA] XIAO ESP32-C6: Internal PCB Antenna Configured "
                 "(GPIO3=LOW, GPIO14=LOW)");
#else
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board");
#endif
}

#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif

unsigned long lastSlaveLedToggle = 0;
bool slaveLedState = false;
int slaveBurstToggles = 0;
unsigned long lastMasterCommandTime = 0;
const unsigned long MASTER_AVAILABLE_TIMEOUT_MS = 2500;

void updateSlaveLed() {
  unsigned long now = millis();

  // OTA Mode Active: Continuous Fast 15Hz Blinking (65ms toggle interval)
  if (otaModeActive) {
    if (now - lastSlaveLedToggle >= 65) {
      lastSlaveLedToggle = now;
      slaveLedState = !slaveLedState;
      digitalWrite(LED_BUILTIN, slaveLedState ? HIGH : LOW);
    }
    return;
  }

  if (slaveBurstToggles > 0) {
    if (now - lastSlaveLedToggle >= 35) {
      lastSlaveLedToggle = now;
      slaveLedState = !slaveLedState;
      digitalWrite(LED_BUILTIN, slaveLedState ? HIGH : LOW);
      slaveBurstToggles--;
    }
    return;
  }

  bool isMasterAvailable =
      (now - lastMasterCommandTime < MASTER_AVAILABLE_TIMEOUT_MS);

  if (!isMasterAvailable) {
    digitalWrite(LED_BUILTIN, LOW);
  } else {
    if (now - lastSlaveLedToggle >= 500) {
      lastSlaveLedToggle = now;
      slaveLedState = !slaveLedState;
      digitalWrite(LED_BUILTIN, slaveLedState ? HIGH : LOW);
    }
  }
}

#define MPU6050_ADDRESS 0x68
MPU6050 mpu(Wire);
bool mpuInitialized = false;
float accelAngle = 0.0;
float gyroAngle = 0.0;
float filteredAngle = 0.0;
unsigned long lastMpuUpdate = 0;

uint8_t masterMac[6];
bool hasMasterMac = false;
bool telemetryEnabled = false;
unsigned long lastTelemetryTime = 0;
const unsigned long TELEMETRY_INTERVAL = 100;

typedef struct cmd_struct {
  char text[128];
} cmd_struct;

typedef struct telemetry_struct {
  char type[10];
  char message[128];
  float pitch;
} telemetry_struct;

cmd_struct myCmd;
telemetry_struct myData;

struct ServoConfig {
  uint16_t tickMin;
  uint16_t tickMax;
  uint16_t currentTick;
  float lastAngle;
};

// Configured Standing Pose Angles for Left Slave (from rollopod_servo_profile.json)
const float DEFAULT_STANDING_ANGLES[16] = {
  128.0f,  // CH 00: Left Rear Coxa
  50.0f,   // CH 01: Left Rear Femur
  70.0f,   // CH 02: Left Rear Tibia
  90.0f,   // CH 03: Unassigned
  95.0f,   // CH 04: Left Middle Coxa
  15.0f,   // CH 05: Left Middle Femur
  70.0f,   // CH 06: Left Middle Patella
  160.0f,  // CH 07: Left Middle Tibia
  65.0f,   // CH 08: Left Front Coxa
  50.0f,   // CH 09: Left Front Femur
  70.0f,   // CH 10: Left Front Tibia
  90.0f,   // CH 11: Unassigned
  90.0f,   // CH 12: Unassigned
  90.0f,   // CH 13: Unassigned
  90.0f,   // CH 14: Unassigned
  90.0f    // CH 15: Unassigned
};

ServoConfig servoConfigs[16];
uint16_t pwmFrequency = SERVO_FREQ_DEFAULT;
String commandBuffer = "";

void initESPNow();
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data,
                int len);
void sendResponse(const char *response, const uint8_t *mac_addr);
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

bool initMPU6050();
void updateMPU();
void setMotorSpeed(int speed);
void setTorque(int state);
void sendTelemetry();

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  setupAntenna();

  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(MOSFET_PIN, LOW);
  delay(100);

  pinMode(MOTOR_DIR_PIN, OUTPUT);
  pinMode(MOTOR_PWM_PIN, OUTPUT);
  digitalWrite(MOTOR_DIR_PIN, LOW);
  analogWrite(MOTOR_PWM_PIN, 0);

  // Configure Encoder Pins & Attach Interrupts (GPIO1 = Encoder A, GPIO0 = Encoder B)
  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(ENCODER_B_PIN, INPUT_PULLUP);
  int initA = digitalRead(ENCODER_A_PIN);
  int initB = digitalRead(ENCODER_B_PIN);
  encoderState = (initA << 1) | initB;
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), encoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_B_PIN), encoderISR, CHANGE);

  Serial.begin(115200);
#if defined(ARDUINO_USB_CDC_ON_BOOT) && (ARDUINO_USB_CDC_ON_BOOT == 1)
  Serial.setTxTimeoutMs(0);
#endif
  delay(500);

  Serial.println("\n\n========================================");
  Serial.println("ESP32-C6 Slave PCA9685 & Encoder PID Controller - ESP-NOW");
  Serial.println("========================================");

  initESPNow();

  Serial.print("\n*** SLAVE MAC ADDRESS: ");
  printMacAddress();
  Serial.println("*** Copy this MAC to master ESP32 sketch ***\n");

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  Serial.println("Initializing MPU6050...");
  mpuInitialized = initMPU6050();
  if (mpuInitialized) {
    Serial.println("MPU6050 initialized successfully");
    lastMpuUpdate = millis();
  } else {
    Serial.println("ERROR: MPU6050 not found on I2C bus!");
  }

  Serial.println("Initializing PCA9685...");
  pca.begin();
  pca.setPWMFreq(SERVO_FREQ_DEFAULT);

  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = TICK_MIN_DEFAULT;
    servoConfigs[i].tickMax = TICK_MAX_DEFAULT;
    servoConfigs[i].currentTick = (TICK_MIN_DEFAULT + TICK_MAX_DEFAULT) / 2;
    servoConfigs[i].lastAngle = DEFAULT_STANDING_ANGLES[i];
    setServoAngle(i, DEFAULT_STANDING_ANGLES[i]);
  }

  targetHoldPos = encoderTicks;
  isHoldingPosition = true;
  setMotorHardwareSpeed(0);

  Serial.println(
      "Slave initialization complete - waiting for ESP-NOW commands...");
}

void loop() {
  if (otaModeActive) {
    ArduinoOTA.handle();
  }

  if (mpuInitialized) {
    updateMPU();
  }

  // Update Closed-Loop PID & Active Zero-Speed Position Hold Controller (50Hz)
  updateClosedLoopControl();

  if (telemetryEnabled && hasMasterMac &&
      (millis() - lastTelemetryTime >= TELEMETRY_INTERVAL)) {
    lastTelemetryTime = millis();
    sendTelemetry();
  }

  updateSlaveLed();
  delay(2);
}

void initESPNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW initialization failed!");
    return;
  }
  Serial.println("ESP-NOW initialized successfully");
  esp_now_register_recv_cb(onDataRecv);
}

#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data,
                int len) {
  const uint8_t *srcMac = recvInfo->src_addr;
#else
void onDataRecv(const uint8_t *srcMac, const uint8_t *data, int len) {
#endif
  lastMasterCommandTime = millis();

  if (!hasMasterMac) {
    memcpy(masterMac, srcMac, 6);
    hasMasterMac = true;
    Serial.printf("Master MAC locked: %02X:%02X:%02X:%02X:%02X:%02X\n",
                  masterMac[0], masterMac[1], masterMac[2], masterMac[3],
                  masterMac[4], masterMac[5]);
  }

  if (len == sizeof(cmd_struct)) {
    cmd_struct *cmd = (cmd_struct *)data;
    String cmdText = String(cmd->text);
    cmdText.trim();
    if (cmdText != "PING") {
      slaveBurstToggles = 8; // 4 fast blinks (8 toggles) on receiving command
    }
    processCommand(cmdText, srcMac);
  } else {
    Serial.printf("Received invalid data length: %d (expected %d)\n", len,
                  sizeof(cmd_struct));
  }
}

void sendResponse(const char *response, const uint8_t *mac_addr) {
  if (!mac_addr)
    return;
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, mac_addr, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  memset(&myData, 0, sizeof(myData));
  strcpy(myData.type, "RESP");
  strncpy(myData.message, response, sizeof(myData.message) - 1);
  myData.pitch = filteredAngle;

  esp_now_send(mac_addr, (uint8_t *)&myData, sizeof(myData));
}

void printMacAddress() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n", mac[0], mac[1], mac[2],
                mac[3], mac[4], mac[5]);
}

void processCommand(String command, const uint8_t *senderMac) {
  command.trim();
  char responseBuffer[128];

  if (command == "PING") {
    sendResponse("PONG\n", senderMac);
  } else if (command == "OTA_MODE" || command == "ENTER_OTA") {
    enableWirelessOTA("rollopod-left-slave");
    sendResponse("OK: OTA Mode Enabled on Left Slave\n", senderMac);
  } else if (command.startsWith("TICK ")) {
    int space1 = command.indexOf(' ');
    int space2 = command.indexOf(' ', space1 + 1);
    if (space1 > 0 && space2 > space1) {
      int channel = command.substring(space1 + 1, space2).toInt();
      int tickValue = command.substring(space2 + 1).toInt();
      if (channel >= 0 && channel < 16 && tickValue >= 0 && tickValue <= 4095) {
        setServoPWM(channel, tickValue);
        snprintf(responseBuffer, sizeof(responseBuffer),
                 "OK: Channel %d set to %d ticks\n", channel, tickValue);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid channel (0-15) or tick value (0-4095)\n",
                     senderMac);
      }
    }
  } else if (command.startsWith("ANGLE ")) {
    int space1 = command.indexOf(' ');
    int space2 = command.indexOf(' ', space1 + 1);
    if (space1 > 0 && space2 > space1) {
      int channel = command.substring(space1 + 1, space2).toInt();
      float angle = command.substring(space2 + 1).toFloat();
      if (channel >= 0 && channel < 16 && angle >= 0.0 && angle <= 180.0) {
        setServoAngle(channel, angle);
        snprintf(responseBuffer, sizeof(responseBuffer),
                 "OK: Channel %d set to %.1f deg\n", channel, angle);
        sendResponse(responseBuffer, senderMac);
      } else {
        sendResponse("ERROR: Invalid channel (0-15) or angle (0-180)\n",
                     senderMac);
      }
    } else if (command.startsWith("ANGLE ALL ")) {
      float angle = command.substring(10).toFloat();
      if (angle >= 0.0 && angle <= 180.0) {
        for (int i = 0; i < 16; i++)
          setServoAngle(i, angle);
        snprintf(responseBuffer, sizeof(responseBuffer),
                 "OK: All 16 channels set to %.1f deg\n", angle);
        sendResponse(responseBuffer, senderMac);
      }
    }
  } else if (command == "STAND" || command == "STAND_POSE" || command == "HOME") {
    for (int i = 0; i < 16; i++) {
      setServoAngle(i, DEFAULT_STANDING_ANGLES[i]);
    }
    sendResponse("OK: Left Slave moved to Standing Pose\n", senderMac);
  } else if (command.startsWith("MOTOR ") || command.startsWith("RPM ")) {
    int spaceIdx = command.indexOf(' ');
    int speed = command.substring(spaceIdx + 1).toInt();
    if (speed >= -255 && speed <= 255) {
      targetRPM = (float)speed;
      if (targetRPM == 0.0f) {
        isHoldingPosition = false;
      }
      snprintf(responseBuffer, sizeof(responseBuffer),
               "OK: Motor target set to %d RPM (ClosedLoop=%s)\n", speed,
               closedLoopEnabled ? "ON" : "OFF");
      sendResponse(responseBuffer, senderMac);
    } else {
      sendResponse("ERROR: Speed must be between -255 and 255\n", senderMac);
    }
  } else if (command.startsWith("SET_PID ")) {
    float p = 0, i = 0, d = 0;
    if (sscanf(command.c_str() + 8, "%f %f %f", &p, &i, &d) == 3) {
      Kp = p;
      Ki = i;
      Kd = d;
      snprintf(responseBuffer, sizeof(responseBuffer),
               "OK: PID set to Kp=%.2f Ki=%.2f Kd=%.2f\n", Kp, Ki, Kd);
      sendResponse(responseBuffer, senderMac);
    } else {
      sendResponse("ERROR: Usage SET_PID <kp> <ki> <kd>\n", senderMac);
    }
  } else if (command.startsWith("SET_CPR ")) {
    float cpr = command.substring(8).toFloat();
    if (cpr > 0.0f) {
      encoderCPR = cpr;
      snprintf(responseBuffer, sizeof(responseBuffer),
               "OK: Encoder CPR set to %.1f\n", encoderCPR);
      sendResponse(responseBuffer, senderMac);
    }
  } else if (command.startsWith("CLOSED_LOOP ")) {
    int mode = command.substring(12).toInt();
    closedLoopEnabled = (mode != 0);
    snprintf(responseBuffer, sizeof(responseBuffer), "OK: Closed loop PID %s\n",
             closedLoopEnabled ? "ENABLED" : "DISABLED");
    sendResponse(responseBuffer, senderMac);
  } else if (command == "GET_ENCODER") {
    long currentTicks;
    noInterrupts();
    currentTicks = encoderTicks;
    interrupts();
    snprintf(responseBuffer, sizeof(responseBuffer),
             "ENCODER_DATA %ld %.1f %.1f\n", currentTicks, measuredRPM,
             targetRPM);
    sendResponse(responseBuffer, senderMac);
  } else if (command == "ENCODER_RESET") {
    noInterrupts();
    encoderTicks = 0;
    interrupts();
    targetHoldPos = 0;
    lastEncoderTicks = 0;
    sendResponse("OK: Encoder ticks reset to 0\n", senderMac);
  } else if (command.startsWith("TORQUE ")) {
    int state = command.substring(7).toInt();
    if (state == 0 || state == 1) {
      setTorque(state);
      snprintf(responseBuffer, sizeof(responseBuffer), "OK: Torque set to %s\n",
               state ? "HIGH" : "LOW");
      sendResponse(responseBuffer, senderMac);
    }
  } else if (command == "RESET_MPU") {
    gyroAngle = 0.0;
    if (mpuInitialized) {
      mpu.update();
      filteredAngle = atan2(mpu.getAccY(), mpu.getAccX()) * 180.0 / M_PI;
    } else {
      filteredAngle = 0.0;
    }
    sendResponse("OK: MPU6050 angles reset\n", senderMac);
  } else if (command == "GET_MPU") {
    if (!mpuInitialized) {
      sendResponse("ERROR: MPU6050 not initialized\n", senderMac);
    } else {
      char mpuBuffer[64];
      snprintf(mpuBuffer, sizeof(mpuBuffer), "MPU_DATA %.2f %.2f %.2f\n",
               filteredAngle, accelAngle, gyroAngle);
      sendResponse(mpuBuffer, senderMac);
    }
  } else if (command.startsWith("TELEMETRY ")) {
    int enable = command.substring(10).toInt();
    telemetryEnabled = (enable != 0);
    snprintf(responseBuffer, sizeof(responseBuffer), "OK: Telemetry %s\n",
             telemetryEnabled ? "ENABLED" : "DISABLED");
    sendResponse(responseBuffer, senderMac);
  } else if (command == "INFO") {
    printInfo(senderMac);
  } else {
    sendResponse("ERROR: Unknown command\n", senderMac);
  }
}

void setServoPWM(uint8_t channel, uint16_t tickValue) {
  if (channel >= 16 || tickValue > 4095)
    return;
  servoConfigs[channel].currentTick = tickValue;
  pca.setPWM(channel, 0, tickValue);
}

void setServoAngle(uint8_t channel, float angle) {
  if (channel >= 16 || angle < 0.0 || angle > 180.0)
    return;
  servoConfigs[channel].lastAngle = angle;
  uint16_t tickMin = servoConfigs[channel].tickMin;
  uint16_t tickMax = servoConfigs[channel].tickMax;
  float tickFloat = tickMin + (angle / 180.0) * (tickMax - tickMin);
  uint16_t tickValue = (uint16_t)(tickFloat + 0.5);
  if (tickValue < tickMin)
    tickValue = tickMin;
  if (tickValue > tickMax)
    tickValue = tickMax;
  if (tickValue > 4095)
    tickValue = 4095;
  setServoPWM(channel, tickValue);
}

void setPWMFrequency(uint16_t freq) {
  if (freq < 40 || freq > 1000)
    return;
  pwmFrequency = freq;
  pca.setPWMFreq(freq);
  for (int i = 0; i < 16; i++)
    setServoAngle(i, servoConfigs[i].lastAngle);
}

void setCalibration(uint8_t channel, uint16_t minTick, uint16_t maxTick) {
  if (channel >= 16 || minTick >= maxTick || maxTick > 4095)
    return;
  servoConfigs[channel].tickMin = minTick;
  servoConfigs[channel].tickMax = maxTick;
  setServoAngle(channel, servoConfigs[channel].lastAngle);
}

void setAllCalibrations(uint16_t minTick, uint16_t maxTick) {
  if (minTick >= maxTick || maxTick > 4095)
    return;
  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = minTick;
    servoConfigs[i].tickMax = maxTick;
    setServoAngle(i, servoConfigs[i].lastAngle);
  }
}

void getCalibration(uint8_t channel, const uint8_t *senderMac) {
  if (channel >= 16)
    return;
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "CAL_DATA %d %d %d\n", channel,
           servoConfigs[channel].tickMin, servoConfigs[channel].tickMax);
  sendResponse(buffer, senderMac);
}

void getAllCalibrations(const uint8_t *senderMac) {
  for (int i = 0; i < 16; i++)
    getCalibration(i, senderMac);
}

void resetToDefaults() {
  pwmFrequency = SERVO_FREQ_DEFAULT;
  pca.setPWMFreq(SERVO_FREQ_DEFAULT);
  for (int i = 0; i < 16; i++) {
    servoConfigs[i].tickMin = TICK_MIN_DEFAULT;
    servoConfigs[i].tickMax = TICK_MAX_DEFAULT;
    servoConfigs[i].currentTick = (TICK_MIN_DEFAULT + TICK_MAX_DEFAULT) / 2;
    servoConfigs[i].lastAngle = DEFAULT_STANDING_ANGLES[i];
    setServoAngle(i, DEFAULT_STANDING_ANGLES[i]);
  }
}

void printInfo(const uint8_t *senderMac) {
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "=== ESP32 Slave PCA9685 Info ===\n");
  sendResponse(buffer, senderMac);
  delay(10);
  snprintf(buffer, sizeof(buffer), "PWM Frequency: %d Hz\n", pwmFrequency);
  sendResponse(buffer, senderMac);
  delay(10);
  snprintf(buffer, sizeof(buffer),
           "Closed Loop PID: %s (Kp=%.2f Ki=%.2f Kd=%.2f)\n",
           closedLoopEnabled ? "ENABLED" : "DISABLED", Kp, Ki, Kd);
  sendResponse(buffer, senderMac);
  delay(10);
}

bool initMPU6050() {
  mpu.begin();
  Serial.println("Calculating gyro offsets, keep the robot still...");
  mpu.calcGyroOffsets(true);
  Serial.println("Offsets calculated!");
  return true;
}

void updateMPU() {
  unsigned long now = millis();
  float dt = (now - lastMpuUpdate) / 1000.0;
  lastMpuUpdate = now;
  if (dt <= 0.0)
    dt = 0.001;

  mpu.update();
  float accX = mpu.getAccX();
  float accY = mpu.getAccY();
  accelAngle = atan2(accY, accX) * 180.0 / M_PI;
  float gyroRate = mpu.getGyroZ();
  gyroAngle += gyroRate * dt;
  filteredAngle = 0.98 * (filteredAngle + gyroRate * dt) + 0.02 * accelAngle;
}

void setMotorSpeed(int speed) {
  targetRPM = (float)speed;
  if (targetRPM == 0.0f) {
    isHoldingPosition = false;
  }
}

void setTorque(int state) { digitalWrite(MOSFET_PIN, state ? HIGH : LOW); }

void sendTelemetry() {
  if (!hasMasterMac)
    return;

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterMac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  memset(&myData, 0, sizeof(myData));
  strcpy(myData.type, "MPU");
  myData.pitch = filteredAngle;

  long currentTicks;
  noInterrupts();
  currentTicks = encoderTicks;
  interrupts();
  snprintf(myData.message, sizeof(myData.message), "ENC %ld %.1f %.1f %d",
           currentTicks, measuredRPM, targetRPM, currentMotorPWM);

  esp_now_send(masterMac, (uint8_t *)&myData, sizeof(myData));
}
