import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Remove nginx service block
content = re.sub(r'  nginx:.*?(?=  \w|\Z)', '', content, flags=re.DOTALL)
content = content.replace('depends_on:\n    - nginx\n', '')

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print('✓ Removed nginx service')
