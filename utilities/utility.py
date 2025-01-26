import boto3
import hashlib
from botocore.credentials import Credentials
import os

def get_account_hash_from_account_id(account_id: str):
    """Convert account ID to a hashed string."""
    return hashlib.md5(account_id.encode("utf-8")).hexdigest()

def create_session_with_credentials(credentials: dict, region: str = "us-east-1"):
    """
    Create a boto3 Session using explicit credentials.
    """
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials.get('Token'),
        region_name=region
    )

def create_session_with_env_credentials(region: str = "us-east-1"):
    """
    Create a boto3 Session using environment variables.
    This will return a session with no credentials if they are not found.
    """
    return boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=region
    )

def get_aws_auth_token(session):
    """
    Extract the frozen credentials and other details needed for SigV4 signing.
    """
    creds = session.get_credentials()
    if not creds:
        # No credentials found in session
        raise ValueError("No valid AWS credentials found in session. "
                         "Make sure environment variables are set or fallback credentials are provided.")
    credentials = creds.get_frozen_credentials()
    region = session.region_name or "us-east-1"
    service_name = "execute-api"  # For Neptune's HTTP endpoint
    return {
        "credentials": Credentials(
            credentials.access_key,
            credentials.secret_key,
            credentials.token
        ),
        "service_name": service_name,
        "region": region
    }

def get_account_hash_from_session(session):
    """
    Retrieve the AWS account ID via STS and compute its hash.
    """
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    return get_account_hash_from_account_id(account_id)

def get_intelligence_base_url_from_session(session):
    """
    Build the base URL for Neptune's SPARQL endpoint.
    """
    account_hash = get_account_hash_from_session(session)
    # Example: https://intelligence.{account_hash}.gryps.io
    return f"https://intelligence.{account_hash}.gryps.io"
