# KiBee V0  
**Compact AI Home Robot with Modular Head & Base**  
Product & Engineering Documentation  

**Version 0.2 • July 2026**  
Derived from the Rollopod Platform  

---

## 1. Overview

KiBee V0 is a compact, modular AI home robot derived from Rollopod’s rolling-mode architecture. KiBee introduces a **Modular Head & Base design**:

1. **Standalone Head Companion**: The Head contains the core AI display, voice, audio, touch sensors, ESP32 microcontroller, and internal 1S battery. It operates independently as a portable desk or handheld AI companion.
2. **Rolling Base Platform**: The Base houses two DC geared motors, motor drivers, a dedicated secondary microcontroller, ToF sensors, IMU, buttons, touch sensors, and a high-capacity 1S or 2S battery.
3. **Pogo Pin Interface & Docking**: The Head connects to the Base via a magnetic/mechanical **Pogo Pin interface**. When docked, the Head accepts the Base to activate full rolling robot mobility.
4. **AirPods-Style Power Ecosystem**: Just like wireless earbuds and their charging case, the Base acts as a charging station for the Head. The Head can be charged directly from the Base battery or via External Charging. The Base is charged via External Charging (which simultaneously tops up the Head when docked).

KiBee permanently retains Rollopod's dual-wheel differential rolling geometry while eliminating legged transformation complexity, offering a versatile, low-cost home companion ecosystem.

---

## 2. Core Philosophy

> A modular companion experience: A standalone desktop AI head that snaps onto a Rollopod-derived rolling base for room-to-room mobility.

**Key advantages of this approach:**

- **Versatile Usability**: Use the Head independently on a desk/nightstand or snap it to the Base for autonomous mobility.
- **Wireless Pogo Pin Docking**: Hot-swappable connection with automatic dock detection and instant control coupling.
- **AirPods Charging Model**: Intelligent power sharing where the Base battery recharges the Head battery on the go.
- **Stable Locomotion**: Low centre of gravity and wide dual-wheel base inherited from Rollopod's rolling mode.
- **Clean Hardware Separation**: High-level interaction logic (Head) decoupled from deterministic real-time motor control (Base).

---

## 3. Relationship with Rollopod

KiBee inherits Rollopod’s core rolling mechanism while introducing modular companion hardware:

- **Rollopod**: Dual-mode hybrid robot (walking + rolling) for rugged outdoor research.
- **KiBee V0**: Pure rolling architecture featuring a **Modular Head + Base** design optimized for consumer home AI interaction.

---

## 4. Mechanical Architecture

### 4.1 Chassis & Base

The Base uses a fixed dual-ring rolling chassis derived directly from Rollopod’s rolling mode:
- Two side rolling rings for smooth indoor mobility
- Suspended central chassis housing motors, batteries, and sensor suite
- Mating guide socket with **Pogo Pin contacts** for securing and connecting the Head
- Low-centre-of-gravity design with differential drive steering

### 4.2 Locomotion Subsystem

- Two DC geared motors, one per ring, controlled via an onboard Motor Driver
- Differential drive enabling forward/reverse movement and zero-radius turns
- Suitable for tiles, wooden floors, carpets, and smooth indoor surfaces

### 4.3 Modular Head Subsystem

- Ergonomic, rounded companion form factor for handheld or desktop use
- Houses display, audio, touch surface, head IMU, ESP32 controller, and 1S battery
- Pogo pin contact interface on the bottom for effortless snap-on docking

---

## 5. Appearance & Industrial Design

KiBee combines soft, approachable consumer aesthetics with functional modularity:
- **Visual Style**: Friendly, rounded forms (reminiscent of desktop AI pets and smart earbuds).
- **Docking Experience**: Satisfying snap-fit magnetic alignment with Pogo pins for blind docking.
- **Expression Display**: OLED display providing dynamic facial expressions, eye animations, and status indicators.

---

## 6. Electronics Architecture

KiBee V0 divides responsibilities across two specialized hardware modules connected via Pogo pins:

``` text
┌─────────────────────────────────────────────────────────────┐
│                        HEAD MODULE                          │
│  ESP32 MC  │  OLED Display  │  LEDs  │  Mic  │  Speaker     │
│  IMU       │  Touch Sensors │  1S Battery                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Pogo Pins (Power + Serial)
┌──────────────────────────────┴──────────────────────────────┐
│                        BASE MODULE                          │
│  Small Microcontroller  │  Dual DC Motors  │  Motor Driver  │
│  1S/2S Battery          │  IMU             │  ToF Sensors   │
│  Touch Sensors          │  Buttons         │  Status LEDs   │
└──────────────────────────────┘
```

### 6.1 Head Subsystem Specifications

- **Main Controller**: ESP32 Microcontroller (handles UI, OLED rendering, voice/audio pipeline, touch processing).
- **Display**: OLED screen for animated eyes, expressions, and UI notifications.
- **Visual Feedback**: RGB LEDs.
- **Audio**: Integrated Microphone (voice commands) & Speaker (speech/sound effects).
- **Sensors**: Head IMU (detects pickup/tilting/gestures) & Touch Sensors (capacitive head petting/tap interactions).
- **Power**: 1S LiPo/Li-ion internal battery.
- **Interface**: Pogo pin pad array for charging, UART/I2C communication, and dock detection.

### 6.2 Base Subsystem Specifications

- **Secondary Controller**: Dedicated Small Microcontroller (handles real-time motor PID loops, ToF obstacle sensing, and power routing).
- **Actuation**: 2 × DC Geared Motors + Motor Driver module.
- **Sensors**: Chassis IMU (orientation & balance telemetry), Time-of-Flight (ToF) distance sensors (obstacle/cliff detection), Touch Sensors, and Wheel Encoders.
- **UI / Inputs**: Physical Buttons & Status LEDs.
- **Power**: 1S or 2S High-Capacity Battery (tailored for motor current demands).
- **Interface**: Spring-loaded Pogo Pins & External Charging Port (USB-C / DC Barrel Jack).

### 6.3 Power & Charging Architecture (AirPods Concept)

| Mode | External Power | Base Battery | Head Battery State |
|------|----------------|--------------|--------------------|
| **Standalone Head** | Unplugged | N/A | Powered by internal 1S battery |
| **Direct Head Charging** | USB Connected to Head | N/A | Charged directly from External Power |
| **Docked (On the go)** | Unplugged | Discharging to Motors & Pogo Pins | Charged from Base Battery via Pogo Pins |
| **Docked Charging** | USB Connected to Base | Charged from External Power | Charged from External Power via Base Pogo Pins |

---

## 7. KiBee V0 Feature Matrix

| Feature | Standalone Head Mode | Combined Mobile Mode (Head + Base) |
|---------|-----------------------|------------------------------------|
| **AI Assistant & Voice** | Active (Mic + Speaker + ESP32) | Active |
| **OLED Expressions** | Active | Active |
| **Touch Interaction** | Active (Head Touch Sensors) | Active (Head & Base Touch Sensors) |
| **Locomotion** | Disabled (Desktop mode) | Active (2x DC Motors & Differential Steering) |
| **Obstacle Sensing** | N/A | Active (ToF Sensors + Base IMU) |
| **Battery Life** | Internal 1S Battery | Extended (Base battery powers/charges Head) |

---

## 8. Target Environments & Use Cases

1. **Desktop Companion (Standalone Head)**: Sits on office desks or nightstands as an interactive voice AI assistant, display clock, or ambient companion.
2. **Mobile Home Companion (Combined Unit)**: Rolls around homes and offices for autonomous monitoring, room delivery, and interactive follow-me modes.

---

## 9. Development Status (V0)

- [x] Dual-ring rolling geometry (from Rollopod research)
- [x] Definition of Modular Head & Base architecture
- [ ] Pogo Pin connector pinout & magnetic latch CAD design
- [ ] Base Small MCU firmware (Motor driver + ToF sensor processing)
- [ ] ESP32 Head firmware (OLED display + Audio + Dock protocol)
- [ ] AirPods-style power management and dual-battery charging circuit validation

---

## 10. Summary

KiBee V0 redefines the personal robot form factor by marrying Rollopod’s rolling chassis with a **Modular Head & Base architecture**. Connected via Pogo pins and powered through an AirPods-inspired dual-battery system, KiBee offers unprecedented flexibility: a lightweight desktop companion when detached, and a fully capable mobile AI robot when docked.

---

**Document Control**  
Title: KiBee V0 – Product & Engineering Documentation  
Version: 0.2 (Modular Architecture Specification)  
Date: July 2026  
Author: Parag Patil  
Status: Active Engineering Specification  
