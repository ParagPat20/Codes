#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <WiFi.h>
#include <WebServer.h>
#include "config.h"
#include "motion.h"

// WiFi credentials
const char* ssid = "HexapodRobot";  // Set your WiFi AP name
const char* password = "12345678";  // Set your WiFi password

// Create WebServer object
WebServer server(80);

// Create two PCA9685 instances
Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40);  // Default I2C address
Adafruit_PWMServoDriver pca2 = Adafruit_PWMServoDriver(0x42);  // Second PCA9685

#define SERVO_FREQ 50  // 50 Hz update rate for servos

// Cytron Motor Control Pins
#define PWM1_PIN 18
#define PWM2_PIN 33
#define DIR1_PIN 19
#define DIR2_PIN 32

// Current motion state
MotionMode currentMode = MODE_TEST_SERVOS;  // Initialize in test servos mode
int currentPhase = 0;
unsigned long lastMotionUpdate = 0;

// Add this global variable to track rolling completion
bool rollingComplete = false;

// HTML page
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
<html>
<head>
  <title>Hexapod Control</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial; text-align: center; margin: 20px; }
    .button {
      background-color: #4CAF50;
      border: none;
      color: white;
      padding: 15px 32px;
      text-align: center;
      display: inline-block;
      font-size: 16px;
      margin: 4px 2px;
      cursor: pointer;
      border-radius: 4px;
    }
    .active { background-color: #45a049; }
    .standby { background-color: #008CBA; }
    .test { background-color: #f44336; }
    
    .servo-controls {
      display: none;
      max-width: 800px;
      margin: 20px auto;
      text-align: left;
      padding: 10px;
    }
    .servo-group {
      border: 1px solid #ddd;
      margin: 10px 0;
      padding: 10px;
      border-radius: 4px;
    }
    .servo-group h3 {
      margin: 0 0 10px 0;
    }
    .servo-item {
      margin: 5px 0;
      display: flex;
      align-items: center;
    }
    .servo-item label {
      width: 100px;
    }
    .servo-item input[type="range"] {
      flex: 1;
      margin: 0 10px;
    }
    .servo-item span {
      width: 50px;
      text-align: right;
    }
    .motor-controls {
      max-width: 800px;
      margin: 20px auto;
      text-align: center;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    .speed-control {
      margin: 20px 0;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }
    .speed-control input[type="range"] {
      width: 200px;
    }
    .motor-buttons {
      display: flex;
      justify-content: center;
      gap: 20px;
    }
    .motor-button {
      padding: 15px 30px;
      font-size: 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      user-select: none;
      touch-action: manipulation;
    }
    .motor-button.forward {
      background-color: #4CAF50;
      color: white;
    }
    .motor-button.backward {
      background-color: #f44336;
      color: white;
    }
    .motor-button:active {
      opacity: 0.8;
    }
  </style>
</head>
<body>
  <h1>Hexapod Control</h1>
  <p>Current Mode: <span id="mode">%MODE%</span></p>
  <p>
    <button class="button standby" onclick="setMode('standby')">STANDBY</button>
    <button class="button active" onclick="setMode('forward')">FORWARD</button>
    <button class="button test" onclick="setMode('test_servos')">TEST MODE</button>
    <button class="button rolling" onclick="setMode('rolling')">ROLLING</button>
  </p>
  
  <div id="servo-controls" class="servo-controls">
    <!-- Left Front Leg -->
    <div class="servo-group">
      <h3>Left Front Leg</h3>
      <div class="servo-item">
        <label>Coxa (LFC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LFC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur (LFF)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LFF', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (LFT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LFT', this.value)">
        <span>90°</span>
      </div>
    </div>
    
    <!-- Left Mid Leg -->
    <div class="servo-group">
      <h3>Left Mid Leg</h3>
      <div class="servo-item">
        <label>Coxa (LMC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LMC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur 1 (LMF1)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LMF1', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur 2 (LMF2)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LMF2', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (LMT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LMT', this.value)">
        <span>90°</span>
      </div>
    </div>
    
    <!-- Left Rear Leg -->
    <div class="servo-group">
      <h3>Left Rear Leg</h3>
      <div class="servo-item">
        <label>Coxa (LRC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LRC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur (LRF)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LRF', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (LRT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('LRT', this.value)">
        <span>90°</span>
      </div>
    </div>
    
    <!-- Right Front Leg -->
    <div class="servo-group">
      <h3>Right Front Leg</h3>
      <div class="servo-item">
        <label>Coxa (RFC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RFC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur (RFF)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RFF', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (RFT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RFT', this.value)">
        <span>90°</span>
      </div>
    </div>
    
    <!-- Right Mid Leg -->
    <div class="servo-group">
      <h3>Right Mid Leg</h3>
      <div class="servo-item">
        <label>Coxa (RMC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RMC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur 1 (RMF1)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RMF1', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur 2 (RMF2)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RMF2', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (RMT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RMT', this.value)">
        <span>90°</span>
      </div>
    </div>
    
    <!-- Right Rear Leg -->
    <div class="servo-group">
      <h3>Right Rear Leg</h3>
      <div class="servo-item">
        <label>Coxa (RRC)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RRC', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Femur (RRF)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RRF', this.value)">
        <span>90°</span>
      </div>
      <div class="servo-item">
        <label>Tibia (RRT)</label>
        <input type="range" min="0" max="180" value="90" oninput="updateServo('RRT', this.value)">
        <span>90°</span>
      </div>
    </div>
  </div>

  <div id="motor-controls" class="motor-controls">
    <h3>Motor Control</h3>
    <div class="speed-control">
      <label>Speed: </label>
      <input type="range" id="motorSpeed" min="0" max="255" value="128" oninput="updateSpeedDisplay(this.value)">
      <span id="speedDisplay">128</span>
    </div>
    <div class="motor-buttons">
      <button class="motor-button forward" onmousedown="setMotor(1)" onmouseup="setMotor(0)" ontouchstart="setMotor(1)" ontouchend="setMotor(0)">
        Forward ▲
      </button>
      <button class="motor-button backward" onmousedown="setMotor(-1)" onmouseup="setMotor(0)" ontouchstart="setMotor(-1)" ontouchend="setMotor(0)">
        Backward ▼
      </button>
    </div>
  </div>

  <script>
    // Add function to update all servo sliders
    function updateAllServoSliders() {
      fetch('/getCurrentAngles')
        .then(response => response.json())
        .then(data => {
          // Update each servo slider
          Object.keys(data).forEach(id => {
            const slider = document.querySelector(`input[oninput*="${id}"]`);
            const span = slider.nextElementSibling;
            if (slider) {
              slider.value = data[id];
              span.textContent = data[id] + '°';
            }
          });
        });
    }

    function setMode(mode) {
      fetch('/mode?set=' + mode)
        .then(response => response.text())
        .then(data => {
          document.getElementById('mode').innerText = data;
          const servoControls = document.getElementById('servo-controls');
          servoControls.style.display = (data === 'TEST_SERVOS') ? 'block' : 'none';
          if (data === 'TEST_SERVOS') {
            updateAllServoSliders();  // Update sliders when entering test mode
          }
        });
    }
    
    function updateServo(id, value) {
      // Update display value
      const span = event.target.nextElementSibling;
      span.textContent = value + '°';
      
      // Send to server
      fetch('/servo?id=' + id + '&angle=' + value)
        .then(response => response.text())
        .then(data => {
          console.log(data);
        });
    }
    
    // Initialize servo controls and update periodically in test mode
    document.addEventListener('DOMContentLoaded', function() {
      const mode = document.getElementById('mode').innerText;
      const servoControls = document.getElementById('servo-controls');
      servoControls.style.display = (mode === 'TEST_SERVOS') ? 'block' : 'none';
      
      if (mode === 'TEST_SERVOS') {
        updateAllServoSliders();
        // Update every 2 seconds while in test mode
        setInterval(() => {
          if (document.getElementById('mode').innerText === 'TEST_SERVOS') {
            updateAllServoSliders();
          }
        }, 2000);
      }
    });

    function updateSpeedDisplay(value) {
      document.getElementById('speedDisplay').textContent = value;
    }

    function setMotor(direction) {
      const speed = document.getElementById('motorSpeed').value;
      const actualSpeed = direction * speed;
      
      fetch('/motor?speed=' + actualSpeed)
        .then(response => response.text())
        .then(data => {
          console.log('Motor response:', data);
        });
    }
  </script>
</body>
</html>
)rawliteral";

// Helper function to find servo config by ID
const ServoConfig* findServoConfig(const char* id) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    if (strcmp(SERVO_CONFIG[i].id, id) == 0) {  // Use strcmp for string comparison
      return &SERVO_CONFIG[i];
    }
  }
  return nullptr;
}

void setServoAngle(const char* id, int angle) {
  const ServoConfig* config = findServoConfig(id);
  if (!config) {
    Serial.print("Invalid servo ID: ");
    Serial.println(id);
    return;
  }

  // Constrain angle to valid range
  angle = constrain(angle, 0, 180);

  // Print detailed debug info
  Serial.print("Setting servo ");
  Serial.print(id);
  Serial.print(" (");
  Serial.print(config->old_id);
  Serial.print(") Channel=");
  Serial.print(config->channel);
  Serial.print(" Angle=");
  Serial.print(angle);

  // Convert angle to pulse length
  int pulseLength = map(angle, 0, 180, 102, 512);
  Serial.print(" Pulse=");
  Serial.println(pulseLength);

  // Determine which PCA9685 to use based on old_id prefix
  if (config->old_id[0] == 'L') {  // Left side servos on PCA1
    pca1.setPWM(config->channel, 0, pulseLength);
  } else {  // Right side servos on PCA2
    pca2.setPWM(config->channel, 0, pulseLength);
  }
}

void moveToStandby() {
  Serial.println("Moving to standby position...");
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(STANDBY_POSITION[i].id, STANDBY_POSITION[i].angle);
  }

  // Wait for servos to reach position
  delay(SERVO_MOVE_TIME);

  currentMode = MODE_STANDBY;
  Serial.println("Standby position reached");
}

void updateForwardMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY + SERVO_MOVE_TIME) {
    return;  // Wait for both movement and delay time
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    const ServoMove& move = FORWARD_SEQUENCE[currentPhase][i];
    if (move.id != nullptr) {
      // Find standby position for this servo
      const ServoPosition* standbyPos = nullptr;
      for (int j = 0; j < NUM_STANDBY_POSITIONS; j++) {
        if (strcmp(STANDBY_POSITION[j].id, move.id) == 0) {
          standbyPos = &STANDBY_POSITION[j];
          break;
        }
      }

      if (standbyPos) {
        // Apply relative change to standby position
        int newAngle = standbyPos->angle + move.change;

        // Debug output
        Serial.print("Servo ");
        Serial.print(move.id);
        Serial.print(": Standby=");
        Serial.print(standbyPos->angle);
        Serial.print(" Change=");
        Serial.print(move.change);
        Serial.print(" New=");
        Serial.println(newAngle);

        setServoAngle(move.id, newAngle);
      }
    } else {
      // No change, use standby position
      setServoAngle(STANDBY_POSITION[i].id, STANDBY_POSITION[i].angle);
    }
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_FORWARD_PHASES;
  lastMotionUpdate = millis();

  Serial.print("Forward phase: ");
  Serial.print(currentPhase);
  Serial.print(" (Move time: ");
  Serial.print(SERVO_MOVE_TIME);
  Serial.print("ms, Delay: ");
  Serial.print(MOTION_DELAY);
  Serial.println("ms)");
}

void updateTestServosMotion() {
  static unsigned long lastDebugUpdate = 0;
  const unsigned long DEBUG_INTERVAL = 1000;  // Print positions every second

  if (millis() - lastDebugUpdate >= DEBUG_INTERVAL) {
    Serial.println("\nCurrent Servo Positions:");
    for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
      const ServoPosition& pos = STANDBY_POSITION[i];
      Serial.print(pos.id);
      Serial.print(": ");
      Serial.println(pos.angle);
    }
    lastDebugUpdate = millis();
  }
}

void updateRollingMotion() {
  if (rollingComplete) {
    return;  // Don't do anything if rolling is complete
  }

  if (millis() - lastMotionUpdate < MOTION_DELAY + SERVO_MOVE_TIME) {
    return;  // Wait for both movement and delay time
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    const ServoPosition& pos = ROLLING_SEQUENCE[currentPhase][i];
    setServoAngle(pos.id, pos.angle);
  }

  delay(500);

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_ROLLING_PHASES;
  lastMotionUpdate = millis();

  // Check if we've completed one full sequence
  if (currentPhase == 0) {
    rollingComplete = true;
    Serial.println("Rolling sequence complete");
  }

  Serial.print("Rolling phase: ");
  Serial.print(currentPhase);
  Serial.print(" (Move time: ");
  Serial.print(SERVO_MOVE_TIME);
  Serial.print("ms, Delay: ");
  Serial.print(MOTION_DELAY);
  Serial.println("ms)");
}

void setMotionMode(MotionMode mode) {
  if (mode != currentMode) {
    Serial.print("Motion mode changing from ");
    Serial.print(getMotionModeName(currentMode));
    Serial.print(" to ");
    Serial.println(getMotionModeName(mode));

    currentMode = mode;
    currentPhase = 0;
    lastMotionUpdate = 0;

    if (mode == MODE_STANDBY) {
      moveToStandby();
    } else if (mode == MODE_ROLLING) {
      rollingComplete = false;  // Reset rolling state when entering roll mode
    }
  }
}

// Helper function to get mode name
const char* getMotionModeName(MotionMode mode) {
  switch (mode) {
    case MODE_STANDBY: return "STANDBY";
    case MODE_FORWARD: return "FORWARD";
    case MODE_TEST_SERVOS: return "TEST_SERVOS";
    case MODE_ROLLING: return "ROLLING";
    default: return "UNKNOWN";
  }
}

void setupWiFi() {
  // Create WiFi network
  WiFi.softAP(ssid, password);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);
}

void setupWebServer() {
  // Route for root / web page
  server.on("/", HTTP_GET, []() {
    String html = String(index_html);
    html.replace("%MODE%", getMotionModeName(currentMode));
    server.send(200, "text/html", html);
  });

  // Route for mode control
  server.on("/mode", HTTP_GET, []() {
    if (server.hasArg("set")) {
      String mode = server.arg("set");
      if (mode == "forward") {
        setMotionMode(MODE_FORWARD);
      } else if (mode == "standby") {
        setMotionMode(MODE_STANDBY);
      } else if (mode == "test_servos") {
        setMotionMode(MODE_TEST_SERVOS);
      } else if (mode == "rolling") {
        setMotionMode(MODE_ROLLING);
      }
    }
    server.send(200, "text/plain", getMotionModeName(currentMode));
  });

  // New route for servo control
  server.on("/servo", HTTP_GET, []() {
    if (server.hasArg("id") && server.hasArg("angle")) {
      String id = server.arg("id");
      int angle = server.arg("angle").toInt();

      if (currentMode == MODE_TEST_SERVOS) {
        setServoAngle(id.c_str(), angle);
        server.send(200, "text/plain", "OK");
      } else {
        server.send(400, "text/plain", "Not in test mode");
      }
    } else {
      server.send(400, "text/plain", "Missing parameters");
    }
  });

  // Add new route to get current angles
  server.on("/getCurrentAngles", HTTP_GET, []() {
    String json = "{";
    for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
      if (i > 0) json += ",";
      json += "\"" + String(STANDBY_POSITION[i].id) + "\":" + String(STANDBY_POSITION[i].angle);
    }
    json += "}";
    server.send(200, "application/json", json);
  });

  // Add motor control route
  server.on("/motor", HTTP_GET, []() {
    if (server.hasArg("speed")) {
      int speed = server.arg("speed").toInt();
      // Use the existing setMotorSpeed function for PWM2/DIR2
      setMotorSpeed("RDC", speed);
      server.send(200, "text/plain", "OK");
    } else {
      server.send(400, "text/plain", "Missing speed parameter");
    }
  });

  server.begin();
  Serial.println("HTTP server started");
}

// Add this function to check PCA9685 drivers
bool checkPCADrivers() {
  Wire.beginTransmission(0x40);  // Check PCA1
  bool pca1_ok = (Wire.endTransmission() == 0);

  Wire.beginTransmission(0x42);  // Check PCA2
  bool pca2_ok = (Wire.endTransmission() == 0);

  Serial.println("\nChecking PCA9685 drivers:");
  Serial.print("PCA1 (0x40): ");
  Serial.println(pca1_ok ? "OK" : "NOT FOUND");
  Serial.print("PCA2 (0x42): ");
  Serial.println(pca2_ok ? "OK" : "NOT FOUND");

  return pca1_ok && pca2_ok;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  Serial.println("\nInitializing Hexapod...");

  // Check PCA drivers before initialization
  if (!checkPCADrivers()) {
    Serial.println("ERROR: One or both PCA9685 drivers not found!");
    Serial.println("Please check connections and addresses.");
    Serial.println("System halted.");
    while (1) {
      delay(1000);
      // Flash LED or other indicator if available
    }
  }

  // Initialize PCA9685 drivers
  Serial.println("\nInitializing PCA9685 drivers...");

  bool init_ok = true;

  try {
    pca1.begin();
    pca1.setPWMFreq(SERVO_FREQ);
    Serial.println("PCA1 initialized successfully");
  } catch (...) {
    Serial.println("Error initializing PCA1");
    init_ok = false;
  }

  try {
    pca2.begin();
    pca2.setPWMFreq(SERVO_FREQ);
    Serial.println("PCA2 initialized successfully");
  } catch (...) {
    Serial.println("Error initializing PCA2");
    init_ok = false;
  }

  if (!init_ok) {
    Serial.println("Failed to initialize one or both PCA9685 drivers!");
    Serial.println("System halted.");
    while (1) {
      delay(1000);
      // Flash LED or other indicator if available
    }
  }

  // Initialize Cytron motor control pins
  pinMode(PWM1_PIN, OUTPUT);
  pinMode(PWM2_PIN, OUTPUT);
  pinMode(DIR1_PIN, OUTPUT);
  pinMode(DIR2_PIN, OUTPUT);

  // Initialize motors to stop
  analogWrite(PWM1_PIN, 0);
  analogWrite(PWM2_PIN, 0);
  digitalWrite(DIR1_PIN, LOW);
  digitalWrite(DIR2_PIN, LOW);

  // Setup WiFi and Web Server
  setupWiFi();
  setupWebServer();

  Serial.println("Initialization complete");
  Serial.println("Available commands:");
  Serial.println("- standby: Move to standby position");
  Serial.println("- forward: Start forward walking sequence");
  Serial.println("- rolling: Start rolling motion sequence");
  Serial.println("- test_servos: Enter servo testing mode");
  Serial.println("- Servo control: LFC:90 or L00:90 format");
  Serial.print("Connect to WiFi AP '");
  Serial.print(ssid);
  Serial.println("' to access web control");
  Serial.print("Then navigate to http://");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  // Handle web server clients
  server.handleClient();

  // Handle serial commands
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    Serial.print("Received command: ");
    Serial.println(input);

    if (input == "forward") {
      setMotionMode(MODE_FORWARD);
      Serial.println("OK");
    } else if (input == "standby") {
      setMotionMode(MODE_STANDBY);
      Serial.println("OK");
    } else if (input == "test_servos") {
      setMotionMode(MODE_TEST_SERVOS);
      Serial.println("OK");
    } else if (input == "rolling") {
      setMotionMode(MODE_ROLLING);
      Serial.println("OK");
    } else if (currentMode == MODE_TEST_SERVOS) {
      parseAndSetServos(input);
      Serial.println("OK");
    } else {
      parseAndSetServos(input);
      Serial.println("OK");
    }
  }

  // Update motion if needed
  switch (currentMode) {
    case MODE_FORWARD:
      updateForwardMotion();
      break;
    case MODE_STANDBY:
      if (currentMode != MODE_TEST_SERVOS) {
        moveToStandby();
      }
      break;
    case MODE_TEST_SERVOS:
      updateTestServosMotion();
      break;
    case MODE_ROLLING:
      updateRollingMotion();
      break;
    default:
      break;
  }
}

void parseAndSetServos(String command) {
  if (command.length() < 3) {
    Serial.println("Invalid command length");
    return;
  }

  // Check if it's a direct channel command (e.g., "L00:90" or "R04:120")
  if (command[0] == 'L' || command[0] == 'R') {
    if (isDigit(command[1])) {
      int colonPos = command.indexOf(':');
      if (colonPos > 0) {
        String channelStr = command.substring(1, colonPos);
        int channel = channelStr.toInt();
        int angle = command.substring(colonPos + 1).toInt();

        Serial.print("Direct channel command - Board: ");
        Serial.print(command[0]);
        Serial.print(" Channel: ");
        Serial.print(channel);
        Serial.print(" Angle: ");
        Serial.println(angle);

        if (angle >= 0 && angle <= 180) {
          int pulseLength = map(angle, 0, 180, 102, 512);
          if (command[0] == 'L') {
            pca1.setPWM(channel, 0, pulseLength);
          } else {
            pca2.setPWM(channel, 0, pulseLength);
          }
          Serial.println("OK");
          return;
        }
      }
    }
    Serial.println("Invalid command format");
    return;
  }

  // Handle leg-joint format (e.g., "LFC:90" or "RMF1:120")
  String servoId = command.substring(0, command.indexOf(':'));
  int angle = command.substring(command.indexOf(':') + 1).toInt();

  Serial.print("Setting ");
  Serial.print(servoId);
  Serial.print(" to angle: ");
  Serial.println(angle);

  if (angle >= 0 && angle <= 180) {
    setServoAngle(servoId.c_str(), angle);
  } else {
    Serial.println("Invalid angle");
  }
}

void setMotorSpeed(String motor, int speed) {
  speed = constrain(speed, -255, 255);
  if (motor == "LDC") {
    digitalWrite(DIR1_PIN, speed >= 0 ? HIGH : LOW);
    analogWrite(PWM1_PIN, abs(speed));
  } else if (motor == "RDC") {
    digitalWrite(DIR2_PIN, speed >= 0 ? HIGH : LOW);
    analogWrite(PWM2_PIN, abs(speed));
    
    // Debug output
    Serial.print("Motor RDC - Direction: ");
    Serial.print(speed >= 0 ? "Forward" : "Backward");
    Serial.print(" Speed: ");
    Serial.println(abs(speed));
  }
}

// Add this function to get current servo angle
int getCurrentServoAngle(const char* id) {
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    if (strcmp(STANDBY_POSITION[i].id, id) == 0) {
      return STANDBY_POSITION[i].angle;
    }
  }
  return 90;  // Default angle if not found
}
