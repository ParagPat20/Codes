#ifndef CONFIG_H
#define CONFIG_H

// PCA9685 addresses
#define PCA1_ADDR 0x40  // Left side servos
#define PCA2_ADDR 0x42  // Right side servos

// Servo frequency and pulse ranges
#define SERVO_FREQ 50  // 50 Hz update rate for servos
#define PULSE_MIN 102  // Minimum pulse length (0 degrees)
#define PULSE_MAX 512  // Maximum pulse length (180 degrees)
#define ANGLE_MIN 0    // Minimum angle
#define ANGLE_MAX 180  // Maximum angle

// Number of servos
#define NUM_SERVOS 20

// Motion timing
#define MOTION_DELAY 100     // Delay between motion phases (ms)
#define SERVO_MOVE_TIME 100  // Time for servo to reach position (ms)

// Leg identifiers for easier reference
#define LEFT_FRONT 0
#define LEFT_MID 1
#define LEFT_REAR 2
#define RIGHT_FRONT 3
#define RIGHT_MID 4
#define RIGHT_REAR 5

// Servo configuration structure
struct ServoConfig {
  const char* id;      // Servo identifier (e.g., "LFC")
  int channel;         // PWM channel number
  const char* old_id;  // Original channel ID (e.g., "L00")
};

// Motion modes
enum MotionMode {
  MODE_STANDBY,
  MODE_FORWARD,
  MODE_TEST_SERVOS,
  MODE_ROLLING  // New rolling motion mode
};

// Servo configurations grouped by leg
const ServoConfig SERVO_CONFIG[NUM_SERVOS] = {
  // Left Front Leg (Group 0)
  { "LFC", 0, "L00" },   // Left Front Coxa
  { "LFF", 14, "L14" },  // Left Front Femur
  { "LFT", 15, "L15" },  // Left Front Tibia

  // Left Mid Leg (Group 1)
  { "LMC", 2, "L02" },    // Left Middle Coxa
  { "LMF1", 11, "L11" },  // Left Middle Femur 1
  { "LMF2", 12, "L12" },  // Left Middle Femur 2
  { "LMT", 13, "L13" },   // Left Middle Tibia

  // Left Rear Leg (Group 2)
  { "LRC", 4, "L04" },  // Left Rear Coxa
  { "LRF", 7, "L07" },  // Left Rear Femur
  { "LRT", 6, "L06" },  // Left Rear Tibia

  // Right Front Leg (Group 3)
  { "RFC", 13, "R13" },  // Right Front Coxa
  { "RFF", 1, "R01" },   // Right Front Femur
  { "RFT", 0, "R00" },   // Right Front Tibia

  // Right Mid Leg (Group 4)
  { "RMC", 11, "R11" },  // Right Middle Coxa
  { "RMF1", 4, "R04" },  // Right Middle Femur 1
  { "RMF2", 3, "R03" },  // Right Middle Femur 2
  { "RMT", 2, "R02" },   // Right Middle Tibia

  // Right Rear Leg (Group 5)
  { "RRC", 15, "R15" },  // Right Rear Coxa
  { "RRF", 8, "R08" },   // Right Rear Femur
  { "RRT", 9, "R09" }    // Right Rear Tibia
};

// Helper arrays for leg servo indices
const int SERVOS_PER_LEG[] = { 3, 4, 3, 3, 4, 3 };  // Number of servos in each leg

const int LEG_SERVO_START[] = {
  0,   // Left Front starts at index 0
  3,   // Left Mid starts at index 3
  7,   // Left Rear starts at index 7
  10,  // Right Front starts at index 10
  13,  // Right Mid starts at index 13
  17   // Right Rear starts at index 17
};

// Helper function to get leg group from servo ID
inline int getLegGroup(const char* id) {
  if (id[0] == 'L') {
    if (id[1] == 'F') return LEFT_FRONT;
    if (id[1] == 'M') return LEFT_MID;
    if (id[1] == 'R') return LEFT_REAR;
  } else if (id[0] == 'R') {
    if (id[1] == 'F') return RIGHT_FRONT;
    if (id[1] == 'M') return RIGHT_MID;
    if (id[1] == 'R') return RIGHT_REAR;
  }
  return -1;
}

#endif