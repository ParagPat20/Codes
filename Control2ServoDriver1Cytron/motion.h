/**
 * Motion patterns for hexapod with 4-servo mid leg configuration
 */

#ifndef MOTION_H
#define MOTION_H

// Standby position for all servos
struct ServoPosition {
    const char* id;
    int angle;
};

#define NUM_STANDBY_POSITIONS 20
const ServoPosition STANDBY_POSITION[NUM_STANDBY_POSITIONS] = {
    // LEFT FRONT
    {"LFC", 0},   // COXA (L2)
    {"LFT", 70},  // FEMUR (L3)
    {"LFB", 180}, // TIBIA (L1)
    
    // LEFT MID (4 servos)
    {"LMC", 90},  // COXA (L8)
    {"LMT", 160}, // FEMUR1 (L6)
    {"LMB", 100}, // FEMUR2 (L7)
    {"LMF", 0},   // TIBIA (L5)
    
    // LEFT BACK
    {"LBC", 0},   // COXA (L11)
    {"LBT", 70},  // FEMUR (L10)
    {"LBB", 180}, // TIBIA (L9)
    
    // RIGHT FRONT
    {"RFC", 0},   // COXA (R3)
    {"RFT", 70},  // FEMUR (R2)
    {"RFB", 180}, // TIBIA (R1)
    
    // RIGHT MID (4 servos)
    {"RMC", 90},  // COXA (R8)
    {"RMT", 160}, // FEMUR1 (R7)
    {"RMB", 100}, // FEMUR2 (R6)
    {"RMF", 0},   // TIBIA (R5)
    
    // RIGHT BACK
    {"RBC", 0},   // COXA (R9)
    {"RBT", 70},  // FEMUR (R11)
    {"RBB", 180}  // TIBIA (R10)
};

// Forward walking sequence
#define NUM_FORWARD_PHASES 4
const ServoPosition FORWARD_SEQUENCE[NUM_FORWARD_PHASES][20] = {
    // Phase 1: Lift and move forward group 1 (RF, LM, RB)
    {
        // LEFT FRONT - maintain standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        // LEFT MID - lift and move
        {"LMC", 110}, {"LMT", 130}, {"LMB", 130}, {"LMF", 30},
        // LEFT BACK - maintain standby
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        // RIGHT FRONT - lift and move
        {"RFC", 20}, {"RFT", 40}, {"RFB", 150},
        // RIGHT MID - maintain standby
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        // RIGHT BACK - lift and move
        {"RBC", 20}, {"RBT", 40}, {"RBB", 150}
    },
    // Phase 2: Lower group 1, lift and move forward group 2 (LF, RM, LB)
    {
        // LEFT FRONT - lift and move
        {"LFC", 20}, {"LFT", 40}, {"LFB", 150},
        // LEFT MID - return to standby
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        // LEFT BACK - lift and move
        {"LBC", 20}, {"LBT", 40}, {"LBB", 150},
        // RIGHT FRONT - maintain new position
        {"RFC", 20}, {"RFT", 70}, {"RFB", 180},
        // RIGHT MID - lift and move
        {"RMC", 110}, {"RMT", 130}, {"RMB", 130}, {"RMF", 30},
        // RIGHT BACK - maintain new position
        {"RBC", 20}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 3: Move body forward
    {
        // All legs move slightly to push body forward
        {"LFC", 10}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 100}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 10}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 10}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 100}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 10}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 4: Return to initial position
    {
        // All legs return to standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 0}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 0}, {"RBT", 70}, {"RBB", 180}
    }
};

// Backward walking sequence (reverse of forward)
#define NUM_BACKWARD_PHASES 4
const ServoPosition BACKWARD_SEQUENCE[NUM_BACKWARD_PHASES][20] = {
    // Phase 1: Lift and move backward group 1 (RF, LM, RB)
    {
        // LEFT FRONT - maintain standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        // LEFT MID - lift and move backward
        {"LMC", 70}, {"LMT", 130}, {"LMB", 130}, {"LMF", 30},
        // LEFT BACK - maintain standby
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        // RIGHT FRONT - lift and move backward
        {"RFC", -20}, {"RFT", 40}, {"RFB", 150},
        // RIGHT MID - maintain standby
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        // RIGHT BACK - lift and move backward
        {"RBC", -20}, {"RBT", 40}, {"RBB", 150}
    },
    // Phase 2: Lower group 1, lift and move backward group 2
    {
        // LEFT FRONT - lift and move backward
        {"LFC", -20}, {"LFT", 40}, {"LFB", 150},
        // LEFT MID - return to standby
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        // LEFT BACK - lift and move backward
        {"LBC", -20}, {"LBT", 40}, {"LBB", 150},
        // RIGHT FRONT - maintain new position
        {"RFC", -20}, {"RFT", 70}, {"RFB", 180},
        // RIGHT MID - lift and move backward
        {"RMC", 70}, {"RMT", 130}, {"RMB", 130}, {"RMF", 30},
        // RIGHT BACK - maintain new position
        {"RBC", -20}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 3: Move body backward
    {
        // All legs move slightly to push body backward
        {"LFC", -10}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 80}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", -10}, {"LBT", 70}, {"LBB", 180},
        {"RFC", -10}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 80}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", -10}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 4: Return to initial position
    {
        // All legs return to standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 0}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 0}, {"RBT", 70}, {"RBB", 180}
    }
};

// Turn left sequence
#define NUM_TURN_LEFT_PHASES 4
const ServoPosition TURN_LEFT_SEQUENCE[NUM_TURN_LEFT_PHASES][20] = {
    // Phase 1: Lift and rotate left side forward, right side backward
    {
        // LEFT FRONT - rotate forward
        {"LFC", 20}, {"LFT", 40}, {"LFB", 150},
        // LEFT MID - lift and rotate
        {"LMC", 110}, {"LMT", 130}, {"LMB", 130}, {"LMF", 30},
        // LEFT BACK - rotate backward
        {"LBC", -20}, {"LBT", 40}, {"LBB", 150},
        // RIGHT FRONT - rotate backward
        {"RFC", -20}, {"RFT", 40}, {"RFB", 150},
        // RIGHT MID - lift and rotate
        {"RMC", 70}, {"RMT", 130}, {"RMB", 130}, {"RMF", 30},
        // RIGHT BACK - rotate forward
        {"RBC", 20}, {"RBT", 40}, {"RBB", 150}
    },
    // Phase 2: Lower legs and prepare for next rotation
    {
        // Return all legs to ground but maintain rotation
        {"LFC", 20}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 110}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", -20}, {"LBT", 70}, {"LBB", 180},
        {"RFC", -20}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 70}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 20}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 3: Rotate body
    {
        // Rotate body while all legs are on ground
        {"LFC", 10}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 100}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", -10}, {"LBT", 70}, {"LBB", 180},
        {"RFC", -10}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 80}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 10}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 4: Return to initial position
    {
        // All legs return to standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 0}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 0}, {"RBT", 70}, {"RBB", 180}
    }
};

// Turn right sequence
#define NUM_TURN_RIGHT_PHASES 4
const ServoPosition TURN_RIGHT_SEQUENCE[NUM_TURN_RIGHT_PHASES][20] = {
    // Phase 1: Lift and rotate right side forward, left side backward
    {
        // LEFT FRONT - rotate backward
        {"LFC", -20}, {"LFT", 40}, {"LFB", 150},
        // LEFT MID - lift and rotate
        {"LMC", 70}, {"LMT", 130}, {"LMB", 130}, {"LMF", 30},
        // LEFT BACK - rotate forward
        {"LBC", 20}, {"LBT", 40}, {"LBB", 150},
        // RIGHT FRONT - rotate forward
        {"RFC", 20}, {"RFT", 40}, {"RFB", 150},
        // RIGHT MID - lift and rotate
        {"RMC", 110}, {"RMT", 130}, {"RMB", 130}, {"RMF", 30},
        // RIGHT BACK - rotate backward
        {"RBC", -20}, {"RBT", 40}, {"RBB", 150}
    },
    // Phase 2: Lower legs and prepare for next rotation
    {
        // Return all legs to ground but maintain rotation
        {"LFC", -20}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 70}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 20}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 20}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 110}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", -20}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 3: Rotate body
    {
        // Rotate body while all legs are on ground
        {"LFC", -10}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 80}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 10}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 10}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 100}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", -10}, {"RBT", 70}, {"RBB", 180}
    },
    // Phase 4: Return to initial position
    {
        // All legs return to standby
        {"LFC", 0}, {"LFT", 70}, {"LFB", 180},
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0},
        {"LBC", 0}, {"LBT", 70}, {"LBB", 180},
        {"RFC", 0}, {"RFT", 70}, {"RFB", 180},
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0},
        {"RBC", 0}, {"RBT", 70}, {"RBB", 180}
    }
};

#endif // MOTION_H 