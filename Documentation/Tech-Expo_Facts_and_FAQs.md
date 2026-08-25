# Rollopod — Tech-Expo Operator Guide: Quick Facts & FAQs

---

## 🏆 Project Overview & Meta Information

* **Project Title:** Rollopod — A Transforming Hexapod Robot with Dual-Mode Walking and Rolling Locomotion
* **Team Members:** Parag Patil, Rutu Patel
* **Institution:** Parul Institute of Technology, Parul University
* **Expo Category:** Senior Category
* **Exhibition Theme:** Robotics & Aerial Robotics
* **Future Vision:** Core locomotion platform for the **Modular Robotic Field Assistant (MRFA)**

---

## ⚡ 1. The "30-Second Elevator Pitch"
> *"Rollopod is a transformable hybrid robot that solves the classic mobility dilemma in mobile robotics: wheeled rovers are fast on flat ground but get stuck on obstacles, while walking hexapods can step over anything but crawl slowly and waste energy. Rollopod bridges this gap by using a shared transformable mechanical structure. Its 6 articulated legs fold edge-to-edge into dual 400 mm rolling rings for high-speed travel (up to 7.5 km/h), and unfold into a terrain-adaptive hexapod for stairs, rubble, and rough terrain—all while keeping the central sensor payload upright and stabilized through a bearing-decoupled gravity pendulum."*

---

## 📊 2. Master Quick-Facts Sheet (Numbers & Specs)

| Category | Parameter | Specification / Exact Value |
| :--- | :--- | :--- |
| **Physical Dimensions** | Length × Width × Height | **40 cm × 50 cm × 40 cm** (0.40 m × 0.50 m × 0.40 m) |
| **Mass Breakdown** | Total System Mass | **~11.0 kg** |
| | Left Wheel / Leg Assembly | **~5.0 kg** (45.45%) |
| | Right Wheel / Leg Assembly | **~5.0 kg** (45.45%) |
| | Central Suspended Pod | **~1.0 kg** (9.10%) |
| **Wheel Geometry** | Wheel Outer Diameter ($D$) | **400 mm** (0.40 m / 15.75 in) |
| | Wheel Circumference ($C$) | **1.2566 m** (1256.6 mm) |
| | Arc Segment per Leg (3 per side) | **418.9 mm** per leg arc |
| **Drive Motors** | Rolling Drive Actuators | **2x High-Torque DC Geared Motors** (100 RPM, 25 kg·cm / 2.45 N·m each) |
| | Total Rolling Drive Torque | **≈ 4.90 N·m combined** |
| | Leg Articulation / Transformation | **18x High-Torque Servos** (3 DOF per leg × 6 legs) |
| **Rolling Speeds** | Max Theoretical Speed (100% PWM) | **2.09 m/s (7.54 km/h / 4.68 mph)** |
| | Operating Waddle-Roll Speed | **1.05 – 1.25 m/s (3.8 – 4.5 km/h / 2.4 – 2.8 mph)** |
| **Walking Speeds** | Tripod Gait Cruising Speed | **0.15 – 0.25 m/s (0.54 – 0.90 km/h)** |
| | Max Peak Step Speed | **0.30 m/s (1.08 km/h)** |
| **Electronics & Control** | Microcontrollers | **Master ESP32 Bridge** (Host) + **Slave ESP32-C6** (On-Robot Edge) |
| | Wireless Protocol | **ESP-NOW** Point-to-Point Broadcast (10–30 ms latency) |
| | Motor Drivers | **2x Cytron MD13S** (13A continuous per channel) |
| | Servo PWM Drivers | **Dual PCA9685** 16-Channel 12-Bit I2C PWM Drivers (50 Hz) |
| | Sensor Payload | **MPU6050 6-DOF IMU**, Intel RealSense 3D Depth Camera, LiDAR |
| **Power Architecture** | Logic Battery Rail | **3S 5000 mAh LiPo** (Regulated via DC-DC Buck Converter) |
| | Actuator Battery Rail | **3S 6200 mAh / 2500 mAh LiPo Packs** (Dedicated High-Current Rails) |
| | Grounding Scheme | **Unified Common Ground Topology** |

---

## ❓ 3. Frequently Asked Questions (FAQs) for Operators

### 🟢 A. Concept & Novelty Questions

#### Q1: Why not just put regular wheels on the bottom of a hexapod chassis?
**Answer:** Adding dedicated permanent wheels and separate drive axles adds massive dead weight, increases bulk, reduces ground clearance, and makes the legs vulnerable to catching on obstacles. Rollopod utilizes **shared structural transformation**—the legs *themselves* are the wheels. When folded, the curved, treaded leg links form the outer rolling rings.

#### Q2: How does Rollopod compare to existing bio-inspired robots like Festo BionicWheelBot?
**Answer:** Festo’s robot rolls like an acrobat over its entire body, which violently tumbles any cameras or onboard electronics. Rollopod features a **bearing-decoupled suspended central pod** that remains horizontal and forward-facing at all times, allowing continuous LiDAR and 3D depth scanning even while rolling at high speeds.

---

### ⚙️ B. Mechanical & Kinematic Architecture Questions

#### Q3: How does the central pod stay upright when the robot rolls without flipping over?
**Answer:** The central ~1 kg pod is mounted on **precision radial ball bearings** around the continuous central rod, with its Center of Gravity (CG) concentrated **below** the axis. It acts as a **passive gravity-biased pendulum**. Gravity holds the pod level and facing forward, completely isolating the sensitive sensors from the rotation of the outer rings. It does **not** require complex Segway-style inverted-pendulum balancing.

#### Q4: What is the central rod, and does it spin freely?
**Answer:** The central rod is a **single rigid reaction rod** that is rigidly locked to both motor rotor shafts. It forms one mechanically coupled rotating assembly. It is **NOT** fixed to the chassis, **NOT** fixed to the ground, and does **NOT** spin like a free idler.

#### Q5: How can Rollopod roll forward if both motor rotors are locked to the same rod without a tail/skid?
**Answer:** This is Rollopod’s proprietary **Dynamic Torque Anchoring (Waddle-Roll Gait)**. Instead of raw on/off pulses, both motors operate on a base PWM (50–60%) overlaid with a 180° phase-shifted low-frequency sine wave (1.5 Hz – 3.0 Hz). When the left motor torque rises and the right decreases, the robot uses the internal gearbox resistance and inertia of the right wheel as a temporary dynamic brace to push the left side forward, and vice versa. This creates smooth, tail-less forward rolling.

#### Q6: Can Rollopod turn in place (zero-radius steering)?
**Answer:** **Yes!** When the left and right DC motors are commanded in opposite directions (Left = CW, Right = CCW), the stator reactions push the two 5 kg side assemblies in opposite directions, executing a 360° zero-radius skid turn on the spot.

---

### 🔌 C. Electronics, Power & Wireless Control Questions

#### Q7: How do you prevent high servo currents from resetting or crashing the microcontrollers?
**Answer:** We use an **Isolated Dual-Power Architecture**. Logic electronics (ESP32, IMU, sensors) run on a dedicated 3S LiPo battery through a regulated buck converter. High-current actuators (18 servos + 2 Cytron DC drivers) draw from separate heavy-duty LiPo packs. Both rails share a **unified common ground** to guarantee clean I2C communication without inductive voltage dips (brownouts).

#### Q8: What wireless protocol is used, and why not standard Wi-Fi or Bluetooth?
**Answer:** We use **ESP-NOW** (point-to-point wireless broadcast by Espressif). Standard Wi-Fi has unpredictable packet buffering (100–300 ms) and connection drops. ESP-NOW provides **deterministic low-latency communication (10–30 ms)** without needing an external Wi-Fi router.

#### Q9: What happens if an ESP-NOW wireless packet drops during rolling? Will the motors de-sync?
**Answer:** **No.** We use **Edge Parametric Calculation**. The master controller only sends a small broadcast packet containing the gait mathematical parameters (`Base_PWM`, `Amplitude`, `Frequency`). When received, both ESP32-C6 motor controllers reset their internal hardware timers (`micros()`) to `t=0` simultaneously and calculate the sine wave locally on the chip. Even if wireless communication drops for several seconds, both motors remain in absolute mathematical lockstep.

#### Q10: How do you prevent the motors from back-driving when one is stopped?
**Answer:** Each motor has a **Quadrature Optical/Magnetic Encoder** running at 50 Hz on the ESP32-C6. When speed is commanded to zero, the controller latches its position (`P_hold`) and runs an **Active Zero-Speed Position Hold PID**, instantly applying counter-torque to lock the shaft against any reaction torque transmitted through the central rod.

---

### 🛠️ D. Prototype Evolution & Materials Questions

#### Q11: What materials were used to build the physical prototype?
**Answer:** 
* **Structure:** High-strength aluminium extrusion frame and CNC-machined carbon fibre linkage plates for high stiffness-to-weight ratio.
* **Leg Appendages:** Redesigned CNC powder-coated steel legs to handle high dynamic ground impacts.
* **Bearings:** Industrial-grade deep-groove radial ball bearings for pod decoupling.

#### Q12: What design challenges were discovered during prototype testing?
**Answer:**
1. **Gearbox Failure:** Early tests with standard plastic-gear DC motors stripped teeth under heavy shock loads; we upgraded to all-metal 25 kg·cm steel gearboxes.
2. **Current Spikes:** Simultaneous 18-servo movement caused voltage dips, which led directly to the implementation of the isolated dual-battery power rail.
3. **Ground Indexing:** Before unfolding into walking mode, the robot uses IMU orientation feedback to verify that legs are facing downward toward the ground before opening.

---

### 🚀 E. Real-World Applications & Future Scope

#### Q13: What are the practical applications of Rollopod?
**Answer:**
1. **Search & Rescue in Disasters:** Rapidly rolls over paved roads to reach disaster zones, then unfolds into hexapod mode to climb through collapsed concrete rubble, stairs, and voids.
2. **Industrial & Pipeline Inspection:** Traverses smooth factory floors and pipeline corridors in rolling mode, stepping over curbs, pipes, and obstacles without stopping.
3. **Agricultural Surveying:** Navigates muddy fields and furrowed crop rows without compacting soil or damaging plant beds.
4. **Planetary / Subterranean Exploration:** Enters uncharted caves, craters, and rough terrains where traditional 4-wheel rovers get permanently trapped.

#### Q14: What is the MRFA vision?
**Answer:** Rollopod is the mobility subsystem for the **Modular Robotic Field Assistant (MRFA)**. Future MRFA units will feature hot-swappable payload bays (thermal cameras, gas detectors, robotic manipulator arms), edge AI for real-time terrain classification, and collaborative multi-robot swarm mapping in GPS-denied environments.

---

## 🎯 4. Operator Quick Cheat-Sheet (At-A-Glance Numbers)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ROLLOPOD AT A GLANCE                            │
├────────────────────────────────┬───────────────────────────────────────┤
│ Mass                           │ 11 kg (5 kg Left + 5 kg Right + 1 kg Pod)│
│ Dimensions                     │ 40 cm (L) × 50 cm (W) × 40 cm (H)     │
│ Outer Wheel Diameter           │ 400 mm (15.75 inches)                 │
│ Rolling Speed (Operating)      │ 1.05 – 1.25 m/s (~4.0 km/h)           │
│ Rolling Speed (Top Max)        │ 2.09 m/s (7.54 km/h)                  │
│ Walking Speed (Tripod Gait)    │ 0.15 – 0.25 m/s (~0.7 km/h)           │
│ DC Drive Torque                │ 25 kg·cm (2.45 N·m) × 2 = 4.90 N·m    │
│ Total Servos                   │ 18x High-Torque Servos (PCA9685 @ 50Hz)│
│ Wireless Communication         │ ESP-NOW (10–30 ms low latency)        │
│ Power Architecture             │ Fully Isolated Logic & Actuator Rails │
└────────────────────────────────┴───────────────────────────────────────┘
```
