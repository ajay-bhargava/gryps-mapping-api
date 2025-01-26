# Contech Hackathon API endpoint
The FastAPI web endpoint is located [here](https://ajay-bhargava--contech-hackathon-real.modal.run).

> [!NOTE] 
> The endpoint requires rotating AWS credentials to be passed as a pickle file prior to running the endpoint. 

## Generating pickle credentials

To generate pickle credentials, run this in a [gryps.io](grpys.io) notebook:

```python
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
```

Copy the output and paste it into a python file as a dictionary and save it as `credentials.pkl`.

```python
import pickle

with open("credentials.pkl", "rb") as f:
    credentials = pickle.load(f)
```

## Running the endpoint

To test the endpoint, run the following command:

```bash
modal serve endpoint.py
```

## Deploying the endpoint

To deploy the endpoint, run the following command:

```bash
modal deploy endpoint.py
```
