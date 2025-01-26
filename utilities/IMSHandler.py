import awswrangler as wr
from fastapi import HTTPException
import boto3
# IMS Query Handler
class IMSQueryHandler:
    def __init__(self, session: boto3.Session):
        self.session = session

    def list_of_databases(self):
        """
        List available databases in AWS Glue Catalog.
        """
        try:
            return wr.catalog.databases(boto3_session=self.session)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def list_of_tables(self, database: str):
        """
        List available tables in a given database.
        """
        try:
            return wr.catalog.tables(database=database, boto3_session=self.session)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def query(self, query: str, database: str):
        """
        Execute an Athena query against the specified database.
        """
        try:
            df = wr.athena.read_sql_query(
                query,
                database=database,
                boto3_session=self.session,
                ctas_approach=False,
                workgroup="AmazonAthenaLakeFormation"
            )
            # Return as a list of dictionaries
            return df.to_dict(orient='records')
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))