# Rollopod - A Transforming Hexapod Robot with Dual-Mode Walking and Rolling Locomotion

## Theme

**Category:** Senior Category  
**Theme:** Robotics & Aerial Robotics

## Project Status

| Component | Status |
|-----------|--------|
| Concept Development | ✅ Completed |
| CAD Design | ✅ Completed |
| Mechanical Architecture | ✅ Completed |
| Electronics Architecture | ✅ Completed |
| Control Architecture | ✅ Completed |
| Firmware Development | 🟡 In Progress |
| Prototype Assembly | 🟡 In Progress |
| Walking Validation | 🔜 Planned |
| Rolling Validation | 🔜 Planned |
| Transformation Testing | 🔜 Planned |

## Innovation Highlights

| Innovation | Description |
|------------|-------------|
| Hybrid Locomotion | Walking and rolling in one platform |
| Transformable Legs | Three legs on each side form a rolling ring |
| Suspended Central Body | Central payload remains between the side structures |
| Distributed Control | Microcontrollers, wireless communication, and PWM-based actuation |
| Modular Electronics | Expandable servo-control architecture |

## Quick Specifications

| Specification | Documented Configuration |
|---------------|--------------------------|
| Robot Type | Transformable dual-ring hexapod |
| Locomotion | Six-legged walking and two-ring rolling |
| Transformation | Three legs on each side fold into a rolling ring |
| Controller | Master/slave microcontroller architecture with PWM drivers |
| Communication | Point-to-point wireless communication |
| Power | Distributed battery system with separate logic and servo-load sections |
| Current Status | Mechanical and control architectures documented; firmware and prototype assembly in progress |

---

## Abstract

For the Senior Category theme of Robotics & Aerial Robotics, Rollopod investigates a transformable mobile robot that combines the terrain adaptability of a hexapod with the continuous motion of a rolling platform. Conventional hexapods distribute support across six legs but require coordinated articulated gait control, while fixed wheeled robots are less adaptable to obstacles and discontinuous terrain. Rollopod addresses this design problem by folding the three legs on each side into a rolling ring, allowing the same structural assemblies to support walking and rolling while a central body remains suspended between the two rings.

The method combines CAD-based mechanical design, servo-actuated transformation, distributed microcontroller control, wireless communication, PWM actuation, separated power distribution, and sensor-oriented architecture. The documented results are a defined mechanical concept, CAD reference geometry, electronics architecture, control architecture, and an active firmware and prototype-assembly effort. This distinction separates design completion from prototype performance: effectiveness will be judged through repeatable engineering tests. Walking, rolling, transformation, autonomous terrain adaptation, and environmental-scanning performance have not been reported as validated results. The engineering conclusion is that Rollopod provides a coherent platform for investigating hybrid locomotion without using independent permanent wheels, while its operational performance must be established through subsequent testing.

## Introduction

### Limitations of Conventional Hexapods

Hexapods provide multiple ground contacts and can maintain support over uneven surfaces. However, their motion depends on repeated lifting and placement of several articulated legs. This creates challenges in gait coordination, actuator loading, power consumption, and travel speed on smooth terrain.

### Limitations of Wheeled Robots

Wheeled robots can provide efficient continuous motion on prepared or relatively smooth surfaces. Their fixed support geometry is less suitable for stepping over obstacles, crossing discontinuities, or changing the body-to-ground relationship. Rotation of the wheel structure can also complicate stable placement of a sensing payload.

### Motivation Behind Rollopod

Rollopod combines the two mobility strategies in one reconfigurable structure. It uses six articulated legs in walking mode and transforms those assemblies into two side rolling rings in rolling mode, with the central body suspended between them. Environmental scanning is included as a sensing objective; autonomous scanning performance is not reported as validated.

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
- Coordinate servo actuation through a distributed microcontroller and PWM-driver architecture.
- Provide wireless command transfer using a point-to-point wireless link.
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

---

## Mechanical Design

### Architecture

Rollopod consists of a central body module and two side assemblies. Each side contains three articulated legs, giving six legs in total. The central body houses or supports the control electronics, power-distribution elements, and sensing payload. It remains suspended between the side rolling structures throughout the documented operating states.

The design is an open mechanical prototype architecture. The reference documents describe aluminium structural members, CNC-cut plates, carbon-fibre components, exposed servo housings, brackets, joints, and folding linkages. The central body is a compact enclosed pod for electronics, while the actuated side structures remain mechanically visible.

> **Figure 1. Overall CAD Assembly.** Insert the selected assembly view or orthographic CAD reference here.

### Leg Arrangement and Walking Configuration

In walking mode, all six legs are deployed. The legs are arranged as three front-to-rear assemblies on each side of the body. Their articulated joints are driven by servos, allowing the platform to support a tripod gait in which alternating groups of legs provide support while the other group is repositioned. Other gait patterns and terrain-adaptive motion are part of the broader control direction and require further implementation and testing.

> **Figure 2. Walking Configuration.** Insert the relevant CAD or reference view here.

### Rolling Configuration

In rolling mode, the three left legs fold inward and align their curved outer profiles edge-to-edge to form the left rolling ring. The three right legs perform the corresponding operation to form the right ring. The two rings provide the rolling contact and remain visible on either side of the suspended central body. No separate permanent wheel is assumed in this configuration.

> **Figure 3. Rolling Configuration.** Insert the relevant CAD or reference view here.

### Transformation Mechanism

The transformation is servo-actuated. From the walking state, the six leg assemblies fold inward toward their respective side structures until the three members on each side form a continuous rolling surface. From the rolling state, the actuators unfold the assemblies to restore the six-legged support configuration. The design also permits transitional states, including partially folded legs and an asymmetric state in which one side is deployed while the opposite side is folded. These intermediate states are mechanically meaningful for demonstrating the transformation sequence, but their safe autonomous execution remains under development.

### Mechanical Topology

```text
Left:  Leg A + Leg B + Leg C -> fold inward -> edge-to-edge rolling ring
Right: Leg D + Leg E + Leg F -> fold inward -> edge-to-edge rolling ring
                         central suspended body
```

The transformation preserves the dual-ring geometry and keeps the central body visible. The platform is not designed to enclose itself as a sphere.

> **Figure 4. Transformation Sequence.** Insert a sequence showing walking, transitional, and rolling states here.


## Electronics Architecture

The robot uses a master/slave microcontroller architecture with a point-to-point wireless link and multi-channel PWM controllers for distributed servo actuation. A PC-side interface sends commands through a master controller, while a robot-mounted controller coordinates the actuator drivers. Separate logic and high-current servo power sections support electrical isolation, protection, and common signal reference. The architecture can be expanded with additional PWM drivers and sensors as the prototype develops.

```text
PC GUI
   |
Master Microcontroller
   |
Wireless Link
   |
Robot Microcontroller
   |
PWM Drivers
   |
Servo Motors and Transformation Actuators
```

The electronics are divided into command and communication, actuator control, power distribution, and sensing functions. The PWM drivers provide multi-channel signal generation for the servo network. The documented battery architecture separates the central logic supply from the left and right servo loads through regulated and protected power sections. An inertial measurement unit and higher-level depth or range sensing are included as sensing elements for balance, terrain assessment, obstacle detection, and environmental scanning. Higher-level processor operation is an architectural option rather than a completed experimental capability.

> **Figure 5. Electronics Architecture.** Command, wireless communication, distributed PWM control, actuation, and power-distribution paths.

## Software Architecture

The software architecture coordinates locomotion, transformation, wireless commands, and servo timing at multiple control levels. The documented control direction is summarized below.

- **Walking gait control:** A tripod gait is the documented baseline. Alternating support groups coordinate leg lifting, repositioning, and weight support while maintaining body stability.
- **Rolling control:** The two side rolling structures are controlled as a differential pair. Relative actuation is intended to provide forward, backward, and directional motion without a separate steering assembly.
- **Transformation control:** Servo sequences coordinate the three leg assemblies on each side during folding and unfolding. Interlocks and state handling are required to manage walking, rolling, and transitional configurations safely.
- **Motion planning:** Higher-level planning is intended to combine gait selection, terrain information, obstacle response, transformation decisions, and rolling control. Autonomous mode selection remains proposed or under development.
- **Wireless communication:** Operator commands are transferred from the external interface to the robot controller through the point-to-point wireless link.
- **Servo synchronization:** The robot controller distributes coordinated position commands through the PWM drivers so that multiple legs and transformation joints move as a group.

The software architecture is documented and partially implemented. Complete system-level validation of walking, rolling, transformation, and autonomous operation is not yet reported.

> **Figure 6. Software Architecture.** Locomotion, transformation, wireless communication, synchronization, and motion-planning layers.

## Methodology

The system uses a staged engineering methodology. First, the mechanical architecture is represented in CAD, including the central body, six articulated legs, side rolling structures, joints, and transformation states. The geometry is checked against the project visual references so that the rolling rings are produced by transformed leg assemblies rather than independent wheels.

The prototype electronics consist of a PC-side control interface and master bridge, a robot-mounted slave microcontroller, multi-channel PWM drivers, servo actuators, and distributed battery sections. The master receives external commands, the slave receives wireless packets, and the PWM driver boards generate servo-control signals through a digital control bus. Logic power and high-current servo power are distributed separately, with common grounding and protection provisions documented in the wiring references.

The control method uses calibrated servo positions and coordinated motion sequences. In walking mode, a tripod gait is the documented baseline for alternating support and leg repositioning. In rolling mode, the side rolling structures are controlled as a differential-drive pair. Transformation sequences coordinate the leg servos so that the three assemblies on each side fold or unfold as a mechanically consistent group.

Sensor-assisted balance and autonomous environmental scanning are included in the system architecture. An inertial measurement unit is intended to provide orientation feedback, while depth or other range sensors are included for terrain and obstacle information. Where these functions have not been integrated or experimentally validated, they are treated as under development rather than as completed capabilities.

## Prototype Development

### Completed or documented

- CAD/reference geometry and multiple visual views are available in the project files.
- The mechanical architecture, transformation states, and dual-ring topology are defined.
- The electronics architecture using master/slave microcontrollers, wireless communication, digital control buses, and PWM drivers is documented.
- Battery separation, buck-converter logic supply, servo power rails, protection, and common-ground requirements are documented.
- The servo-control interface, calibration approach, firmware organization, and wireless-control procedure are documented.
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

## Current Progress

Based on the project documentation, the current progress is:

- Mechanical and CAD architecture documented, including walking, rolling, and transitional configurations.
- Visual and geometric reference canon established for the central body, six legs, side rings, servo locations, and transformation principle.
- Electronics architecture designed around master/slave microcontroller control, wireless communication, digital control buses, and PWM drivers.
- Distributed battery and power-protection architecture documented.
- Servo-control firmware structure, Python GUI, and wireless control documentation are available in the project files.
- Engineering novelty and design description documented in `PatentFile.md`.
- Prototype development and system integration ongoing.

No numerical performance results, experimental walking or rolling results, transformation-cycle results, range claims, or test outcomes are asserted here because they are not established by the provided project documents.

## Results

The documented results are reported by development maturity rather than as unsupported performance claims.

| Area | Documented Result | Maturity |
|------|-------------------|----------|
| Mechanical design | CAD/reference geometry, dual-ring topology, and transformation states defined | Completed |
| Electronics and power | Microcontroller, wireless, PWM-driver, servo-control, and distributed battery architecture documented | Completed |
| Control architecture | Walking-gait, rolling, transformation, synchronization, and motion-planning structure defined | Completed |
| Firmware and assembly | Firmware organization and physical prototype development are progressing | In Progress |
| Locomotion and transformation | Walking, rolling, and transformation performance measurements are not reported | Future Work |

## Expected Prototype Capabilities

The expected outcomes of the continuing work are:

- A functional prototype capable of controlled walking and rolling demonstrations.
- Repeatable servo-actuated transformation between the two primary configurations.
- Stable central-body and sensor positioning during rolling and transformation.
- A reliable wireless control path between the operator interface and on-robot actuators.
- A validated power-distribution arrangement that limits logic brownouts during servo loading.
- Sensor-assisted terrain assessment and obstacle-aware mode selection, subject to successful integration.
- Experimental measurements that quantify locomotion, power use, stability, and transformation behavior.

These are target capabilities and are separate from the completed design and documentation work listed above.

## Applications

The architecture is relevant to applications that require a choice between terrain adaptability and continuous movement, including:

- Search-and-rescue reconnaissance in cluttered or uneven environments.
- Inspection of industrial areas, structures, tunnels, and confined spaces.
- Exploration of forests, deserts, caves, and other irregular terrain.
- Agricultural monitoring and field inspection.
- Educational and research platforms for legged locomotion, transformation, and sensor integration.
- Planetary or remote-environment exploration studies.

Use in any operational or safety-critical application would require application-specific design, testing, environmental qualification, and risk assessment.

## Design Challenges

The following remain important engineering challenges in the development of the platform:

- **Transformation mechanism:** Aligning three articulated leg assemblies into a continuous rolling ring while preserving clearance and reliable engagement.
- **Structural rigidity:** Maintaining stiffness in the open mechanical frame under legged support and rolling loads.
- **Weight distribution:** Balancing the central body, batteries, actuators, and payload around the two side structures.
- **Servo synchronization:** Coordinating multiple joints during gait execution and transformation without conflicting motion commands.
- **Power management:** Supplying high-current servo loads while protecting the logic and communication electronics from voltage disturbance.
- **Stability:** Maintaining support, body orientation, and sensor usability during walking, rolling, and transitional states.
- **Autonomous mode switching:** Determining when a change between walking and rolling is appropriate and executing it safely from sensor information.

## Future Scope

Future development can focus on completing the physical prototype; integrating and calibrating all actuators; implementing closed-loop transformation; adding validated IMU and depth-sensing feedback; and developing terrain-aware path planning. Additional work includes mechanical load and fatigue analysis, improved rolling traction, battery and thermal management, communication fault handling, emergency-stop behavior, autonomous recovery from unstable states, and a repeatable experimental test protocol.

The platform can also be extended with multiple PWM-driver boards, richer sensor fusion, onboard logging, simulation, and higher-level processor operation once the basic mechanical and control functions are validated.

## Conclusion

Rollopod is an engineering design for a transformable hexapod that uses six articulated legs for walking and converts the three legs on each side into dual rolling rings. Its suspended central body, distributed microcontroller/PWM-driver control architecture, wireless command path, and separated power system provide a coherent basis for hybrid-locomotion research. The mechanical, electronic, and software architectures are documented, while prototype assembly and system validation continue.

The modular architecture developed for Rollopod is intended to serve as one of the foundational subsystems of the future Modular Robotic Field Assistant (MRFA), an integrated modular robotics research platform.

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

### External References

1. T.-T. Lee, C.-M. Liao, and T.-K. Chen, “On the Stability Properties of Hexapod Tripod Gait,” *IEEE Journal on Robotics and Automation*, vol. 4, no. 4, pp. 427–434, 1988. doi: [10.1109/56.808](https://doi.org/10.1109/56.808).
2. F. Zhang, S. Zhang, Q. Wang, Y. Yang, and B. Jin, “Straight Gait Research of a Small Electric Hexapod Robot,” *Applied Sciences*, vol. 11, no. 8, 3714, 2021. doi: [10.3390/app11083714](https://doi.org/10.3390/app11083714).
3. I. Kim, W. Jeon, and H. Yang, “Design of a Transformable Mobile Robot for Enhancing Mobility,” *International Journal of Advanced Robotic Systems*, 2017. doi: [10.1177/1729881416687135](https://doi.org/10.1177/1729881416687135).
4. Espressif Systems, “Wireless Communication Framework Programming Guide,” official documentation. Available at: [official wireless communication guide](https://docs.espressif.com/projects/esp-now/en/latest/).
5. NXP Semiconductors, “16-Channel, 12-Bit PWM Controller,” product datasheet. Available at: [official PWM controller datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf).
