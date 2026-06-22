/*
 * ESP32 PCA9685 16-Channel Servo Controller
 * 
 * Controls up to 16 servos via PCA9685 PWM driver board using direct PWM tick values
 * Communicates via Serial with Python GUI
 * 
 * Serial Commands:
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
#define MOSFET_PIN 19

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

// Function prototypes
void setServoPWM(uint8_t channel, uint16_t tickValue);
void setServoAngle(uint8_t channel, float angle);
void setPWMFrequency(uint16_t freq);
void setCalibration(uint8_t channel, uint16_t minTick, uint16_t maxTick);
void setAllCalibrations(uint16_t minTick, uint16_t maxTick);
void getCalibration(uint8_t channel);
void getAllCalibrations();
void resetToDefaults();
void printInfo();
void processSerialCommand(String command);

void setup() {
  // Configure and turn on MOSFET power control pin
  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(MOSFET_PIN, HIGH); // Pull HIGH to turn on MOSFET (enable ground path for PCA9685)
  delay(100); // Wait for power to stabilize

  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // Wait for serial port to connect
  }
  
  Serial.println("ESP32 PCA9685 Servo Controller - Tick Mode");
  Serial.println("==========================================");
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize PCA9685
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
  Serial.println("\nReady for commands...");
  Serial.println("Type 'INFO' for current configuration");
  printInfo();
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processSerialCommand(command);
    }
  }
}

// Command parser - processes serial commands
void processSerialCommand(String command) {
  command.toUpperCase();
  command.trim();
  
  // TICK command: "TICK <channel> <value>"
  if (command.startsWith("TICK ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (secondSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      int tickValue = command.substring(secondSpace + 1).toInt();
      
      if (channel >= 0 && channel < 16 && tickValue >= 0 && tickValue <= 4095) {
        setServoPWM(channel, tickValue);
        Serial.print("OK: Channel ");
        Serial.print(channel);
        Serial.print(" set to tick ");
        Serial.println(tickValue);
      } else {
        Serial.println("ERROR: Invalid channel (0-15) or tick value (0-4095)");
      }
    } else {
      Serial.println("ERROR: Invalid TICK command format. Use: TICK <channel> <value>");
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
        Serial.print("OK: Channel ");
        Serial.print(channel);
        Serial.print(" set to ");
        Serial.print(angle, 1);
        Serial.println(" degrees");
      } else {
        Serial.println("ERROR: Invalid channel (0-15) or angle (0.0-180.0)");
      }
    } else {
      Serial.println("ERROR: Invalid ANGLE command format. Use: ANGLE <channel> <angle>");
    }
  }
  
  // CAL command: "CAL <channel> <min_tick> <max_tick>"
  else if (command.startsWith("CAL ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    int thirdSpace = command.indexOf(' ', secondSpace + 1);
    
    if (thirdSpace > 0) {
      int channel = command.substring(firstSpace + 1, secondSpace).toInt();
      int minTick = command.substring(secondSpace + 1, thirdSpace).toInt();
      int maxTick = command.substring(thirdSpace + 1).toInt();
      
      if (channel >= 0 && channel < 16 && minTick >= 0 && maxTick > minTick && maxTick <= 4095) {
        setCalibration(channel, minTick, maxTick);
        Serial.print("OK: Channel ");
        Serial.print(channel);
        Serial.print(" calibration set to ");
        Serial.print(minTick);
        Serial.print("-");
        Serial.println(maxTick);
      } else {
        Serial.println("ERROR: Invalid channel or tick range (0 < min < max <= 4095)");
      }
    } else {
      Serial.println("ERROR: Invalid CAL command format. Use: CAL <channel> <min> <max>");
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
        Serial.print("OK: All channels calibration set to ");
        Serial.print(minTick);
        Serial.print("-");
        Serial.println(maxTick);
      } else {
        Serial.println("ERROR: Invalid tick range (0 < min < max <= 4095)");
      }
    } else {
      Serial.println("ERROR: Invalid CAL_ALL command format. Use: CAL_ALL <min> <max>");
    }
  }
  
  // GET_CAL command: "GET_CAL <channel>"
  else if (command.startsWith("GET_CAL ")) {
    int channel = command.substring(8).toInt();
    if (channel >= 0 && channel < 16) {
      getCalibration(channel);
    } else {
      Serial.println("ERROR: Invalid channel (0-15)");
    }
  }
  
  // GET_ALL_CAL command
  else if (command == "GET_ALL_CAL") {
    getAllCalibrations();
  }
  
  // FREQ command: "FREQ <frequency>"
  else if (command.startsWith("FREQ ")) {
    int freq = command.substring(5).toInt();
    
    if (freq >= 40 && freq <= 1000) {
      setPWMFrequency(freq);
      Serial.print("OK: PWM frequency set to ");
      Serial.print(freq);
      Serial.println(" Hz");
    } else {
      Serial.println("ERROR: Invalid frequency (40-1000 Hz)");
    }
  }
  
  // SLEEP command
  else if (command == "SLEEP") {
    pca.sleep();
    Serial.println("OK: PCA9685 sleep mode enabled");
  }
  
  // WAKE command
  else if (command == "WAKE") {
    pca.wakeup();
    Serial.println("OK: PCA9685 woken up");
  }
  
  // RESET command
  else if (command == "RESET") {
    resetToDefaults();
    Serial.println("OK: Reset to default configuration");
    printInfo();
  }
  
  // INFO command
  else if (command == "INFO") {
    printInfo();
  }
  
  // Unknown command
  else {
    Serial.println("ERROR: Unknown command");
    Serial.println("Available commands:");
    Serial.println("  TICK <ch> <value>          - Set PWM tick (0-4095)");
    Serial.println("  ANGLE <ch> <angle>         - Set angle (0.0-180.0)");
    Serial.println("  CAL <ch> <min> <max>       - Set channel calibration");
    Serial.println("  CAL_ALL <min> <max>        - Set all channels calibration");
    Serial.println("  GET_CAL <ch>               - Get channel calibration");
    Serial.println("  GET_ALL_CAL                - Get all calibrations");
    Serial.println("  FREQ <frequency>           - Set PWM frequency");
    Serial.println("  SLEEP                      - Sleep mode");
    Serial.println("  WAKE                       - Wake from sleep");
    Serial.println("  RESET                      - Reset to defaults");
    Serial.println("  INFO                       - Show configuration");
  }
}

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
void getCalibration(uint8_t channel) {
  if (channel >= 16) {
    return;
  }
  
  Serial.print("CAL_DATA ");
  Serial.print(channel);
  Serial.print(" ");
  Serial.print(servoConfigs[channel].tickMin);
  Serial.print(" ");
  Serial.println(servoConfigs[channel].tickMax);
}

// Get all calibrations
void getAllCalibrations() {
  Serial.println("ALL_CAL_DATA");
  for (int i = 0; i < 16; i++) {
    Serial.print(i);
    Serial.print(" ");
    Serial.print(servoConfigs[i].tickMin);
    Serial.print(" ");
    Serial.println(servoConfigs[i].tickMax);
  }
  Serial.println("END_CAL_DATA");
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
void printInfo() {
  Serial.println("\n========== Current Configuration ==========");
  Serial.print("PWM Frequency: ");
  Serial.print(pwmFrequency);
  Serial.println(" Hz");
  
  Serial.println("\nChannel Configuration:");
  Serial.println("Ch  | Angle  | Curr Tick | Tick Min | Tick Max");
  Serial.println("----|--------|-----------|----------|----------");
  
  for (int i = 0; i < 16; i++) {
    Serial.printf("%2d  | %6.1f | %4d      | %4d     | %4d\n", 
                  i, 
                  servoConfigs[i].lastAngle,
                  servoConfigs[i].currentTick,
                  servoConfigs[i].tickMin,
                  servoConfigs[i].tickMax);
  }
  
  Serial.println("==========================================\n");
}

