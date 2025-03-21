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
  { "LFC", 135 },  // Front Coxa
  { "LFF", 80 },   // Front Femur
  { "LFT", 35 },   // Front Tibia

  // LEFT MID
  { "LMC", 62 },    // Mid Coxa
  { "LMF1", 145 },  // Mid Femur 1
  { "LMF2", 70 },   // Mid Femur 2
  { "LMT", 140 },   // Mid Tibia

  // LEFT REAR
  { "LRC", 53 },   // Rear Coxa
  { "LRF", 90 },   // Rear Femur
  { "LRT", 125 },  // Rear Tibia

  // RIGHT FRONT
  { "RFC", 45 },   // Front Coxa
  { "RFF", 105 },  // Front Femur
  { "RFT", 55 },   // Front Tibia

  // RIGHT MID
  { "RMC", 100 },   // Mid Coxa
  { "RMF1", 0 },    // Mid Femur 1
  { "RMF2", 115 },  // Mid Femur 2
  { "RMT", 150 },   // Mid Tibia

  // RIGHT REAR
  { "RRC", 140 },  // Rear Coxa
  { "RRF", 100 },  // Rear Femur
  { "RRT", 35 }    // Rear Tibia
};

// Add this helper struct for relative movements
struct ServoMove {
  const char* id;
  int change;  // Amount to add/subtract from standby position
};

// Forward walking sequence with relative changes
#define NUM_FORWARD_PHASES 4
const ServoMove FORWARD_SEQUENCE[NUM_FORWARD_PHASES][20] = {
  // Phase 1: Lift and move forward group 1 (RF, LM, RR legs)
  {
    { "LFC", -20 },  // LFC: no change from standby
    { nullptr, 0 },  // LFF: no change
    { nullptr, 0 },  // LFT: no change

    { nullptr, 0 },  // Add 13 to standby position
    { nullptr, 0 },  // LMF1: no change
    { nullptr, 0 },  // LMF2: no change
    { nullptr, 0 },  // LMT: no change

    { "LRC", +40 },  // Add 22 to standby position
    { nullptr, 0 },  // LRF: no change
    { nullptr, 0 },  // LRT: no change

    { nullptr, 0 },  // Add 20 to standby position
    { nullptr, 0 },  // RFF: no change
    { nullptr, 0 },  // RFT: no change

    { "RMC", +40 },  // Subtract 15 from standby position
    { nullptr, 0 },  // RMF1: no change
    { nullptr, 0 },  // RMF2: no change
    { nullptr, 0 },  // RMT: no change

    { nullptr, 0 },  // RRC: no change
    { nullptr, 0 },  // RRF: no change
    { nullptr, 0 }   // RRT: no change
  },

  // Phase 2: Return to standby (all changes are 0)
  {
    { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 } },

  // Phase 3: Move other legs
  {
    { nullptr, 0 },  // Subtract 20 from standby
    { nullptr, 0 },  // LFF: no change
    { nullptr, 0 },  // LFT: no change
    { "LMC", +40 },  // Subtract 17 from standby
    { nullptr, 0 },  // LMF1: no change
    { nullptr, 0 },  // LMF2: no change
    { nullptr, 0 },  // LMT: no change
    { nullptr, 0 },  // LRC: no change
    { nullptr, 0 },  // LRF: no change
    { nullptr, 0 },  // LRT: no change
    { "RFC", +40 },  // RFC: no change
    { nullptr, 0 },  // RFF: no change
    { nullptr, 0 },  // RFT: no change
    { nullptr, 0 },  // Add 15 to standby
    { nullptr, 0 },  // RMF1: no change
    { nullptr, 0 },  // RMF2: no change
    { nullptr, 0 },  // RMT: no change
    { "RRC", +40 },  // Subtract 20 from standby
    { nullptr, 0 },  // RRF: no change
    { nullptr, 0 }   // RRT: no change
  },

  // Phase 4: Return to standby (all changes are 0)
  {
    { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 }, { nullptr, 0 } }
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
  // Phase 2: Prepare for roll - Lift left side
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