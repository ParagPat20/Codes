# Rollopod - A Transforming Hexapod Robot with Dual-Mode Walking and Rolling Locomotion

## Theme

**Category:** Senior Category  
**Theme:** Robotics & Aerial Robotics

## Abstract

Rollopod is a transformable mobile robot designed to combine the terrain adaptability of a six-legged walking platform with the potentially higher travel efficiency of a rolling platform. Conventional hexapods provide multiple ground contacts and can negotiate uneven terrain, but their articulated gait generally limits travel speed and increases control complexity. Conventional rolling robots can move efficiently on suitable surfaces, but their fixed geometry is less suited to obstacles, discontinuous terrain, and continuous scanning from a stable central payload. The proposed system addresses these limitations through a dual-ring architecture in which the three legs on each side fold inward and form a continuous rolling ring; the robot therefore uses the same structural leg assemblies for walking and rolling rather than carrying independent permanent wheels.

The project methodology combines CAD-based mechanical development, servo-actuated transformation, distributed embedded control, wireless command transfer, and sensor-oriented architecture. The documented control system uses a PC Python interface, a USB-connected ESP32 master bridge, ESP-NOW communication, an on-robot ESP32 slave, I2C-connected PCA9685 PWM drivers, and servo actuators. The current project documentation records the mechanical concept and CAD reference views, electronics and power architecture, control software structure, ESP-NOW setup procedures, and an ongoing prototype-development effort. Autonomous terrain adaptation, environmental scanning, transformation validation, and performance measurement remain under development or require experimental validation. The significance of Rollopod is its attempt to integrate two complementary locomotion modes while keeping the central body suspended and available for sensing and control across operating states.

## Introduction

Mobile robots must operate across surfaces that differ in smoothness, continuity, slope, and obstacle density. A conventional hexapod distributes its load over six legs and can maintain support when individual feet encounter uneven ground. This arrangement is useful for terrain adaptability, but walking requires repeated leg lifting, positioning, and synchronization. As a result, a legged platform may have lower travel efficiency on smooth ground than a rolling platform, and its many actuated joints increase the demands on power, control, and mechanical coordination.

Rolling robots have the opposite trade-off. Wheels can provide efficient continuous motion on prepared or relatively smooth surfaces, but a fixed wheeled geometry has limited ability to step over obstacles, bridge gaps, or alter its support configuration. A rolling platform may also make it difficult to keep a sensing payload stable and forward-facing while the rolling structure rotates. The project ideation therefore identifies a need for a platform that can use legged locomotion on complex terrain and rolling locomotion when a faster or more continuous mode is appropriate.

Rollopod was proposed as a hybrid response to this problem. It uses six articulated legs in walking mode and transforms those same leg assemblies into two side rolling rings in rolling mode. The central body remains suspended between the rings, and the documented design does not form a sphere or attach decorative legs to independent wheels. This architecture preserves a legged configuration for terrain interaction while providing a compact rolling configuration for suitable surfaces. Environmental scanning is an intended capability of the central sensing arrangement; its autonomous performance is not treated as experimentally demonstrated in this document.

## Problem Statement

Current mobile-robot designs must balance several competing requirements:

- Mobility across smooth, uneven, and obstacle-filled terrain.
- Terrain adaptability without excessive mechanical or control complexity.
- Higher travel speed when the surface permits continuous rolling.
- Continuous environmental scanning while the robot is moving.
- Stable placement of sensors and the central payload during locomotion and transformation.
- Reliable coordination of multiple actuators under battery and communication constraints.

A fixed hexapod and a fixed rolling robot each address only part of this problem. Rollopod investigates whether a shared transformable structure can provide both modes in one platform.

## Objectives

- Develop a six-legged robot with a defined walking configuration.
- Develop a rolling configuration formed by transforming the legs into two side rings.
- Maintain a suspended central body during walking, rolling, and transformation.
- Coordinate servo actuation through a distributed ESP32 and PCA9685 architecture.
- Provide wireless command transfer using ESP-NOW.
- Separate high-current actuator power from sensitive logic electronics.
- Define a control architecture for gait execution, rolling control, and transformation.
- Provide a platform for future depth, inertial, and environmental sensing.
- Evaluate the mechanical and control design experimentally as prototype development progresses.

## Novelty

The engineering novelty documented for Rollopod is the integration of a hexapod and a dual-ring rolling mechanism through a shared structural transformation. Three articulated legs on the left side fold inward and connect edge-to-edge to create one rolling ring; the corresponding three legs on the right side form the second ring. The rings are therefore transformed leg assemblies rather than permanent wheels.

The design also combines:

- A central suspended body retained between the two side structures.
- Servo-actuated transformation between walking and rolling states.
- Curved, treaded outer leg profiles intended to form a continuous rolling surface when folded.
- Independent control of the two rolling sides, allowing differential-speed steering in the rolling configuration.
- Distributed electronics placed within a compact mechanical topology.

These features describe the proposed engineering configuration and design direction. They are not presented as a claim of legal priority or as proof of experimentally demonstrated performance.

## Mechanical Design

### Architecture

Rollopod consists of a central body module and two side assemblies. Each side contains three articulated legs, giving six legs in total. The central body houses or supports the control electronics, power-distribution elements, and sensing payload. It remains suspended between the side rolling structures throughout the documented operating states.

The design is an open mechanical prototype architecture. The reference documents describe aluminium structural members, CNC-cut plates, carbon-fibre components, exposed servo housings, brackets, joints, and folding linkages. The central body is a compact enclosed pod for electronics, while the actuated side structures remain mechanically visible.

### Leg Arrangement and Walking Configuration

In walking mode, all six legs are deployed. The legs are arranged as three front-to-rear assemblies on each side of the body. Their articulated joints are driven by servos, allowing the platform to support a tripod gait in which alternating groups of legs provide support while the other group is repositioned. Other gait patterns and terrain-adaptive motion are part of the broader control direction and require further implementation and testing.

### Rolling Configuration

In rolling mode, the three left legs fold inward and align their curved outer profiles edge-to-edge to form the left rolling ring. The three right legs perform the corresponding operation to form the right ring. The two rings provide the rolling contact and remain visible on either side of the suspended central body. No separate permanent wheel is assumed in this configuration.

### Transformation Mechanism

The transformation is servo-actuated. From the walking state, the six leg assemblies fold inward toward their respective side structures until the three members on each side form a continuous rolling surface. From the rolling state, the actuators unfold the assemblies to restore the six-legged support configuration. The design also permits transitional states, including partially folded legs and an asymmetric state in which one side is deployed while the opposite side is folded. These intermediate states are mechanically meaningful for demonstrating the transformation sequence, but their safe autonomous execution remains under development.

### Mechanical Topology

```text
Left:  Leg A + Leg B + Leg C -> fold inward -> edge-to-edge rolling ring
Right: Leg D + Leg E + Leg F -> fold inward -> edge-to-edge rolling ring
                         central suspended body
```

The transformation preserves the dual-ring geometry and keeps the central body visible. The platform is not designed to enclose itself as a sphere.

## Electronics Architecture

The documented electronics use a distributed architecture with separate command, communication, actuator-control, and power functions.

```text
Python GUI / PC
       | USB serial
ESP32 Master bridge
       | ESP-NOW
ESP32 Slave on robot
       | I2C: GPIO21 SDA, GPIO22 SCL
PCA9685 PWM drivers
       | PWM signal
Servo motors and transformation actuators
```

- **ESP32 architecture:** The PC-connected master ESP32 translates serial commands from the Python GUI into wireless packets. The robot-mounted slave ESP32 receives the packets and acts as the on-robot control hub.
- **ESP-NOW:** ESP-NOW provides point-to-point wireless communication between the master and slave. The master is configured with the slave MAC address according to the project setup guide.
- **PCA9685:** The slave communicates over I2C with 16-channel PCA9685 PWM driver boards. Additional boards can be assigned distinct I2C addresses when more servo channels are required.
- **Power distribution:** The documented design separates the logic supply from the high-current servo supplies. A middle control section powers the logic electronics through a regulated supply, while left and right battery sections feed the corresponding servo rails through protection components. Common ground is required for ESP32, PCA9685, and signal-reference continuity.
- **Servo control:** The PCA9685 generates PWM outputs for calibrated servo positions. The software documentation supports tick-based control, angle mapping, per-channel calibration, and synchronized command transmission.
- **Sensors:** The design references an MPU6050 inertial measurement unit for orientation and angular-rate feedback. Depth-camera, LiDAR, camera, and ultrasonic sensing are described as sensing options for terrain assessment, obstacle detection, and environmental scanning; the level of integration and validation is not uniform across the project and is identified as under development where applicable.
- **Raspberry Pi:** The project ideation describes a Raspberry Pi as a higher-level processor for sensor processing, depth measurement, object recognition, wireless operation, and autonomous decision-making. Its role is part of the proposed system architecture and is not treated here as a completed experimental result.

## Software Architecture

The control software is organized around a Python GUI, ESP32 firmware, wireless communication, I2C driver control, and servo calibration.

- **Walking gait:** The mechanical concept identifies a tripod gait as a basis for stable forward walking. Coordinated leg lifting, repositioning, support, and timing are required for implementation.
- **Rolling control:** The rolling configuration uses the two side structures as rolling elements. Differential speed between the left and right sides is intended to provide forward, backward, and directional control without a separate steering mechanism.
- **ESP-NOW communication:** The master bridge forwards serial commands to the robot slave over ESP-NOW. The setup guide documents MAC-address configuration, firmware upload, and communication checks.
- **Servo synchronization:** The slave forwards commands over I2C to PCA9685 drivers, which produce PWM outputs for multiple servos. Calibration data maps requested angles to channel-specific tick ranges.
- **Motion planning:** Higher-level motion planning is intended to combine gait selection, terrain or obstacle information, transformation decisions, and rolling control. Autonomous mode selection and sensor-based path planning remain proposed or under development unless separately validated.

The repository includes firmware examples for master bridging, slave PCA9685 control, ESP-NOW testing, I2C scanning, and MPU6050 work, together with a Python servo-controller GUI. These artifacts document the implementation direction; they do not by themselves establish complete system-level validation.

## Prototype Development

### Completed or documented

- CAD/reference geometry and multiple visual views are available in the project files.
- The mechanical architecture, transformation states, and dual-ring topology are defined.
- The electronics architecture using ESP32, ESP-NOW, I2C, and PCA9685 drivers is documented.
- Battery separation, buck-converter logic supply, servo power rails, protection, and common-ground requirements are documented.
- The servo-control GUI, calibration approach, firmware organization, and ESP-NOW setup procedure are documented.
- Component categories and the intended roles of servos, IMU, batteries, drivers, and higher-level processing are identified.
- The engineering novelty and design description have been documented in the project patent synopsis.

### In progress

- Physical prototype development and mechanical assembly.
- Integration of the transformation mechanism with the control system.
- Servo calibration and coordinated multi-actuator motion.
- Integration and validation of sensing for balance, terrain assessment, and environmental scanning.
- System-level validation of walking, rolling, and transitional states.

### Future work

- Complete autonomous mode selection and terrain-aware motion planning.
- Validate transformation repeatability, stability, and mechanical load paths.
- Measure speed, endurance, turning behavior, payload stability, and terrain performance using a defined test protocol.
- Improve fault handling, emergency stopping, and recovery behavior.

## Methodology

The system uses a staged engineering methodology. First, the mechanical architecture is represented in CAD, including the central body, six articulated legs, side rolling structures, joints, and transformation states. The geometry is checked against the project visual references so that the rolling rings are produced by transformed leg assemblies rather than independent wheels.

The prototype electronics consist of a PC-side Python interface and ESP32 master bridge, an ESP32 slave mounted on the robot, PCA9685 PWM drivers, servo actuators, and distributed battery sections. The master receives serial commands, the slave receives ESP-NOW packets, and the PCA9685 boards generate the servo PWM outputs through I2C commands. Logic power and high-current servo power are distributed separately, with common grounding and protection provisions documented in the wiring references.

The control method uses calibrated servo positions and coordinated motion sequences. In walking mode, a tripod gait is the documented baseline for alternating support and leg repositioning. In rolling mode, the side rolling structures are controlled as a differential-drive pair. Transformation sequences coordinate the leg servos so that the three assemblies on each side fold or unfold as a mechanically consistent group.

Sensor-assisted balance and autonomous environmental scanning are included in the system architecture. The MPU6050 is intended to provide inertial feedback, while depth or other range sensors are proposed for terrain and obstacle information. Where these functions have not been integrated or experimentally validated, they are treated as under development rather than as completed capabilities.

## Current Progress

Based on the project documentation, the current progress is:

- Mechanical and CAD architecture documented, including walking, rolling, and transitional configurations.
- Visual and geometric reference canon established for the central body, six legs, side rings, servo locations, and transformation principle.
- Electronics architecture designed around ESP32 master/slave control, ESP-NOW, I2C, and PCA9685 drivers.
- Distributed battery and power-protection architecture documented.
- Servo-control firmware structure, Python GUI, calibration workflow, and wireless setup instructions available in the repository.
- Engineering novelty and design description documented in `PatentFile.md`.
- Prototype development and system integration ongoing.

No numerical performance results, experimental walking or rolling results, transformation-cycle results, range claims, or test outcomes are asserted here because they are not established by the provided project documents.

## Expected Outcomes

The expected outcomes of the continuing work are:

- A functional prototype capable of controlled walking and rolling demonstrations.
- Repeatable servo-actuated transformation between the two primary configurations.
- Stable central-body and sensor positioning during rolling and transformation.
- A reliable wireless control path between the operator interface and on-robot actuators.
- A validated power-distribution arrangement that limits logic brownouts during servo loading.
- Sensor-assisted terrain assessment and obstacle-aware mode selection, subject to successful integration.
- Experimental measurements that quantify locomotion, power use, stability, and transformation behavior.

These are target outcomes and are separate from the completed design and documentation work listed above.

## Applications

The architecture is relevant to applications that require a choice between terrain adaptability and continuous movement, including:

- Search-and-rescue reconnaissance in cluttered or uneven environments.
- Inspection of industrial areas, structures, tunnels, and confined spaces.
- Exploration of forests, deserts, caves, and other irregular terrain.
- Agricultural monitoring and field inspection.
- Educational and research platforms for legged locomotion, transformation, and sensor integration.
- Planetary or remote-environment exploration studies.

Use in any operational or safety-critical application would require application-specific design, testing, environmental qualification, and risk assessment.

## Future Scope

Future development can focus on completing the physical prototype; integrating and calibrating all actuators; implementing closed-loop transformation; adding validated IMU and depth-sensing feedback; and developing terrain-aware path planning. Additional work includes mechanical load and fatigue analysis, improved rolling traction, battery and thermal management, communication fault handling, emergency-stop behavior, autonomous recovery from unstable states, and a repeatable experimental test protocol.

The platform can also be extended with multiple PCA9685 boards, richer sensor fusion, onboard logging, simulation, and higher-level Raspberry Pi processing once the basic mechanical and control functions are validated.

## Conclusion

Rollopod is a documented engineering design for a transformable hexapod that uses six articulated legs for walking and converts the three legs on each side into dual rolling rings. Its central suspended body, distributed ESP32/PCA9685 control architecture, wireless ESP-NOW command path, and separated power system provide a coherent basis for investigating hybrid locomotion. The mechanical concept, CAD references, electronics architecture, software structure, and prototype-development direction are established in the project documentation. Experimental validation of locomotion, transformation, sensing, autonomy, and performance remains necessary before those capabilities can be claimed as demonstrated.

## References

### Internal Project References

- `README.md`
- `HexapodTheoriticalIdeation.md`
- `PatentFile.md`
- `Connections.md`
- `BatteryConnections.md`
- `ESP_NOW_SETUP_GUIDE.md`
- `QUICK_START.md`
- `VISUAL_REFERENCE.md`
- `AI_VISUAL_CANON.md`

