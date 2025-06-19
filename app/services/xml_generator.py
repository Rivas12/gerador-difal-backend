def generate_xml(data):
    import xml.etree.ElementTree as ET

    root = ET.Element("GNRE")
    
    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)

    return ET.tostring(root, encoding='unicode')