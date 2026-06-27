#!/usr/bin/env python3
"""Fix Eikon fields in all profile READMEs."""
import re

agents = ['chizul', 'klerik', 'anser', 'kashik', 'crow', 'frieza', 'llmc']
for name in agents:
    path = f'profiles/{name}/README.md'
    with open(path) as f:
        content = f.read()
    
    # Fix Eikon field — the previous run removed the filename part
    content = re.sub(
        r'\*\*Eikon\*\*\s+\|\s+.*$',
        f'**Eikon**     | `{name}.eikon` (6 states: idle, listening, thinking, speaking, working, error)                                     |',
        content,
        flags=re.MULTILINE
    )
    
    with open(path, 'w') as f:
        f.write(content)
    print(f'{name}: fixed')
