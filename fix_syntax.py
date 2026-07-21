import os
import glob
import re

for file in glob.glob('src/**/*.py', recursive=True):
    with open(file, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace | None with Optional
    content = re.sub(r'([a-zA-Z_\[\]]+)\s*\|\s*None', r'Optional[\1]', content)
    # Replace list[str] | str with Union[list[str], str]
    content = content.replace('list[str] | str', 'Union[list[str], str]')
    content = content.replace('str | bytes', 'Union[str, bytes]')
    
    if content != original_content:
        # Ensure imports
        if 'from typing import' in content:
            if 'Optional' not in content:
                content = content.replace('from typing import ', 'from typing import Optional, ')
            if 'Union' not in content:
                content = content.replace('from typing import ', 'from typing import Union, ')
        else:
            content = 'from typing import Optional, Union\n' + content
        
        with open(file, 'w') as f:
            f.write(content)
        print(f"Fixed {file}")
