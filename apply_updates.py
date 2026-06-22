with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

# Add Ring and Leg description
readme = readme.replace(
    "- Six legs total.\n",
    "- Six legs total.\n\n### Ring Structure & Leg Distribution\nThe rolling rings are structural transformation frames rather than conventional wheels. Each ring acts as a rolling surface, a structural support frame, a mounting structure for three articulated legs, and a housing for transformation linkages.\n\nEach rolling ring carries three major articulated leg assemblies. The front, middle and rear legs are permanently attached to the ring structure. The middle leg is larger and occupies the central region of the ring. The legs fold inward into the ring volume during rolling transformation. The rings remain mechanically visible in both walking and rolling modes.\n"
)

# Add Transformation States
readme = readme.replace(
    "- No spherical enclosure is formed.\n",
    "- No spherical enclosure is formed.\n\n### Transformation States\nRollopod can exist in:\n\n1. **Walking State**\n   - All six legs deployed.\n\n2. **Rolling State**\n   - Both side rings closed.\n\n3. **Transitional State**\n   - One or more legs partially folded.\n   - One ring may be deployed while the opposite ring remains closed.\n   - Intermediate configurations are mechanically valid and visually important.\n"
)

# Add Visual Appearance
readme = readme.replace(
    "The robot is visually characterized by:\n- Two large side rolling rings.\n- Central rectangular body.\n- Open mechanical architecture.\n- Exposed servo actuators.\n- Aluminium structural members.\n- Visible folding joints.\n- Six articulated legs.\n",
    "The robot is visually characterized by:\n- Two large side rolling rings.\n- Central rectangular body.\n- Open mechanical architecture.\n- Exposed servo motors, brackets, and joints.\n- Aluminium structural members and CNC-cut plates.\n- Carbon-fibre components.\n- Visible folding mechanical linkages.\n- Six articulated legs.\n\n**Visual Appearance**\nThe robot should resemble a practical engineering prototype with functional engineering aesthetics. The robot should not resemble a consumer product, toy, or futuristic science-fiction machine.\n"
)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)

# Update HexapodTheoriticalIdeation.md
with open('HexapodTheoriticalIdeation.md', 'r', encoding='utf-8') as f:
    hexapod = f.read()

hexapod = hexapod.replace('outer disks', 'structural rolling rings')
hexapod = hexapod.replace('outer disk', 'structural rolling ring')
hexapod = hexapod.replace('disk rotation', 'structural rolling ring rotation')

# Add transformation states
hexapod = hexapod.replace(
    "- No spherical enclosure is formed.\n",
    "- No spherical enclosure is formed.\n\n### Transformation States\nRollopod can exist in:\n\n1. **Walking State**\n   - All six legs deployed.\n\n2. **Rolling State**\n   - Both side rings closed.\n\n3. **Transitional State**\n   - One or more legs partially folded.\n   - One ring may be deployed while the opposite ring remains closed.\n   - Intermediate configurations are mechanically valid and visually important.\n"
)

with open('HexapodTheoriticalIdeation.md', 'w', encoding='utf-8') as f:
    f.write(hexapod)

# Update PatentFile.md
with open('PatentFile.md', 'r', encoding='utf-8') as f:
    patent = f.read()

patent = patent.replace(
    "- No spherical enclosure is formed.\n",
    "- No spherical enclosure is formed.\n\n### Transformation States\nRollopod can exist in:\n\n1. **Walking State**\n   - All six legs deployed.\n\n2. **Rolling State**\n   - Both side rings closed.\n\n3. **Transitional State**\n   - One or more legs partially folded.\n   - One ring may be deployed while the opposite ring remains closed.\n   - Intermediate configurations are mechanically valid and visually important.\n"
)

with open('PatentFile.md', 'w', encoding='utf-8') as f:
    f.write(patent)
