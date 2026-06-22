import os

curvature_text = "\n\n**Leg Curvature for Rolling:**\nCrucially, each individual leg features an outer curvature with thick treads. When the three legs on a side fold inward, their curved outer profiles align perfectly edge-to-edge to form a continuous circular rolling surface."

def update_file(filename):
    if not os.path.exists(filename):
        return
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    if "The wheels are created by transformed legs." in text:
        text = text.replace(
            "The wheels are created by transformed legs.",
            "The wheels are created by transformed legs." + curvature_text
        )
    elif "The rings are created from the transformed leg assemblies." in text:
        text = text.replace(
            "The rings are created from the transformed leg assemblies.",
            "The rings are created from the transformed leg assemblies." + curvature_text
        )

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

update_file('AI_VISUAL_CANON.md')
update_file('VISUAL_REFERENCE.md')
update_file('README.md')
update_file('PatentFile.md')
update_file('HexapodTheoriticalIdeation.md')
