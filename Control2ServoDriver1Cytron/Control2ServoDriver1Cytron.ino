#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "config.h"
#include "motion.h"

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
MotionMode currentMode = MODE_STANDBY;
int currentPhase = 0;
unsigned long lastMotionUpdate = 0;

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

  // Print original values
  Serial.print(id);
  Serial.print(" (");
  Serial.print(config->old_id);
  Serial.print("): Raw=");
  Serial.print(angle);

  // Apply inversion and offset
  if (config->inverted) {
    angle = 180 - angle;
    Serial.print(", Inverted=");
    Serial.print(angle);
  }
  angle += config->offset;
  if (config->offset != 0) {
    Serial.print(", Offset=");
    Serial.print(angle);
  }
  angle = constrain(angle, 0, 180);
  Serial.print(", Final=");
  Serial.println(angle);

  // Convert angle to pulse length
  int pulseLength = map(angle, 0, 180, 102, 512);

  // Determine which PCA9685 to use based on old_id
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
    delay(100);  // Small delay between servo movements
  }
  currentMode = MODE_STANDBY;
  Serial.println("Standby position reached");
}

void updateForwardMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(FORWARD_SEQUENCE[currentPhase][i].id,
                  FORWARD_SEQUENCE[currentPhase][i].angle);
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_FORWARD_PHASES;
  lastMotionUpdate = millis();
}

void updateBackwardMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(BACKWARD_SEQUENCE[currentPhase][i].id,
                  BACKWARD_SEQUENCE[currentPhase][i].angle);
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_BACKWARD_PHASES;
  lastMotionUpdate = millis();
}

void updateTurnLeftMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(TURN_LEFT_SEQUENCE[currentPhase][i].id,
                  TURN_LEFT_SEQUENCE[currentPhase][i].angle);
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_TURN_LEFT_PHASES;
  lastMotionUpdate = millis();
}

void updateTurnRightMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(TURN_RIGHT_SEQUENCE[currentPhase][i].id,
                  TURN_RIGHT_SEQUENCE[currentPhase][i].angle);
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_TURN_RIGHT_PHASES;
  lastMotionUpdate = millis();
}

void updateTestMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(TEST_SEQUENCE[currentPhase][i].id,
                  TEST_SEQUENCE[currentPhase][i].angle);
  }

  // Move to next phase
  currentPhase = (currentPhase + 1) % NUM_TEST_PHASES;
  lastMotionUpdate = millis();
}

void updateTestForwardMotion() {
  if (millis() - lastMotionUpdate < MOTION_DELAY) {
    return;
  }

  // Update all servos for current phase
  for (int i = 0; i < NUM_STANDBY_POSITIONS; i++) {
    setServoAngle(TEST_FORWARD_SEQUENCE[currentPhase][i].id,
                  TEST_FORWARD_SEQUENCE[currentPhase][i].angle);
  }
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
    }
  }
}

// Helper function to get mode name
const char* getMotionModeName(MotionMode mode) {
  switch(mode) {
    case MODE_STANDBY: return "STANDBY";
    case MODE_FORWARD: return "FORWARD";
    case MODE_BACKWARD: return "BACKWARD";
    case MODE_TURN_LEFT: return "TURN_LEFT";
    case MODE_TURN_RIGHT: return "TURN_RIGHT";
    case MODE_TEST: return "TEST";
    case MODE_TEST_FORWARD: return "TEST_FORWARD";
    case MODE_TEST_SERVOS: return "TEST_SERVOS";
    default: return "UNKNOWN";
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize PCA9685 instances
  pca1.begin();
  pca1.setPWMFreq(SERVO_FREQ);
  pca2.begin();
  pca2.setPWMFreq(SERVO_FREQ);

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


  Serial.println("Initialization complete");
  Serial.println("Send servo commands (format: LFC:90,LFT:70,...) or type 'standby' to move to standby position");
}

void loop() {
  // Handle serial commands
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    Serial.print("Received command: ");
    Serial.println(input);
    
    if (input == "forward") {
      setMotionMode(MODE_FORWARD);
      Serial.println("OK");
    } else if (input == "backward") {
      setMotionMode(MODE_BACKWARD);
      Serial.println("OK");
    } else if (input == "turn_left") {
      setMotionMode(MODE_TURN_LEFT);
      Serial.println("OK");
    } else if (input == "turn_right") {
      setMotionMode(MODE_TURN_RIGHT);
      Serial.println("OK");
    } else if (input == "standby") {
      setMotionMode(MODE_STANDBY);
      Serial.println("OK");
    } else if (input == "test") {
      setMotionMode(MODE_TEST);
      Serial.println("OK");
    } else if (input == "test_forward") {
      setMotionMode(MODE_TEST_FORWARD);
      Serial.println("OK");
    } else if (input == "test_servos") {
      setMotionMode(MODE_TEST_SERVOS);
      Serial.println("OK");
    } else if (currentMode == MODE_TEST_SERVOS) {
      // In test mode, directly handle servo commands
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
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Forward phase: ");
        Serial.println(currentPhase);
      }
      updateForwardMotion();
      break;
    case MODE_BACKWARD:
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Backward phase: ");
        Serial.println(currentPhase);
      }
      updateBackwardMotion();
      break;
    case MODE_TURN_LEFT:
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Turn left phase: ");
        Serial.println(currentPhase);
      }
      updateTurnLeftMotion();
      break;
    case MODE_TURN_RIGHT:
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Turn right phase: ");
        Serial.println(currentPhase);
      }
      updateTurnRightMotion();
      break;
    case MODE_STANDBY:
      // Already prints debug in moveToStandby()
      moveToStandby();
      break;
    case MODE_TEST:
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Test phase: ");
        Serial.println(currentPhase);
      }
      updateTestMotion();
      break;
    case MODE_TEST_FORWARD:
      if (millis() - lastMotionUpdate >= MOTION_DELAY) {
        Serial.print("Test forward phase: ");
        Serial.println(currentPhase);
      }
      updateTestForwardMotion();
      break;
    case MODE_TEST_SERVOS:
      // Do nothing, just wait for commands
      break;
    default:
      break;
  }
}

void parseAndSetServos(String command) {
  // Format: [Leg][Joint]:[Angle]
  // Example: LFC:90, RFT:145
  
  if (command.length() < 5) {
    Serial.println("Invalid command length");
    return;
  }

  String servoId = command.substring(0, 3);
  int angle = command.substring(4).toInt();

  Serial.print("Setting ");
  Serial.print(servoId);
  Serial.print(" to angle: ");
  Serial.println(angle);

  // Find servo config
  const ServoConfig* config = findServoConfig(servoId.c_str());
  if (config && angle >= 0 && angle <= 180) {
    // Apply inversion and offset from config
    if (config->inverted) {
      angle = 180 - angle;
      Serial.print("Inverted angle: ");
      Serial.println(angle);
    }
    angle += config->offset;
    Serial.print("After offset: ");
    Serial.println(angle);
    
    // Constrain final angle
    angle = constrain(angle, 0, 180);
    
    // Determine which PCA9685 to use based on old_id
    if (config->old_id[0] == 'L') {  // Left side servos on PCA1
      pca1.setPWM(config->channel, 0, angleToPulse(angle));
      Serial.print("Set LEFT servo channel ");
    } else {  // Right side servos on PCA2
      pca2.setPWM(config->channel, 0, angleToPulse(angle));
      Serial.print("Set RIGHT servo channel ");
    }
    Serial.print(config->channel);
    Serial.print(" to angle ");
    Serial.println(angle);
  } else {
    Serial.println("Invalid servo ID or angle");
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
  }
}
