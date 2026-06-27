#!/usr/bin/env python3
"""Update all profile READMEs with new dark editorial images."""
import re

agents = {
    "senter": "https://v3b.fal.media/files/b/0a9feb37/5ny2dJrSH1UApTs1Y8zcK_64Joy9aY.png",
    "chizul": "https://v3b.fal.media/files/b/0a9feb37/bDNP7fYDTh9KZcnEdCeAK_CQwqcvut.png",
    "klerik": "https://v3b.fal.media/files/b/0a9feb38/-UdPioFQBtzT95KBbivZb_cuzRg3fl.png",
    "anser": "https://v3b.fal.media/files/b/0a9feb38/00R6aqWkVrmNhK3W5f1dZ_YhUFUbZk.png",
    "kashik": "https://v3b.fal.media/files/b/0a9feb38/XDEb5Ycll2dlE3Oj2l85L_i0ZKZ9JM.png",
    "crow": "https://v3b.fal.media/files/b/0a9feb3a/T1XI1xqd5llXYoH_6S81h_MBMJ3Dmq.png",
    "frieza": "https://v3b.fal.media/files/b/0a9feb43/wDnlH0GEWEv2s3ShJU-Wj_ghyUyiNT.png",
    "llmc": "https://v3b.fal.media/files/b/0a9feb44/uq1RWKdJbCz5UNT2RjnYi_HHb3f7So.png",
}

for name, url in agents.items():
    path = f"profiles/{name}/README.md"
    with open(path) as f:
        content = f.read()
    
    # Replace the image URL (matches any fal.media URL in the first image)
    content = re.sub(
        r'!\[.*?\]\(https://v3b\.fal\.media/.*?\.png\)',
        f'![{name.title()}]({url})',
        content,
        count=1
    )
    
    with open(path, 'w') as f:
        f.write(content)
    print(f"{name}: ✓")