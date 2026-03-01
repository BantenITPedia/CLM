with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Change port 8000 to 8002 for CLM nginx (WebPCI uses 8000)
content = content.replace(\ - 8000:8000 \, \- 8002:8000 \)

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print('Updated ports: 8002:8000 and 8001:8001')
