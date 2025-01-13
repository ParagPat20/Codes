#ifndef CONFIG_H
#define CONFIG_H

// Number of servos
#define NUM_SERVOS 20

// Servo configuration structure
struct ServoConfig {
    const char* id;
    int channel;
    bool inverted;
    int offset;
    const char* old_id;  // For reference
};

// Servo configurations
const ServoConfig SERVO_CONFIG[NUM_SERVOS] = {
    // Left Front Leg
    {"LFC", 1, false, 0, "L2"},   // L2 = channel 1
    {"LFT", 2, false, 0, "L3"},   // L3 = channel 2
    {"LFB", 0, false, 0, "L1"},   // L1 = channel 0
    
    // Left Mid Leg (4 servos)
    {"LMC", 7, false, 0, "L8"},   // L8 = channel 7
    {"LMT", 5, false, 0, "L6"},   // L6 = channel 5
    {"LMB", 6, false, 0, "L7"},   // L7 = channel 6
    {"LMF", 4, false, 33, "L5"},  // L5 = channel 4
    
    // Left Back Leg
    {"LBC", 10, true, -20, "L11"}, // L11 = channel 10
    {"LBT", 9, true, 20, "L10"},   // L10 = channel 9
    {"LBB", 8, true, 0, "L9"},     // L9 = channel 8
    
    // Right Front Leg
    {"RFC", 2, true, 0, "R3"},    // R3 = channel 2 (PCA2)
    {"RFT", 1, false, 0, "R2"},   // R2 = channel 1 (PCA2)
    {"RFB", 0, true, 0, "R1"},    // R1 = channel 0 (PCA2)
    
    // Right Mid Leg (4 servos)
    {"RMC", 7, false, 0, "R8"},   // R8 = channel 7 (PCA2)
    {"RMT", 6, true, 0, "R7"},    // R7 = channel 6 (PCA2)
    {"RMB", 5, false, 0, "R6"},   // R6 = channel 5 (PCA2)
    {"RMF", 4, false, 0, "R5"},   // R5 = channel 4 (PCA2)
    
    // Right Back Leg
    {"RBC", 8, false, 0, "R9"},   // R9 = channel 8 (PCA2)
    {"RBT", 10, false, 0, "R11"}, // R11 = channel 10 (PCA2)
    {"RBB", 9, true, 0, "R10"}    // R10 = channel 9 (PCA2)
};

// Motion modes
enum MotionMode {
    MODE_STANDBY,
    MODE_FORWARD,
    MODE_BACKWARD,
    MODE_TURN_LEFT,
    MODE_TURN_RIGHT,
    MODE_TEST,
    MODE_TEST_FORWARD
};

// Motion timing
#define MOTION_DELAY 300  // Delay between motion phases (ms)
#define SERVO_MOVE_TIME 800  // Time for servo to reach position (ms)

#endif 