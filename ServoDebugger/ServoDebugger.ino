#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <WiFi.h>
#include <WebServer.h>
#include <EEPROM.h>
#include <ArduinoJson.h>

// Create two PCA9685 instances
Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40);  // Default I2C address
Adafruit_PWMServoDriver pca2 = Adafruit_PWMServoDriver(0x42);  // Second PCA9685

#define SERVO_FREQ 50  // 50 Hz update rate for servos
#define EEPROM_SIZE 4096  // Size of EEPROM to use
#define SWEEP_STEP 5  // Step size for sweep (degrees)
#define SWEEP_DELAY 100  // Delay between sweep steps (ms)

// WiFi credentials for AP mode
const char* ssid = "HexapodDebugger";
const char* password = "12345678";

// Web server on port 80
WebServer server(80);

// Servo configuration structure
struct ServoConfig {
  int minAngle;
  int maxAngle;
  int offset;
  bool inverted;
  bool sweeping;  // Flag to track if servo is currently sweeping
};

// Store configuration for all servos (32 possible servos - 16 per PCA)
ServoConfig servoConfigs[32];

// Current servo angles
int currentAngles[32];

// Sweep direction (1 = increasing, -1 = decreasing)
int sweepDirections[32];

// Last sweep update time
unsigned long lastSweepUpdate = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  EEPROM.begin(EEPROM_SIZE);
  
  // Initialize PCA9685 instances
  pca1.begin();
  pca1.setPWMFreq(SERVO_FREQ);
  pca2.begin();
  pca2.setPWMFreq(SERVO_FREQ);

  // Load servo configurations from EEPROM
  loadConfigs();

  // Setup WiFi Access Point
  WiFi.softAP(ssid, password);
  Serial.println("Access Point Started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  // Setup web server routes
  server.on("/", handleRoot);
  server.on("/update", HTTP_POST, handleUpdate);
  server.on("/config", HTTP_POST, handleConfig);
  server.on("/save", HTTP_POST, handleSave);
  server.on("/sweep", HTTP_POST, handleSweep);  // New endpoint for sweep control
  server.begin();

  Serial.println("\nServo Debugger Ready!");
  Serial.println("Connect to WiFi AP:");
  Serial.println("SSID: " + String(ssid));
  Serial.println("Password: " + String(password));
}

void loop() {
  server.handleClient();
  
  // Update any active sweeps
  updateSweeps();
  
  // Handle serial commands for backward compatibility
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    handleSerialCommand(command);
  }
}

void updateSweeps() {
  if (millis() - lastSweepUpdate < SWEEP_DELAY) return;
  
  for (int i = 0; i < 32; i++) {
    if (servoConfigs[i].sweeping) {
      int pca = (i / 16) + 1;
      int channel = i % 16;
      
      // Update angle based on direction
      currentAngles[i] += (SWEEP_STEP * sweepDirections[i]);
      
      // Check if we need to reverse direction
      if (currentAngles[i] >= servoConfigs[i].maxAngle) {
        currentAngles[i] = servoConfigs[i].maxAngle;
        sweepDirections[i] = -1;
      } else if (currentAngles[i] <= servoConfigs[i].minAngle) {
        currentAngles[i] = servoConfigs[i].minAngle;
        sweepDirections[i] = 1;
      }
      
      setServoAngle(pca, channel, currentAngles[i]);
    }
  }
  
  lastSweepUpdate = millis();
}

void handleSweep() {
  int pca = server.arg("pca").toInt();
  int channel = server.arg("channel").toInt();
  bool start = server.arg("start") == "true";
  
  int servoIndex = ((pca-1) * 16) + channel;
  
  if (start) {
    // Start sweeping
    servoConfigs[servoIndex].sweeping = true;
    sweepDirections[servoIndex] = 1;  // Start increasing
    currentAngles[servoIndex] = servoConfigs[servoIndex].minAngle;  // Start from min
  } else {
    // Stop sweeping
    servoConfigs[servoIndex].sweeping = false;
  }
  
  server.send(200, "text/plain", "OK");
}

void loadConfigs() {
  // Initialize default values
  for (int i = 0; i < 32; i++) {
    servoConfigs[i].minAngle = 0;
    servoConfigs[i].maxAngle = 180;
    servoConfigs[i].offset = 0;
    servoConfigs[i].inverted = false;
    servoConfigs[i].sweeping = false;  // Initialize sweep state
    currentAngles[i] = 90;
    sweepDirections[i] = 1;  // Initialize sweep direction
  }
  
  // Try to load from EEPROM
  if (EEPROM.read(0) == 0xAA) {
    int addr = 1;
    for (int i = 0; i < 32; i++) {
      EEPROM.get(addr, servoConfigs[i]);
      addr += sizeof(ServoConfig);
    }
  }
}

void saveConfigs() {
  EEPROM.write(0, 0xAA); // Mark EEPROM as initialized
  int addr = 1;
  for (int i = 0; i < 32; i++) {
    EEPROM.put(addr, servoConfigs[i]);
    addr += sizeof(ServoConfig);
  }
  EEPROM.commit();
}

void handleRoot() {
  String html = "<html><head>";
  html += "<style>";
  html += "body { font-family: Arial; margin: 20px; }";
  html += ".slider-container { margin: 10px 0; display: flex; align-items: center; gap: 10px; }";
  html += ".config-container { background: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 5px; }";
  html += ".sweep-btn { margin-left: 10px; }";
  html += ".angle-input { width: 60px; }";
  html += "</style>";
  html += "<script>";
  html += "function updateServo(pca, channel) {";
  html += "  var slider = document.getElementById('servo_'+pca+'_'+channel);";
  html += "  var input = document.getElementById('angle_input_'+pca+'_'+channel);";
  html += "  var display = document.getElementById('angle_'+pca+'_'+channel);";
  html += "  var angle = slider.value;";
  html += "  input.value = angle;";
  html += "  display.textContent = angle + '°';";
  html += "  fetch('/update', {";
  html += "    method: 'POST',";
  html += "    headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
  html += "    body: 'pca='+pca+'&channel='+channel+'&angle='+angle";
  html += "  });";
  html += "}";
  html += "function updateFromInput(pca, channel) {";
  html += "  var input = document.getElementById('angle_input_'+pca+'_'+channel);";
  html += "  var slider = document.getElementById('servo_'+pca+'_'+channel);";
  html += "  var display = document.getElementById('angle_'+pca+'_'+channel);";
  html += "  var angle = parseInt(input.value) || 0;";
  html += "  angle = Math.min(Math.max(angle, slider.min), slider.max);";
  html += "  input.value = angle;";
  html += "  slider.value = angle;";
  html += "  display.textContent = angle + '°';";
  html += "  fetch('/update', {";
  html += "    method: 'POST',";
  html += "    headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
  html += "    body: 'pca='+pca+'&channel='+channel+'&angle='+angle";
  html += "  });";
  html += "}";
  html += "function updateConfig(pca, channel) {";
  html += "  var min = document.getElementById('min_'+pca+'_'+channel).value;";
  html += "  var max = document.getElementById('max_'+pca+'_'+channel).value;";
  html += "  var offset = document.getElementById('offset_'+pca+'_'+channel).value;";
  html += "  var inverted = document.getElementById('inv_'+pca+'_'+channel).checked;";
  html += "  var slider = document.getElementById('servo_'+pca+'_'+channel);";
  html += "  slider.min = min;";
  html += "  slider.max = max;";
  html += "  fetch('/config', {";
  html += "    method: 'POST',";
  html += "    headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
  html += "    body: 'pca='+pca+'&channel='+channel+'&min='+min+'&max='+max+'&offset='+offset+'&inverted='+inverted";
  html += "  });";
  html += "}";
  html += "function saveAll() {";
  html += "  fetch('/save', { method: 'POST' }).then(response => alert('Settings saved!'));";
  html += "}";
  html += "function toggleSweep(pca, channel, btn) {";
  html += "  var start = btn.textContent === 'Start Sweep';";
  html += "  fetch('/sweep', {";
  html += "    method: 'POST',";
  html += "    headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
  html += "    body: 'pca='+pca+'&channel='+channel+'&start='+start";
  html += "  }).then(() => {";
  html += "    btn.textContent = start ? 'Stop Sweep' : 'Start Sweep';";
  html += "  });";
  html += "}";
  html += "</script></head><body>";
  html += "<h1>Hexapod Servo Debugger</h1>";
  
  // Generate controls for each PCA and channel
  for (int pca = 1; pca <= 2; pca++) {
    html += "<h2>PCA" + String(pca) + "</h2>";
    for (int channel = 0; channel < 16; channel++) {
      int servoIndex = ((pca-1) * 16) + channel;
      ServoConfig &cfg = servoConfigs[servoIndex];
      
      html += "<div class='config-container'>";
      html += "<h3>Channel " + String(channel) + "</h3>";
      
      // Angle slider and input
      html += "<div class='slider-container'>";
      html += "Angle: <input type='range' id='servo_" + String(pca) + "_" + String(channel) + "' ";
      html += "min='" + String(cfg.minAngle) + "' max='" + String(cfg.maxAngle) + "' ";
      html += "value='" + String(currentAngles[servoIndex]) + "' ";
      html += "oninput='updateServo(" + String(pca) + "," + String(channel) + ")'>";
      html += "<input type='number' id='angle_input_" + String(pca) + "_" + String(channel) + "' ";
      html += "class='angle-input' value='" + String(currentAngles[servoIndex]) + "' ";
      html += "onchange='updateFromInput(" + String(pca) + "," + String(channel) + ")'>";
      html += "<span id='angle_" + String(pca) + "_" + String(channel) + "'>" + String(currentAngles[servoIndex]) + "°</span>";
      html += "<button class='sweep-btn' onclick='toggleSweep(" + String(pca) + "," + String(channel) + ",this)'>";
      html += cfg.sweeping ? "Stop Sweep" : "Start Sweep";
      html += "</button>";
      html += "</div>";
      
      // Configuration inputs
      html += "<div class='config-container'>";
      html += "Min: <input type='number' id='min_" + String(pca) + "_" + String(channel) + "' ";
      html += "value='" + String(cfg.minAngle) + "' style='width:60px'> ";
      html += "Max: <input type='number' id='max_" + String(pca) + "_" + String(channel) + "' ";
      html += "value='" + String(cfg.maxAngle) + "' style='width:60px'> ";
      html += "Offset: <input type='number' id='offset_" + String(pca) + "_" + String(channel) + "' ";
      html += "value='" + String(cfg.offset) + "' style='width:60px'> ";
      html += "Inverted: <input type='checkbox' id='inv_" + String(pca) + "_" + String(channel) + "' ";
      html += cfg.inverted ? "checked" : "";
      html += "> ";
      html += "<button onclick='updateConfig(" + String(pca) + "," + String(channel) + ")'>Apply</button>";
      html += "</div></div>";
    }
  }
  
  html += "<br><button onclick='saveAll()' style='font-size:1.2em;padding:10px'>Save All Settings</button>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

void handleUpdate() {
  int pca = server.arg("pca").toInt();
  int channel = server.arg("channel").toInt();
  int angle = server.arg("angle").toInt();
  
  int servoIndex = ((pca-1) * 16) + channel;
  currentAngles[servoIndex] = angle;
  
  setServoAngle(pca, channel, angle);
  server.send(200, "text/plain", "OK");
}

void handleConfig() {
  int pca = server.arg("pca").toInt();
  int channel = server.arg("channel").toInt();
  int servoIndex = ((pca-1) * 16) + channel;
  
  servoConfigs[servoIndex].minAngle = server.arg("min").toInt();
  servoConfigs[servoIndex].maxAngle = server.arg("max").toInt();
  servoConfigs[servoIndex].offset = server.arg("offset").toInt();
  servoConfigs[servoIndex].inverted = server.arg("inverted") == "true";
  
  server.send(200, "text/plain", "OK");
}

void handleSave() {
  saveConfigs();
  server.send(200, "text/plain", "OK");
}

void setServoAngle(int pca_num, int channel, int angle) {
  int servoIndex = ((pca_num-1) * 16) + channel;
  ServoConfig &cfg = servoConfigs[servoIndex];
  
  // Apply inversion if needed
  if (cfg.inverted) {
    angle = 180 - angle;
  }
  
  // Apply offset
  angle += cfg.offset;
  
  // Constrain to configured limits
  angle = constrain(angle, cfg.minAngle, cfg.maxAngle);
  
  // Convert angle to pulse length (0-180 degrees maps to 102-512 pulse length)
  int pulseLength = map(angle, 0, 180, 102, 512);
  
  if (pca_num == 1) {
    pca1.setPWM(channel, 0, pulseLength);
  } else {
    pca2.setPWM(channel, 0, pulseLength);
  }
  
  Serial.printf("Set PCA%d CH%d to %d° (adjusted: %d°)\n", pca_num, channel, currentAngles[servoIndex], angle);
}

void handleSerialCommand(String command) {
  if (command.startsWith("test ")) {
    command = command.substring(5);
    int pca_num = command.toInt();
    command = command.substring(command.indexOf(' ') + 1);
    int channel = command.toInt();
    command = command.substring(command.indexOf(' ') + 1);
    int angle = command.toInt();
    
    setServoAngle(pca_num, channel, angle);
  }
  else if (command.startsWith("sweep ")) {
    command = command.substring(6);
    int pca_num = command.toInt();
    command = command.substring(command.indexOf(' ') + 1);
    int channel = command.toInt();
    
    sweepServo(pca_num, channel);
  }
  else if (command == "reset") {
    resetAll();
  }
}

void sweepServo(int pca_num, int channel) {
  Serial.print("Sweeping - PCA: ");
  Serial.print(pca_num);
  Serial.print(", Channel: ");
  Serial.println(channel);
  
  // Sweep from 0 to 180 degrees
  for (int angle = 0; angle <= 180; angle += 10) {
    setServoAngle(pca_num, channel, angle);
    delay(500);
  }
  
  // And back to 0
  for (int angle = 180; angle >= 0; angle -= 10) {
    setServoAngle(pca_num, channel, angle);
    delay(500);
  }
  
  Serial.println("Sweep complete");
}

void resetAll() {
  Serial.println("Resetting all servos to neutral position (90 degrees)...");
  
  // Reset all channels on both PCAs to 90 degrees
  for (int channel = 0; channel < 16; channel++) {
    setServoAngle(1, channel, 90);
    setServoAngle(2, channel, 90);
    delay(100);
  }
  
  Serial.println("Reset complete");
} 