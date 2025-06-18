def generate_xml(data):
    """
    Generate an XML document from the provided data.

    Args:
        data (dict): A dictionary containing the data to be converted to XML.

    Returns:
        str: A string representation of the XML document.
    """
    import xml.etree.ElementTree as ET

    root = ET.Element("GNRE")
    
    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)

    return ET.tostring(root, encoding='unicode')