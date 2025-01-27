import modal
from pydantic import BaseModel
import json
import dotenv

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
        "awswrangler",
        "python-dotenv"
    )
)

# Define the Modal App
app = modal.App("contech-ims-v2")

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
    from fastapi.responses import JSONResponse
# Request Pydantic Data Model for the endpoint
class AddressRequest(BaseModel):
    partial_address: str
    city: str

class BinRequest(BaseModel):
    bin_number: str

# Define the Modal Function to run the FastAPI application
@app.function(
    image=asgi_image,
    concurrency_limit=1, 
    allow_concurrent_inputs=500,
    secrets=[modal.Secret.from_dotenv()]
)
@modal.asgi_app(label="contech-ims-v2")
def endpoint():
    # Define the FastAPI application
    web_application = FastAPI(title="Contech IMS V2.0")
    # Define the credentials for the session
    CREDENTIALS = {
        "AccessKeyId": os.environ["AWS_ACCESS_KEY_ID"],
        "SecretAccessKey": os.environ["AWS_SECRET_ACCESS_KEY"],
        "Token": os.environ["AWS_SESSION_TOKEN"]
    }


    # First, try to get a session from environment variables.
    session = create_session_with_env_credentials()

    # If that didn't work (credentials are missing), fallback to a known set.
    if session.get_credentials() is None:
        session = create_session_with_credentials(CREDENTIALS)

    # Initialize IMS client
    sql_client = IMSQueryHandler(session=session)
    # Define the endpoint to get building information    
    @web_application.get("/get_buildings")
    async def get_building_location():
        try:
            query = f"""
            SELECT has_address, has_city, has_number FROM gryps_neptune.building
            """
            results = pd.DataFrame(sql_client.query(query=query, database="gryps_neptune"))
            return JSONResponse(content=results.to_dict(orient='records'))

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @web_application.post("/coa_by_bin")
    async def coa_by_bin(request: BinRequest):
        try:
            query = f"""
            SELECT bin_num, coa_number, coa_file_link FROM coa_docs WHERE bin_num = {request.bin_number}
            """
            returned = pd.DataFrame(sql_client.query(query=query, database="dob_bis"))
            
            
            # Convert query results to COA record format and return as JSON
            coa_data = {
                "bin_num": request.bin_number,
                "coa_records": [
                    {
                        "coa_number": row["coa_number"],
                        "coa_file_link": row["coa_file_link"]
                    }
                    for _, row in returned.iterrows()
                ]
            }
            
            return JSONResponse(content=coa_data)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @web_application.post("/violation_by_bin")
    async def violation_by_bin(request: BinRequest):
        try:
            query = f"""
            SELECT bin_num, violation_date, violation_link FROM violations_oath WHERE bin_num = {request.bin_number}
            """
            returned = pd.DataFrame(sql_client.query(query=query, database="dob_bis"))

            violation_data = {
                "bin_num": request.bin_number,
                "violation_records": [
                    {
                        "violation_date": int(pd.Timestamp(row["violation_date"]).timestamp()),
                        "violation_link": row["violation_link"]
                    }
                    for _, row in returned.iterrows()
                ]
            }

            print(violation_data)

            return JSONResponse(content=violation_data)
        
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