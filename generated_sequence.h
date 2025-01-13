#define NUM_PHASES 5
const ServoPosition SEQUENCE[NUM_PHASES][20] = {
    // Phase 1
    {
        // Left Front
        {"LFC", 45}, {"LFT", 70}, {"LFB", 180}, 
        // Left Mid
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0}, 
        // Left Back
        {"LBC", 45}, {"LBT", 70}, {"LBB", 180}, 
        // Right Front
        {"RFC", 45}, {"RFT", 70}, {"RFB", 180}, 
        // Right Mid
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0}, 
        // Right Back
        {"RBC", 45}, {"RBT", 70}, {"RBB", 180}, 
    },
    // Phase 2
    {
        // Left Front
        {"LFC", 65}, {"LFT", 50}, {"LFB", 180}, 
        // Left Mid
        {"LMC", 70}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0}, 
        // Left Back
        {"LBC", 65}, {"LBT", 50}, {"LBB", 180}, 
        // Right Front
        {"RFC", 25}, {"RFT", 70}, {"RFB", 180}, 
        // Right Mid
        {"RMC", 110}, {"RMT", 160}, {"RMB", 80}, {"RMF", 0}, 
        // Right Back
        {"RBC", 25}, {"RBT", 70}, {"RBB", 180}, 
    },
    // Phase 3
    {
        // Left Front
        {"LFC", 45}, {"LFT", 70}, {"LFB", 180}, 
        // Left Mid
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0}, 
        // Left Back
        {"LBC", 45}, {"LBT", 70}, {"LBB", 180}, 
        // Right Front
        {"RFC", 45}, {"RFT", 70}, {"RFB", 180}, 
        // Right Mid
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0}, 
        // Right Back
        {"RBC", 45}, {"RBT", 70}, {"RBB", 180}, 
    },
    // Phase 4
    {
        // Left Front
        {"LFC", 25}, {"LFT", 70}, {"LFB", 180}, 
        // Left Mid
        {"LMC", 110}, {"LMT", 160}, {"LMB", 80}, {"LMF", 0}, 
        // Left Back
        {"LBC", 25}, {"LBT", 70}, {"LBB", 180}, 
        // Right Front
        {"RFC", 65}, {"RFT", 50}, {"RFB", 180}, 
        // Right Mid
        {"RMC", 70}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0}, 
        // Right Back
        {"RBC", 65}, {"RBT", 50}, {"RBB", 180}, 
    },
    // Phase 5
    {
        // Left Front
        {"LFC", 45}, {"LFT", 70}, {"LFB", 180}, 
        // Left Mid
        {"LMC", 90}, {"LMT", 160}, {"LMB", 100}, {"LMF", 0}, 
        // Left Back
        {"LBC", 45}, {"LBT", 70}, {"LBB", 180}, 
        // Right Front
        {"RFC", 45}, {"RFT", 70}, {"RFB", 180}, 
        // Right Mid
        {"RMC", 90}, {"RMT", 160}, {"RMB", 100}, {"RMF", 0}, 
        // Right Back
        {"RBC", 45}, {"RBT", 70}, {"RBB", 180}, 
    }
};
