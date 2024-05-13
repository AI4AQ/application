# Lambda scripts, Step 1 of 5
# This script is triggered to run nightly using the "Event Bridge (Cloudwatch Events)" trigger.
# This trigger uses CRON to determine the timing for running the script
# The purpose of this script is to pull the current air quality data from PurpleAir,
# utilizing their API. The API key is stored in AWS Secrets Manager.
# The output is stored in "temp/lambda1output/temp_output_daily_purpleair_sensor_data.json",
# which is subsequently used in Step 2 of 5.


import json
import logging
import os
import urllib3
import boto3
import time

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# initialize S3 client and bucket name
s3_client = boto3.client("s3")
S3_BUCKET_NAME = 'ai4aq-prelim'

# define the Secrets Manager secret ID
SECRETS_MANAGER_SECRET_ID = 'purpleair/read'

def pull_current_outdoor_purpleair_sensor_data(fields, api_read_key, outdoor_sensor_list):
    """
    Retrieve the latest sensor data from the PurpleAir API for multiple sensors.

    Args:
    - fields (list of str): A list of fields to retrieve for each sensor.
    - api_read_key (str): API read key for PurpleAir.
    - outdoor_sensor_list (list): List of outdoor sensor IDs.

    Returns:
    - list of dicts: List of dictionaries containing sensor data for each sensor.
    """
    
    # initialize an empty list to store sensor data
    list_of_sensor_data = []
    
    # create an HTTP connection pool
    http = urllib3.PoolManager()
    
    # iterate through each outdoor sensor
    for sensor_id in outdoor_sensor_list:
        # construct the URL for the PurpleAir API
        url = f"https://api.purpleair.com/v1/sensors/{sensor_id}"
        
        # define parameters for the HTTP request
        params = {"fields": ",".join(fields)}
        headers = {"X-API-Key": api_read_key}
        
        try:
            # send a GET request to the PurpleAir API
            response = http.request('GET', url, fields=params, headers=headers, timeout=urllib3.Timeout(connect=5, read=10))
            # parse the JSON response
            sensor_response_json = json.loads(response.data.decode('utf-8'))
            # extract sensor data from the response
            sensor_data = sensor_response_json.get('sensor')
            # append sensor data to the list
            if sensor_data is not None:
                list_of_sensor_data.append(sensor_data)
            else:
                logger.warning(f"No data returned for sensor {sensor_id}")
        
        except Exception as e:
            # log any errors that occur during data retrieval
            logger.error(f"Error fetching data for sensor {sensor_id}: {e}")
    
    return list_of_sensor_data

def lambda_handler(event, context):
    
    try:
        # load the outdoor sensor list from S3
        purple_air_parameters_object_key = "purpleair_parameters.json"
        pa_parameter_file_content = s3_client.get_object(
            Bucket=S3_BUCKET_NAME, Key=purple_air_parameters_object_key)["Body"].read()
        outdoor_sensor_list = json.loads(pa_parameter_file_content).get('outdoor_sensor_list') # use sensor_test to test with fewer sensors for testing OR
                                                                                        # outdoor_sensor_list for all sensors.

        # retrieve the API read key from AWS Secrets Manager
        api_read_key = get_secret_from_secrets_manager()
        if api_read_key is None:
            # return an error response if the secret retrieval fails
            return {"statusCode": 500, "body": "Failed to retrieve secret from AWS Secrets Manager."}

        # define fields to retrieve from PurpleAir API
        # each field will increase cost
        fields = ['pm2.5_atm_a', 'pm2.5_atm_b', 'pm10.0_atm_a', 'pm10.0_atm_b']
        
        # fetch sensor data from PurpleAir API
        sensor_data = pull_current_outdoor_purpleair_sensor_data(fields, api_read_key, outdoor_sensor_list)
        
        # convert sensor data to JSON format
        sensor_data_json = json.dumps(sensor_data)

        # upload sensor data to S3
        output_file_key = "temp/lambda1output/temp_output_daily_purpleair_sensor_data.json"
        s3_client.put_object(Body=sensor_data_json, Bucket=S3_BUCKET_NAME, Key=output_file_key)

        # return success response
        return {"statusCode": 200, "body": f"Data saved to S3://{S3_BUCKET_NAME}/{output_file_key}"}
    
    except Exception as e:
        # log any errors that occur during execution
        logger.error(f"Error in lambda_handler: {e}")
        # raise the exception to trigger the error response
        raise e

def get_secret_from_secrets_manager():
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
        api_read_key = secret_json.get("purple-air-read-key")
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