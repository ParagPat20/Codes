import os

new_anchor = "Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body where three legs on each side transform into a wheel."

def update_file(filename, is_readme=False):
    if not os.path.exists(filename):
        return
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    # Anchor replacement
    text = text.replace("Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body and two side rolling ring assemblies.", new_anchor)

    # Specific replacements
    text = text.replace("- Two large circular side rolling rings.", "- Three legs on each side transform into a wheel.")
    text = text.replace("- Two large side rolling rings.", "- Three legs on each side transform into a wheel.")
    text = text.replace("Two large circular side rolling rings.", "Three legs on each side transform into a wheel.")
    text = text.replace("two large side rolling rings.", "three legs on each side transform into a wheel.")
    text = text.replace("- Two side rolling ring assemblies.", "- Three legs on each side transform into a wheel.")
    
    # Fix the Ring Structure & Leg Distribution that was inserted previously
    text = text.replace("Each rolling ring carries three major articulated leg assemblies. The front, middle and rear legs are permanently attached to the ring structure. The middle leg is larger and occupies the central region of the ring. The legs fold inward into the ring volume during rolling transformation. The rings remain mechanically visible in both walking and rolling modes.", 
    "Each wheel structure carries three major articulated leg assemblies. The legs themselves become the wheel. The front, middle and rear legs connect edge-to-edge when folded.")
    
    text = text.replace("The rolling rings are structural transformation frames rather than conventional wheels. Each ring acts as a rolling surface, a structural support frame, a mounting structure for three articulated legs, and a housing for transformation linkages.",
    "The side rolling structures are NOT permanent wheels. The wheel structure is formed by the transformation of the three legs on each side.")
    
    # Add new sections to README
    if is_readme:
        new_sections = """## AUTHORITATIVE GEOMETRY

The uploaded CAD model is the primary source of truth. Text descriptions are secondary.
All generated images must follow:
- wheel diameter
- body proportions
- leg proportions
- servo locations
- transformation sequence
exactly as shown in CAD. Without a visual anchor, image models invent geometry.

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

"""
        text = text.replace("## Physical Architecture\n", new_sections + "## Physical Architecture\n")
        
        # update AI Image Generation Reference
        text = text.replace("- Spherical robots.", "- Spherical robots.\n- Festo BionicWheelBot style geometry\n- Wheels with attached legs\n- Spider robots\n- Wheel-legged hybrids\n- Circular wheel frames carrying legs\n- Permanent wheels\n- Sci-fi mechs\n- Military robot aesthetics\n- Tank-like robots\n- Ball robots")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

update_file('README.md', is_readme=True)
update_file('PatentFile.md')
update_file('HexapodTheoriticalIdeation.md')
