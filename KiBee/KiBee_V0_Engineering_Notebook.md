# KiBee V0

## Engineering Notebook

**Project:** KiBee V0\
**Platform:** Rollopod Mobility Platform\
**Author:** Parag Patil

------------------------------------------------------------------------

# 1. Overview

KiBee V0 is a compact AI companion robot derived directly from
**Rollopod's Rolling Mode**. Unlike Rollopod, KiBee permanently remains
in the rolling configuration and is optimized for indoor environments.

KiBee is intended to validate the reusable technologies that will
eventually power future Rollopod generations, including AI, navigation,
electronics, and human-robot interaction.

------------------------------------------------------------------------

# 2. Vision

Design a friendly, intelligent companion robot that:

-   Uses Rollopod's suspended-body rolling architecture.
-   Is practical for homes, offices, and laboratories.
-   Demonstrates AI interaction.
-   Provides a reusable robotics platform for future products.

------------------------------------------------------------------------

# 3. Design Philosophy

-   Reuse Rollopod rolling architecture.
-   No walking or transformation mechanism.
-   Consumer-friendly appearance.
-   Quiet and efficient.
-   Modular and upgradeable.
-   Easy to manufacture and maintain.

------------------------------------------------------------------------

# 4. Relationship with Rollopod

``` text
Rollopod Mobility Platform
        │
        ├── Hybrid Walking + Rolling
        │
        └── Rolling Mode
                │
                ▼
             KiBee V0
```

Rollopod remains the flagship hybrid locomotion platform.

KiBee is the first practical consumer robot built from Rollopod's
rolling technology.

------------------------------------------------------------------------

# 5. Mechanical Architecture

## Chassis

-   Dual rolling rings
-   Suspended central body
-   Fixed rolling configuration
-   Low center of gravity
-   Wide wheel spacing

## Mobility

-   Two independently driven wheels
-   Differential steering
-   Zero-radius turning
-   Indoor optimized

------------------------------------------------------------------------

# 6. Body Layout

The central body contains:

-   Raspberry Pi 5
-   ESP32
-   Battery
-   Motor driver
-   Camera
-   Microphones
-   Speaker
-   Display
-   IMU
-   Expansion interface

------------------------------------------------------------------------

# 7. Electronics

## Main Processor

**Raspberry Pi 5**

Responsibilities:

-   AI
-   Navigation
-   Vision
-   Audio
-   Networking
-   User Interface

## Real-Time Controller

**ESP32**

Responsibilities:

-   Motor control
-   Battery monitoring
-   IMU processing
-   Encoder feedback
-   Safety functions

------------------------------------------------------------------------

# 8. Mobility Hardware

-   2 × DC geared motors
-   Motor driver
-   IMU
-   Wheel encoders

------------------------------------------------------------------------

# 9. Software Stack

``` text
Application
│
├── AI Assistant
├── Voice
├── Navigation
├── Vision
├── Display
└── Motion

ROS2 / Ubuntu

ESP32 Firmware

Motor Driver
```

------------------------------------------------------------------------

# 10. Core Features (V0)

-   Autonomous movement
-   AI assistant
-   Voice interaction
-   Indoor navigation
-   Remote control

------------------------------------------------------------------------

# 11. Design Decisions

## Why use Rollopod's rolling mode?

-   Already developed architecture
-   Stable platform
-   Efficient indoor movement
-   Lower mechanical complexity
-   Lower power consumption

## Why Raspberry Pi + ESP32?

-   High-level AI separated from deterministic motor control.
-   Easy future expansion.
-   ROS2 compatibility.

------------------------------------------------------------------------

# 12. Future Ideas

-   Dock charging
-   Face recognition
-   Person following
-   Vision AI
-   Smart home integration
-   Modular accessories
-   Camera modules
-   LiDAR module

------------------------------------------------------------------------

# 13. Open Questions

-   Final wheel diameter?
-   Motor selection?
-   Battery capacity?
-   Cooling strategy?
-   Docking mechanism?
-   Camera position?
-   Enclosure material?
-   Speaker placement?

------------------------------------------------------------------------

# 14. Development Checklist

-   [ ] CAD Design
-   [ ] Chassis Prototype
-   [ ] Electronics Integration
-   [ ] Motion Testing
-   [ ] Voice Assistant
-   [ ] AI Integration
-   [ ] Navigation
-   [ ] First Public Demonstration

------------------------------------------------------------------------

# 15. Notes

This document is intended as a living engineering notebook. Design
decisions, sketches, hardware selections, software architecture, and
future ideas should be updated continuously throughout KiBee's
development.
