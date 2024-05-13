# Lambda scripts, Step 5 of 5
# This script is triggered to run nightly using the "Event Bridge (Cloudwatch Events)" trigger.
# This trigger uses CRON to determine the timing for running the script, and is scheduled to run 15
# minutes after Step 1, allowing Steps 1-4 ample time to complete before running.
# The purpose of this script is to send a copy of the full historical output of Step 4
# from this S3 bucket to the Lightsail S3 bucket. The application that is hosted in Lightsail
# relies on the bucket in Lightsail.
# NOTE: there is likely a better solution, but this worked for MVP with the IAM accounts we had configured
# and the time permitted

import json
import logging
import csv
import tempfile
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def lambda_handler(event, context):
    def get_secret_from_secrets_manager(SECRETS_MANAGER_SECRET_ID, secret_key):
        # initialize Secrets Manager client
        # this will pull from the Secrets Manager API directly,
        # not using the extension in Lambda
        client = boto3.client('secretsmanager')
        
        try:
            
            # retrieve the secret value from Secrets Manager
            response = client.get_secret_value(SecretId=SECRETS_MANAGER_SECRET_ID)
            secret_value = response['SecretString']
            # parse the secret JSON
            secret_json = json.loads(secret_value)
            # extract the API read key from the secret
            api_read_key = secret_json.get(secret_key)
            if api_read_key is None:
                # raise an error if the API read key is missing in the secret
                raise ValueError("API read key is missing in the secret.")
            # log the received secret
            logger.info("Secret received: %s", api_read_key)
            return api_read_key
        
        except Exception as e:
            # log any errors that occur during secret retrieval
            logger.error(f"Error fetching secret: {e}")
            return None
    
    # Define the buckets
    source_bucket_name = "ai4aq-prelim"
    destination_bucket_name = "ai4aq"
    prelim_file_key = "data/all_history/slc_daily_pm2.5_pm10_2016_present.csv"
    file_key = "data/slc_daily_pm2.5_pm10_2016_present.csv"
    
    # Initialize S3 clients for prelim bucket
    s3_source = boto3.client("s3")
    
    # Initalize S3 bucket sec
    ai4aq_bucket_access_key = get_secret_from_secrets_manager('lightsail_s3_access_key', 'lightsail_s3_access_key')
    ai4aq_bucket_secret_access_key = get_secret_from_secrets_manager('lightsail_s3_secret_access_key', 'lightsail_s3_secret_access_key')
        
    # initialize S3 client for ai4aq bucket with secrets
    s3_destination = boto3.client("s3", aws_access_key_id = ai4aq_bucket_access_key, aws_secret_access_key = ai4aq_bucket_secret_access_key)

    try:
        # Get the object from the prelim bucket
        response = s3_source.get_object(Bucket=source_bucket_name, Key=prelim_file_key)
        # Read the content of the object
        file_content = response['Body'].read()
        
        # Put the object into the destination bucket
        s3_destination.put_object(Bucket=destination_bucket_name, Key=file_key, Body=file_content)
        
        return {
            "statusCode": 200,
            "body": "File copied successfully."
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error: {e}"
        }