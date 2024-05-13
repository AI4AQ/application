# Lambda scripts, Step 3 of 5
# This script is triggered to run whenever a file is added to the directory "temp/lambda2output",
# which is done in Step 2
# The purpose of this script is to combine the PM values calculates in Step 2
# with the static information about each sensor (altitude, etc.).
# The output is stored in "temp/lambda3output/temp_calculated_daily_purpleair_sensor_data_with_static.json",
# which is subsequently used in Step 4 of 5.

import json
import logging
import os
import urllib3
import boto3
from datetime import datetime

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# initialize S3 client and bucket name
s3_client = boto3.client("s3")
S3_BUCKET_NAME = 'ai4aq-prelim'

def lambda_handler(event, context):
    try:
        # load the daily sensor data from S3 with PM calculated values
        purple_air_calculated_pm_object_key = "temp/lambda2output/temp_calculated_daily_purpleair_sensor_data.json"
        pa_daily_calculated_pm_file_content = s3_client.get_object(
            Bucket=S3_BUCKET_NAME, Key=purple_air_calculated_pm_object_key)["Body"].read()
        daily_sensor_data_calculated_pm = json.loads(pa_daily_calculated_pm_file_content)
                
        # load the static sensor data from S3
        purple_air_unique_sensor_object_key = "unique_sensors.json"
        purple_air_unique_sensor_content = s3_client.get_object(
            Bucket=S3_BUCKET_NAME, Key=purple_air_unique_sensor_object_key)["Body"].read()
        purple_air_static_sensor_data = json.loads(purple_air_unique_sensor_content)
                
        merged_purpleair_daily_data = []
        for sensor_entry in daily_sensor_data_calculated_pm:
            sensor_index = str(sensor_entry['sensor_index']) # needs to be string to match the static data json object
            if sensor_index in purple_air_static_sensor_data:
                merged_entry = {**sensor_entry, **purple_air_static_sensor_data[sensor_index]}
                # drop the columns from channels A and B that we no longer need
                merged_entry.pop('pm2.5_atm_a', None)
                merged_entry.pop('pm2.5_atm_b', None)
                merged_entry.pop('pm10.0_atm_a', None)
                merged_entry.pop('pm10.0_atm_b', None)
                # merge this observation into the list
                merged_purpleair_daily_data.append(merged_entry)

        # serialize the calculated_pm_values list to bytes
        merged_purpleair_daily_data_bytes = bytes(json.dumps(merged_purpleair_daily_data), 'utf-8')
        
        # upload calculated data to S3
        output_file_key = "temp/lambda3output/temp_calculated_daily_purpleair_sensor_data_with_static.json"
        s3_client.put_object(Body=merged_purpleair_daily_data_bytes, Bucket=S3_BUCKET_NAME, Key=output_file_key)

        # return success response
        return {"statusCode": 200, "body": f"Data saved to S3://{S3_BUCKET_NAME}/{output_file_key}"}
  
    except Exception as e:
        # log any errors that occur during execution
        logger.error(f"Error in lambda_handler: {e}")
        # raise the exception to trigger the error response
        raise e