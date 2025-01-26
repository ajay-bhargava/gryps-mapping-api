import requests

token_url = "http://169.254.169.254/latest/api/token"
headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}  # Token TTL (6 hours)

# Get the token
token_response = requests.put(token_url, headers=headers)
token_response.raise_for_status()  # Raise an exception for bad status codes
token = token_response.text

# Use the token to get the credentials
url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
headers = {"X-aws-ec2-metadata-token": token}
response = requests.get(url, headers=headers)
role_name = response.text.strip()
response = requests.get(f"{url}{role_name}", headers=headers)
print(response.json())