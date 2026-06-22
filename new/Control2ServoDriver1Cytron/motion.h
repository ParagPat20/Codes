/**
 * Motion patterns for hexapod with 4-servo mid leg configuration
 */

#ifndef MOTION_H
#define MOTION_H

#include "config.h"
#include <Arduino.h>

// Standby position for all servos
struct ServoPosition {
  const char* id;
  int angle;
};

#define NUM_STANDBY_POSITIONS 20
const ServoPosition STANDBY_POSITION[NUM_STANDBY_POSITIONS] = {
  // LEFT FRONT
  { "LFC", 150 },  // Front Coxa
  { "LFF", 75 },   // Front Femur
  { "LFT", 35 },   // Front Tibia

  // LEFT MID
  { "LMC", 62 },    // Mid Coxa
  { "LMF1", 145 },  // Mid Femur 1
  { "LMF2", 90 },   // Mid Femur 2
  { "LMT", 140 },   // Mid Tibia

  // LEFT REAR
  { "LRC", 53 },   // Rear Coxa
  { "LRF", 95 },   // Rear Femur
  { "LRT", 125 },  // Rear Tibia

  // RIGHT FRONT
  { "RFC", 45 },   // Front Coxa
  { "RFF", 100 },  // Front Femur
  { "RFT", 55 },   // Front Tibia

  // RIGHT MID
  { "RMC", 100 },   // Mid Coxa
  { "RMF1", 0 },    // Mid Femur 1
  { "RMF2", 80 },  // Mid Femur 2
  { "RMT", 150 },   // Mid Tibia

  // RIGHT REAR
  { "RRC", 140 },  // Rear Coxa
  { "RRF", 95 },  // Rear Femur
  { "RRT", 35 }    // Rear Tibia
};

// Add this helper struct for relative movements
struct ServoMove {
  const char* id;
  int change;  // Amount to add/subtract from standby position
};

// Walking scheme with relative changes
// add nullptr to set pos standby servo

//
// this scheme is
// + forward means : adding values will lead to forward, subtracting values will lead to backward
// - forward means : adding values will lead to backward, subtracting values will lead to forward
// + up: adding up, subtracting down
// - up : adding down, subtracting up

// LFC: +  : Forward
// LFF: + : Up

// LMC: + : Forward
// LMF2: - : UP (inverse)

// LRC: + : Forward
// LRF: + : Up

// RFC: - : Forward (inverse)
// RFF: + : Up

// RMC: - : Forward (inverse)
// RMF2: + : Up

// RRC: - : Forward (inverse)
// RRF: + : Up

// Forward walking sequence with relative changes
#define NUM_FORWARD_PHASES 6
const ServoMove FORWARD_SEQUENCE[NUM_FORWARD_PHASES][20] = {
  // Phase 1: Lift group 1 (RF, LM, RR)
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC
    { nullptr, 0 },  // LMF1
    { "LMF2", -30 }, // LMF2 - lift
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC
    { "RFF", +30 },  // RFF - lift
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC
    { "RRF", +30 },  // RRF - lift
    { nullptr, 0 }   // RRT
  },

  // Phase 2: Move group 1 forward while lifted
  {
    { nullptr, 0 },   // LFC
    { nullptr, 0 },   // LFF
    { nullptr, 0 },   // LFT

    { "LMC", +30 },   // LMC - forward
    { nullptr, 0 },   // LMF1
    { "LMF2", -30 },  // LMF2 - keep lifted
    { nullptr, 0 },   // LMT

    { nullptr, 0 },   // LRC
    { nullptr, 0 },   // LRF
    { nullptr, 0 },   // LRT

    { "RFC", -30 },   // RFC - forward (inverse)
    { "RFF", +30 },   // RFF - keep lifted
    { nullptr, 0 },   // RFT

    { nullptr, 0 },   // RMC
    { nullptr, 0 },   // RMF1
    { nullptr, 0 },   // RMF2
    { nullptr, 0 },   // RMT

    { "RRC", -30 },   // RRC - forward (inverse)
    { "RRF", +30 },   // RRF - keep lifted
    { nullptr, 0 }    // RRT
  },

  // Phase 3: Drop group 1
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", +30 },  // LMC - maintain forward
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - drop
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", -30 },  // RFC - maintain forward
    { "RFF", 0 },    // RFF - drop
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", -30 },  // RRC - maintain forward
    { "RRF", 0 },    // RRF - drop
    { nullptr, 0 }   // RRT
  },

  // Phase 4: Lift group 2 (LF, RM, LR)
  {
    { "LFC", 0 },    // LFC
    { "LFF", +30 },  // LFF - lift
    { nullptr, 0 },  // LFT

    { "LMC", +30 },  // LMC - maintain forward
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", 0 },    // LRC
    { "LRF", +30 },  // LRF - lift
    { nullptr, 0 },  // LRT

    { "RFC", -30 },  // RFC - maintain forward
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", 0 },    // RMC
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - lift
    { nullptr, 0 },  // RMT

    { "RRC", -30 },  // RRC - maintain forward
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 5: Move group 2 forward while lifted
  {
    { "LFC", +30 },  // LFC - forward
    { "LFF", +30 },  // LFF - keep lifted
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - back to center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", +30 },  // LRC - forward
    { "LRF", +30 },  // LRF - keep lifted
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - back to center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", -30 },  // RMC - forward (inverse)
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - keep lifted
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - back to center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 6: Drop group 2
  {
    { "LFC", +30 },  // LFC - maintain forward
    { "LFF", 0 },    // LFF - drop
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - maintain center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", +30 },  // LRC - maintain forward
    { "LRF", 0 },    // LRF - drop
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - maintain center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", -30 },  // RMC - maintain forward
    { nullptr, 0 },  // RMF1
    { "RMF2", 0 },   // RMF2 - drop
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - maintain center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  }
};

// Backward walking sequence with relative changes
#define NUM_BACKWARD_PHASES 6
const ServoMove BACKWARD_SEQUENCE[NUM_BACKWARD_PHASES][20] = {
  // Phase 1: Lift group 1 (RF, LM, RR)
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC
    { nullptr, 0 },  // LMF1
    { "LMF2", -30 }, // LMF2 - lift
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC
    { "RFF", +30 },  // RFF - lift
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC
    { "RRF", +30 },  // RRF - lift
    { nullptr, 0 }   // RRT
  },

  // Phase 2: Move group 1 backward while lifted
  {
    { nullptr, 0 },   // LFC
    { nullptr, 0 },   // LFF
    { nullptr, 0 },   // LFT

    { "LMC", -30 },   // LMC - backward
    { nullptr, 0 },   // LMF1
    { "LMF2", -30 },  // LMF2 - keep lifted
    { nullptr, 0 },   // LMT

    { nullptr, 0 },   // LRC
    { nullptr, 0 },   // LRF
    { nullptr, 0 },   // LRT

    { "RFC", +30 },   // RFC - backward (inverse)
    { "RFF", +30 },   // RFF - keep lifted
    { nullptr, 0 },   // RFT

    { nullptr, 0 },   // RMC
    { nullptr, 0 },   // RMF1
    { nullptr, 0 },   // RMF2
    { nullptr, 0 },   // RMT

    { "RRC", +30 },   // RRC - backward (inverse)
    { "RRF", +30 },   // RRF - keep lifted
    { nullptr, 0 }    // RRT
  },

  // Phase 3: Drop group 1
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", -30 },  // LMC - maintain backward
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - drop
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", +30 },  // RFC - maintain backward
    { "RFF", 0 },    // RFF - drop
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", +30 },  // RRC - maintain backward
    { "RRF", 0 },    // RRF - drop
    { nullptr, 0 }   // RRT
  },

  // Phase 4: Lift group 2 (LF, RM, LR)
  {
    { "LFC", 0 },    // LFC
    { "LFF", +30 },  // LFF - lift
    { nullptr, 0 },  // LFT

    { "LMC", -30 },  // LMC - maintain backward
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", 0 },    // LRC
    { "LRF", +30 },  // LRF - lift
    { nullptr, 0 },  // LRT

    { "RFC", +30 },  // RFC - maintain backward
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", 0 },    // RMC
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - lift
    { nullptr, 0 },  // RMT

    { "RRC", +30 },  // RRC - maintain backward
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 5: Move group 2 backward while lifted
  {
    { "LFC", -30 },  // LFC - backward
    { "LFF", +30 },  // LFF - keep lifted
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - back to center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", -30 },  // LRC - backward
    { "LRF", +30 },  // LRF - keep lifted
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - back to center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", +30 },  // RMC - backward (inverse)
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - keep lifted
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - back to center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 6: Drop group 2
  {
    { "LFC", -30 },  // LFC - maintain backward
    { "LFF", 0 },    // LFF - drop
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - maintain center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", -30 },  // LRC - maintain backward
    { "LRF", 0 },    // LRF - drop
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - maintain center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", +30 },  // RMC - maintain backward
    { nullptr, 0 },  // RMF1
    { "RMF2", 0 },   // RMF2 - drop
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - maintain center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  }
};

// Left walking sequence with relative changes
#define NUM_LEFT_PHASES 6
const ServoMove LEFT_SEQUENCE[NUM_LEFT_PHASES][20] = {
  // Phase 1: Lift group 1 (RF, LM, RR)
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC
    { nullptr, 0 },  // LMF1
    { "LMF2", -30 }, // LMF2 - lift
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC
    { "RFF", +30 },  // RFF - lift
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC
    { "RRF", +30 },  // RRF - lift
    { nullptr, 0 }   // RRT
  },

  // Phase 2: Move group 1 left while lifted
  {
    { nullptr, 0 },   // LFC
    { nullptr, 0 },   // LFF
    { nullptr, 0 },   // LFT

    { "LMC", -30 },   // LMC - left
    { nullptr, 0 },   // LMF1
    { "LMF2", -30 },  // LMF2 - keep lifted
    { nullptr, 0 },   // LMT

    { nullptr, 0 },   // LRC
    { nullptr, 0 },   // LRF
    { nullptr, 0 },   // LRT

    { "RFC", -30 },   // RFC - left
    { "RFF", +30 },   // RFF - keep lifted
    { nullptr, 0 },   // RFT

    { nullptr, 0 },   // RMC
    { nullptr, 0 },   // RMF1
    { nullptr, 0 },   // RMF2
    { nullptr, 0 },   // RMT

    { "RRC", -30 },   // RRC - left
    { "RRF", +30 },   // RRF - keep lifted
    { nullptr, 0 }    // RRT
  },

  // Phase 3: Drop group 1
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", -30 },  // LMC - maintain left
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - drop
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", -30 },  // RFC - maintain left
    { "RFF", 0 },    // RFF - drop
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", -30 },  // RRC - maintain left
    { "RRF", 0 },    // RRF - drop
    { nullptr, 0 }   // RRT
  },

  // Phase 4: Lift group 2 (LF, RM, LR)
  {
    { "LFC", 0 },    // LFC
    { "LFF", +30 },  // LFF - lift
    { nullptr, 0 },  // LFT

    { "LMC", -30 },  // LMC - maintain left
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", 0 },    // LRC
    { "LRF", +30 },  // LRF - lift
    { nullptr, 0 },  // LRT

    { "RFC", -30 },  // RFC - maintain left
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", 0 },    // RMC
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - lift
    { nullptr, 0 },  // RMT

    { "RRC", -30 },  // RRC - maintain left
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 5: Move group 2 left while lifted
  {
    { "LFC", -30 },  // LFC - left
    { "LFF", +30 },  // LFF - keep lifted
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - back to center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", -30 },  // LRC - left
    { "LRF", +30 },  // LRF - keep lifted
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - back to center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", -30 },  // RMC - left
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - keep lifted
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - back to center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 6: Drop group 2
  {
    { "LFC", -30 },  // LFC - maintain left
    { "LFF", 0 },    // LFF - drop
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - maintain center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", -30 },  // LRC - maintain left
    { "LRF", 0 },    // LRF - drop
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - maintain center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", -30 },  // RMC - maintain left
    { nullptr, 0 },  // RMF1
    { "RMF2", 0 },   // RMF2 - drop
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - maintain center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  }
};

// Right walking sequence with relative changes
#define NUM_RIGHT_PHASES 6
const ServoMove RIGHT_SEQUENCE[NUM_RIGHT_PHASES][20] = {
  // Phase 1: Lift group 1 (RF, LM, RR)
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC
    { nullptr, 0 },  // LMF1
    { "LMF2", -30 }, // LMF2 - lift
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC
    { "RFF", +30 },  // RFF - lift
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC
    { "RRF", +30 },  // RRF - lift
    { nullptr, 0 }   // RRT
  },

  // Phase 2: Move group 1 right while lifted
  {
    { nullptr, 0 },   // LFC
    { nullptr, 0 },   // LFF
    { nullptr, 0 },   // LFT

    { "LMC", +30 },   // LMC - right
    { nullptr, 0 },   // LMF1
    { "LMF2", -30 },  // LMF2 - keep lifted
    { nullptr, 0 },   // LMT

    { nullptr, 0 },   // LRC
    { nullptr, 0 },   // LRF
    { nullptr, 0 },   // LRT

    { "RFC", +30 },   // RFC - right
    { "RFF", +30 },   // RFF - keep lifted
    { nullptr, 0 },   // RFT

    { nullptr, 0 },   // RMC
    { nullptr, 0 },   // RMF1
    { nullptr, 0 },   // RMF2
    { nullptr, 0 },   // RMT

    { "RRC", +30 },   // RRC - right
    { "RRF", +30 },   // RRF - keep lifted
    { nullptr, 0 }    // RRT
  },

  // Phase 3: Drop group 1
  {
    { nullptr, 0 },  // LFC
    { nullptr, 0 },  // LFF
    { nullptr, 0 },  // LFT

    { "LMC", +30 },  // LMC - maintain right
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - drop
    { nullptr, 0 },  // LMT

    { nullptr, 0 },  // LRC
    { nullptr, 0 },  // LRF
    { nullptr, 0 },  // LRT

    { "RFC", +30 },  // RFC - maintain right
    { "RFF", 0 },    // RFF - drop
    { nullptr, 0 },  // RFT

    { nullptr, 0 },  // RMC
    { nullptr, 0 },  // RMF1
    { nullptr, 0 },  // RMF2
    { nullptr, 0 },  // RMT

    { "RRC", +30 },  // RRC - maintain right
    { "RRF", 0 },    // RRF - drop
    { nullptr, 0 }   // RRT
  },

  // Phase 4: Lift group 2 (LF, RM, LR)
  {
    { "LFC", 0 },    // LFC
    { "LFF", +30 },  // LFF - lift
    { nullptr, 0 },  // LFT

    { "LMC", +30 },  // LMC - maintain right
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", 0 },    // LRC
    { "LRF", +30 },  // LRF - lift
    { nullptr, 0 },  // LRT

    { "RFC", +30 },  // RFC - maintain right
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", 0 },    // RMC
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - lift
    { nullptr, 0 },  // RMT

    { "RRC", +30 },  // RRC - maintain right
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 5: Move group 2 right while lifted
  {
    { "LFC", +30 },  // LFC - right
    { "LFF", +30 },  // LFF - keep lifted
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - back to center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", +30 },  // LRC - right
    { "LRF", +30 },  // LRF - keep lifted
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - back to center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", +30 },  // RMC - right
    { nullptr, 0 },  // RMF1
    { "RMF2", +30 }, // RMF2 - keep lifted
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - back to center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  },

  // Phase 6: Drop group 2
  {
    { "LFC", +30 },  // LFC - maintain right
    { "LFF", 0 },    // LFF - drop
    { nullptr, 0 },  // LFT

    { "LMC", 0 },    // LMC - maintain center
    { nullptr, 0 },  // LMF1
    { "LMF2", 0 },   // LMF2 - maintain ground
    { nullptr, 0 },  // LMT

    { "LRC", +30 },  // LRC - maintain right
    { "LRF", 0 },    // LRF - drop
    { nullptr, 0 },  // LRT

    { "RFC", 0 },    // RFC - maintain center
    { "RFF", 0 },    // RFF - maintain ground
    { nullptr, 0 },  // RFT

    { "RMC", +30 },  // RMC - maintain right
    { nullptr, 0 },  // RMF1
    { "RMF2", 0 },   // RMF2 - drop
    { nullptr, 0 },  // RMT

    { "RRC", 0 },    // RRC - maintain center
    { "RRF", 0 },    // RRF - maintain ground
    { nullptr, 0 }   // RRT
  }
};

// Rolling sequence with absolute angles
#define NUM_ROLLING_PHASES 6
const ServoPosition ROLLING_SEQUENCE[NUM_ROLLING_PHASES][20] = {
  // Phase 1: Start in standby position
  {
    // Copy STANDBY_POSITION values for all servos
    STANDBY_POSITION[0], STANDBY_POSITION[1], STANDBY_POSITION[2],
    STANDBY_POSITION[3], STANDBY_POSITION[4], STANDBY_POSITION[5],
    STANDBY_POSITION[6], STANDBY_POSITION[7], STANDBY_POSITION[8],
    STANDBY_POSITION[9], STANDBY_POSITION[10], STANDBY_POSITION[11],
    STANDBY_POSITION[12], STANDBY_POSITION[13], STANDBY_POSITION[14],
    STANDBY_POSITION[15], STANDBY_POSITION[16], STANDBY_POSITION[17],
    STANDBY_POSITION[18], STANDBY_POSITION[19] },
  {
    // LEFT FRONT
    { "LFC", 170 },  // Front Coxa - center
    { "LFF", 135 },  // Front Femur - lift
    { "LFT", 95 },   // Front Tibia - tuck

    // LEFT MID
    { "LMC", 62 },    // Mid Coxa - center
    { "LMF1", 100 },  // Mid Femur 1 - lift
    { "LMF2", 70 },   // Mid Femur 2 - lift
    { "LMT", 140 },   // Mid Tibia - tuck

    // LEFT REAR
    { "LRC", 18 },   // Rear Coxa - center
    { "LRF", 145 },  // Rear Femur - lift
    { "LRT", 65 },   // Rear Tibia - tuck

    // RIGHT FRONT
    { "RFC", 10 },   // Front Coxa
    { "RFF", 145 },  // Front Femur
    { "RFT", 90 },   // Front Tibia

    // RIGHT MID
    { "RMC", 100 },   // Mid Coxa
    { "RMF1", 100 },  // Mid Femur 1
    { "RMF2", 115 },  // Mid Femur 2
    { "RMT", 150 },   // Mid Tibia

    // RIGHT REAR
    { "RRC", 175 },  // Rear Coxa
    { "RRF", 140 },  // Rear Femur
    { "RRT", 65 }    // Rear Tibia
  },

  // Phase 3: Start roll - Push with right legs
  {
    // LEFT FRONT
    { "LFC", 170 },  // Front Coxa - center
    { "LFF", 135 },  // Front Femur - lift
    { "LFT", 95 },   // Front Tibia - tuck

    // LEFT MID
    { "LMC", 62 },   // Mid Coxa - center
    { "LMF1", 40 },  // Mid Femur 1 - lift
    { "LMF2", 70 },  // Mid Femur 2 - lift
    { "LMT", 140 },  // Mid Tibia - tuck

    // LEFT REAR
    { "LRC", 18 },   // Rear Coxa - center
    { "LRF", 145 },  // Rear Femur - lift
    { "LRT", 65 },   // Rear Tibia - tuck

    // RIGHT FRONT
    { "RFC", 10 },   // Front Coxa
    { "RFF", 145 },  // Front Femur
    { "RFT", 90 },   // Front Tibia

    // RIGHT MID
    { "RMC", 10 },    // Mid Coxa
    { "RMF1", 100 },  // Mid Femur 1
    { "RMF2", 115 },  // Mid Femur 2
    { "RMT", 150 },   // Mid Tibia

    // RIGHT REAR
    { "RRC", 175 },  // Rear Coxa
    { "RRF", 140 },  // Rear Femur
    { "RRT", 65 }    // Rear Tibia
  },

  // Phase 4: Mid roll - Right legs push, left legs reach
  {
    // LEFT FRONT
    { "LFC", 170 },  // Front Coxa - center
    { "LFF", 135 },  // Front Femur - lift
    { "LFT", 95 },   // Front Tibia - tuck

    // LEFT MID
    { "LMC", 152 },  // Mid Coxa - center
    { "LMF1", 40 },  // Mid Femur 1 - lift
    { "LMF2", 70 },  // Mid Femur 2 - lift
    { "LMT", 140 },  // Mid Tibia - tuck

    // LEFT REAR
    { "LRC", 18 },   // Rear Coxa - center
    { "LRF", 145 },  // Rear Femur - lift
    { "LRT", 65 },   // Rear Tibia - tuck

    // RIGHT FRONT
    { "RFC", 10 },   // Front Coxa
    { "RFF", 145 },  // Front Femur
    { "RFT", 90 },   // Front Tibia

    // RIGHT MID
    { "RMC", 10 },    // Mid Coxa
    { "RMF1", 135 },  // Mid Femur 1
    { "RMF2", 115 },  // Mid Femur 2
    { "RMT", 150 },   // Mid Tibia

    // RIGHT REAR
    { "RRC", 175 },  // Rear Coxa
    { "RRF", 140 },  // Rear Femur
    { "RRT", 65 }    // Rear Tibia
  },

  // Phase 5: Complete roll - Left legs touch down
  {
    // LEFT FRONT
    { "LFC", 170 },  // Front Coxa - center
    { "LFF", 135 },  // Front Femur - lift
    { "LFT", 95 },   // Front Tibia - tuck

    // LEFT MID
    { "LMC", 152 },  // Mid Coxa - center
    { "LMF1", 10 },  // Mid Femur 1 - lift
    { "LMF2", 75 },  // Mid Femur 2 - lift
    { "LMT", 90 },   // Mid Tibia - tuck

    // LEFT REAR
    { "LRC", 18 },   // Rear Coxa - center
    { "LRF", 145 },  // Rear Femur - lift
    { "LRT", 65 },   // Rear Tibia - tuck

    // RIGHT FRONT
    { "RFC", 10 },   // Front Coxa
    { "RFF", 145 },  // Front Femur
    { "RFT", 90 },   // Front Tibia

    // RIGHT MID
    { "RMC", 10 },    // Mid Coxa
    { "RMF1", 135 },  // Mid Femur 1
    { "RMF2", 115 },  // Mid Femur 2
    { "RMT", 150 },   // Mid Tibia

    // RIGHT REAR
    { "RRC", 175 },  // Rear Coxa
    { "RRF", 140 },  // Rear Femur
    { "RRT", 65 }    // Rear Tibia
  },

  // Phase 6: Start next roll - Push with left legs
  {
    // LEFT FRONT
    { "LFC", 170 },  // Front Coxa - center
    { "LFF", 110 },  // Front Femur - lift
    { "LFT", 100 },  // Front Tibia - tuck

    // LEFT MID
    { "LMC", 152 },  // Mid Coxa - center
    { "LMF1", 30 },  // Mid Femur 1 - lift
    { "LMF2", 75 },  // Mid Femur 2 - lift
    { "LMT", 90 },   // Mid Tibia - tuck

    // LEFT REAR
    { "LRC", 18 },   // Rear Coxa - center
    { "LRF", 115 },  // Rear Femur - lift
    { "LRT", 60 },   // Rear Tibia - tuck

    // RIGHT FRONT
    { "RFC", 10 },   // Front Coxa
    { "RFF", 145 },  // Front Femur
    { "RFT", 125 },  // Front Tibia

    // RIGHT MID
    { "RMC", 10 },    // Mid Coxa
    { "RMF1", 125 },  // Mid Femur 1
    { "RMF2", 115 },  // Mid Femur 2
    { "RMT", 90 },    // Mid Tibia

    // RIGHT REAR
    { "RRC", 175 },  // Rear Coxa
    { "RRF", 140 },  // Rear Femur
    { "RRT", 100 }   // Rear Tibia
  },

};

#endif  // MOTION_H