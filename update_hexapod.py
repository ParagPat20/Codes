with open('HexapodTheoriticalIdeation.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('compact spherical form', 'compact dual-ring rolling configuration')
text = text.replace('all the legs are folded and retracted', 'the legs fold inward toward their respective left and right rolling rings')
text = text.replace('rolling sphere', 'dual-ring rolling structure')
text = text.replace('spherical form for rolling', 'side-ring rolling configuration')
text = text.replace('hexapod transforms into a sphere', 'hexapod transforms into a dual-wheel rolling robot')

new_sections = """

Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body and two side rolling ring assemblies.

# Physical Architecture

Rollopod consists of:

- One central body module.
- Two large circular side rolling rings.
- Three articulated legs mounted on the left ring.
- Three articulated legs mounted on the right ring.
- Six legs total.

The rolling rings remain visible in all operating modes.

The central body remains suspended between the two rolling rings.

The robot never transforms into a sphere.

# Transformation Mechanism

Walking Mode:

- Six legs fully extended.
- Three legs on each side.
- Robot operates as a hexapod.

Rolling Mode:

- Left legs fold into left rolling ring.
- Right legs fold into right rolling ring.
- Folded legs become part of the rolling structure.
- Two rolling rings provide locomotion.

During transformation:

- Central body remains visible.
- Central body remains suspended.
- No spherical enclosure is formed.
"""

text = text.replace('A Fastest Evolution of Hexapod\n\n', 'A Fastest Evolution of Hexapod\n\n' + new_sections + '\n')

with open('HexapodTheoriticalIdeation.md', 'w', encoding='utf-8') as f:
    f.write(text)
