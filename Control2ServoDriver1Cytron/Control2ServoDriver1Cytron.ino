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
        if (strcmp(SERVO_CONFIG[i].id, id) == 0) {
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

    // Apply inversion and offset
    if (config->inverted) {
        angle = 180 - angle;
    }
    angle += config->offset;
    angle = constrain(angle, 0, 180);

    // Convert angle to pulse length
    int pulseLength = map(angle, 0, 180, 102, 512);

    // Determine which PCA9685 to use based on channel
    if (config->channel < 16) {
        pca1.setPWM(config->channel, 0, pulseLength);
    } else {
        pca2.setPWM(config->channel - 16, 0, pulseLength);
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

void setMotionMode(MotionMode mode) {
    if (mode != currentMode) {
        currentMode = mode;
        currentPhase = 0;
        lastMotionUpdate = 0;
        
        if (mode == MODE_STANDBY) {
            moveToStandby();
        }
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
    
    // Move to standby position on startup
    moveToStandby();
}

void loop() {
    // Handle serial commands
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        if (input == "forward") {
            setMotionMode(MODE_FORWARD);
        } else if (input == "backward") {
            setMotionMode(MODE_BACKWARD);
        } else if (input == "turn_left") {
            setMotionMode(MODE_TURN_LEFT);
        } else if (input == "turn_right") {
            setMotionMode(MODE_TURN_RIGHT);
        } else if (input == "standby") {
            setMotionMode(MODE_STANDBY);
        } else {
            parseAndSetServos(input);
        }
    }

    // Update motion if needed
    switch (currentMode) {
        case MODE_FORWARD:
            updateForwardMotion();
            break;
        case MODE_BACKWARD:
            updateBackwardMotion();
            break;
        case MODE_TURN_LEFT:
            updateTurnLeftMotion();
            break;
        case MODE_TURN_RIGHT:
            updateTurnRightMotion();
            break;
        case MODE_STANDBY:
            // Do nothing, stay in position
            break;
        default:
            break;
    }
}

void parseAndSetServos(String input) {
    input.trim();
    if (input.length() == 0) {
        return;
    }

    // Split input by commas
    int startIdx = 0;
    while (startIdx < input.length()) {
        int endIdx = input.indexOf(',', startIdx);
        if (endIdx == -1) endIdx = input.length();
        
        String pair = input.substring(startIdx, endIdx);
        int colonIdx = pair.indexOf(':');
        
        if (colonIdx != -1) {
            String id = pair.substring(0, colonIdx);
            int angle = pair.substring(colonIdx + 1).toInt();
            
            if (id == "LDC" || id == "RDC") {
                setMotorSpeed(id, angle);
            } else {
                setServoAngle(id.c_str(), angle);
            }
        }
        
        startIdx = endIdx + 1;
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
