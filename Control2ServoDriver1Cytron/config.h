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
};

// Servo configurations
const ServoConfig SERVO_CONFIG[NUM_SERVOS] = {
    // Left Front Leg
    {"LFC", 0, false, 0},  // Coxa
    {"LFT", 1, false, 0},  // Tibia
    {"LFB", 2, false, 0},  // Body
    
    // Left Mid Leg (4 servos)
    {"LMC", 3, false, 0},  // Coxa
    {"LMT", 4, false, 0},  // Tibia
    {"LMB", 5, false, 0},  // Body
    {"LMF", 6, false, 0},  // Fourth servo
    
    // Left Back Leg
    {"LBC", 7, false, 0},  // Coxa
    {"LBT", 8, false, 0},  // Tibia
    {"LBB", 9, false, 0},  // Body
    
    // Right Front Leg
    {"RFC", 16, true, 0},  // Coxa
    {"RFT", 17, true, 0},  // Tibia
    {"RFB", 18, true, 0},  // Body
    
    // Right Mid Leg (4 servos)
    {"RMC", 19, true, 0},  // Coxa
    {"RMT", 20, true, 0},  // Tibia
    {"RMB", 21, true, 0},  // Body
    {"RMF", 22, true, 0},  // Fourth servo
    
    // Right Back Leg
    {"RBC", 23, true, 0},  // Coxa
    {"RBT", 24, true, 0},  // Tibia
    {"RBB", 25, true, 0}   // Body
};

// Motion modes
enum MotionMode {
    MODE_STANDBY,
    MODE_FORWARD,
    MODE_BACKWARD,
    MODE_TURN_LEFT,
    MODE_TURN_RIGHT
};

// Motion timing
#define MOTION_DELAY 50  // Delay between motion phases (ms)
#define SERVO_MOVE_TIME 150  // Time for servo to reach position (ms)

#endif 