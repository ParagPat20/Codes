# Official Rollopod Visual Reference

This document serves as the authoritative visual description of Rollopod.

## Geometry

Rollopod consists of:

- One central rectangular body.
- Three legs on the left side that transform into a wheel.
- Three legs on the right side that transform into a wheel.
- Six legs total.

### Reference Geometry

The official Rollopod appearance consists of:

- Three legs on each side transform into a wheel structure.
- Central suspended rectangular body.
- Open-frame architecture.
- Wheel diameter significantly larger than body height.
- Exposed mechanical joints.
- Exposed servo housings.
- Thick rolling tread sections mounted on the legs.
- Industrial engineering appearance.

The overall appearance should resemble a transformable field robot rather than a consumer robot.

## Critical Geometry Constraints
IMPORTANT:

The side rolling rings are NOT permanent wheels.
The wheel structure is formed by the transformation of the three legs on each side.

**Walking Mode Appearance:**
The robot should visually resemble:
- traditional hexapod
- six visible fully deployed legs
- central suspended body
- no complete circular wheel exists

The wheel structures should not visually dominate. At first glance it should be identified as a hexapod.

**Rolling Mode Appearance:**
The robot should visually resemble:
- two large wheels
- central suspended body

The six legs are folded and integrated into the wheel structure. No separate walking legs remain visible.
- Three left legs fold together to create one continuous rolling ring.
- Three right legs fold together to create one continuous rolling ring.
- The rings are created from the transformed leg assemblies.

The robot must never appear as:
- A wheel robot with legs attached.
- A wheel with decorative legs.
- A wheel carrying a hexapod.
Instead: The legs themselves become the wheel.

## Mechanical Topology

LEFT SIDE
Leg A
Leg B
Leg C
↓
Fold inward
↓
Connect edge-to-edge
↓
Create left wheel

RIGHT SIDE
Leg D
Leg E
Leg F
↓
Fold inward
↓
Connect edge-to-edge
↓
Create right wheel

The wheels do not exist independently. The wheels are created by transformed legs.

**Leg Curvature for Rolling:**
Crucially, each individual leg features an outer curvature with thick treads. When the three legs on a side fold inward, their curved outer profiles align perfectly edge-to-edge to form a continuous circular rolling surface.

## Transformation States

Rollopod can exist in:

1. **Walking State**
   - All six legs deployed.
   - No complete circular wheel exists.
   - Body suspended between leg bases.

2. **Rolling State**
   - Both sides folded into wheels.
   - Legs fold together to form the wheels.
   - Robot rolls on two wheels made of legs.
   - Body remains visible.

3. **Transitional State**
   - One or more legs partially folded.
   - One side may be deployed while the opposite side remains closed into a wheel.
   - Intermediate configurations are mechanically valid and visually important.

## Appearance

The robot should resemble a practical engineering prototype.
Features include:

- Exposed servo motors.
- Exposed brackets.
- Exposed joints.
- Mechanical linkages.
- CNC-cut plates.
- Aluminium members.
- Carbon-fibre components.
- Functional engineering aesthetics.

The robot should not resemble a consumer product, toy, or futuristic science-fiction machine.

## Negative Constraints
Do NOT generate:

- Sphere robots.
- Ball robots.
- Spider spheres.
- Futuristic sci-fi designs.
- Humanoid robots.
- Fully enclosed robots.
- Festo BionicWheelBot style geometry
- Wheels with attached legs
- Wheel-legged hybrids
- Circular wheel frames carrying legs
- Permanent wheels
- Military robot aesthetics
- Tank-like robots

## Universal Anchor Rule
Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body where three legs on each side transform into a wheel.
