#ifndef __DEBUG_H
#define __DEBUG_H

#include "DEV_Config.h"

#define USE_DEBUG 1
#if USE_DEBUG
  #define Debug(__info) Serial.print(__info)
#else
  #define Debug(__info)  
#endif

#endif
