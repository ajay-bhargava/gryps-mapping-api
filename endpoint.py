import modal
from pydantic import BaseModel
import pickle

# Load credentials from pickle file
with open("credentials.pkl", "rb") as f:
    credentials = pickle.load(f)

# Define the FastAPI Image
asgi_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]==0.115.4",
        "pydantic==2.9.2",
        "starlette==0.41.2",
        "pandas",
        "numpy",
        "boto3",
        "awswrangler"
    )
)

# Define the Modal App
app = modal.App("ContechIMSEndpoint")

# Import necessary modules for the FastAPI application
with asgi_image.imports():
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
    import pandas as pd
    from utilities.utility import (
        create_session_with_credentials,
        create_session_with_env_credentials
    )
    from utilities.IMSHandler import IMSQueryHandler
    import os

# Request Pydantic Data Model for the endpoint
class AddressRequest(BaseModel):
    partial_address: str
    city: str

# Define the Modal Function to run the FastAPI application
@app.function(
    image=asgi_image,
    concurrency_limit=1, 
    allow_concurrent_inputs=500,
    secrets=[modal.Secret.from_dict(credentials)]
)
@modal.asgi_app(label="ContechIMS")
def endpoint():
    # Define the FastAPI application
    web_application = FastAPI(title="Contech Hackathon Real Endpoint")

    # Define the endpoint to get building information
    @web_application.post("/get_building_info")
    async def get_building_info(request: AddressRequest):
        # Define the credentials for the session
        CREDENTIALS = {
            "AccessKeyId": os.environ["AccessKeyId"],
            "SecretAccessKey": os.environ["SecretAccessKey"],
            "Token": os.environ["Token"]
        }

        # First, try to get a session from environment variables.
        session = create_session_with_env_credentials()

        # If that didn't work (credentials are missing), fallback to a known set.
        if session.get_credentials() is None:
            session = create_session_with_credentials(CREDENTIALS)

        # Initialize IMS client
        sql_client = IMSQueryHandler(session=session)

        try:
            # Step 1: Query the building number
            query = f"""
            SELECT DISTINCT has_inferred_building_number 
            FROM gryps_neptune.building 
            WHERE has_address LIKE '%{request.partial_address}%' AND has_city = '{request.city}'
            """
            uri_results = sql_client.query(query=query, database="gryps_neptune")
            building_number = uri_results[0]["has_inferred_building_number"]

            # Step 2: Query details for the building number
            query = f"SELECT DISTINCT bin_num, coa_file_link FROM coa_docs WHERE bin_num = {building_number}"
            results = sql_client.query(query=query, database="dob_bis")
            return pd.DataFrame(results).to_json()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Root Endpoint
    @web_application.get("/")
    def root():
        return HTMLResponse(
            """
            <h1>Contech Hackathon</h1>
            <p>Extracts content from SOP PDF documents and returns answers to queries on that content.</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
            </ul>
            """
        )

    # Return the FastAPI application
    return web_application