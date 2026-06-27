import os
import xml.etree.ElementTree as ET

params_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'params.xml')
tree = ET.parse(params_file)
root = tree.getroot()

params = {}
for param in root.findall('param'):
    name = param.get('name')
    param_type = param.get('type')
    value = param.text
    
    # Convert to appropriate type
    if param_type == 'int':
        params[name] = int(value)
    elif param_type == 'bool':
        params[name] = value.lower() == 'true'
    else:  # string
        params[name] = value
        
if __name__ == "__main__":
    print(params)