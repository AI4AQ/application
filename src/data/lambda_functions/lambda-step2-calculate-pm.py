# Lambda scripts, Step 2 of 5
# This script is triggered to run whenever a file is added to the directory "temp/lambda1output",
# which is done in Step 1
# The purpose of this script is to calculate PM2.5 and PM10
# The output is stored in "temp/lambda2output/temp_calculated_daily_purpleair_sensor_data.json",
# which is subsequently used in Step 3 of 5.

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
        # load the daily sensor data from S3
        purple_air_daily_object_key = "temp/lambda1output/temp_output_daily_purpleair_sensor_data.json"
        pa_daily_file_content = s3_client.get_object(
            Bucket=S3_BUCKET_NAME, Key=purple_air_daily_object_key)["Body"].read()
        daily_sensor_data = json.loads(pa_daily_file_content)
        
        # create an empty list to store new values for each sensor
        # that is a calculated PM value
        calculated_pm_values = []
        
        for sensor_entry in daily_sensor_data:
            pm25_a = sensor_entry.get("pm2.5_atm_a")
            pm25_b = sensor_entry.get("pm2.5_atm_b")
            pm10_a = sensor_entry.get("pm10.0_atm_a")
            pm10_b = sensor_entry.get("pm10.0_atm_b")
            
            # logic for pm2.5 calculation
            # if only channel A is present, and it has a value <=500 and >0, use channel A value
            if pm25_a is not None and pm25_a <= 500 and pm25_a > 0 and (pm25_b is None or pm25_b > 500 or pm25_b == 0):
                sensor_entry["pm2"] = pm25_a
            
            # if only channel B is present, and it has a value <=500, use channel B value
            elif pm25_b is not None and pm25_b <= 500 and pm25_b > 0  and (pm25_a is None or pm25_a > 500 or pm25_a == 0):
                sensor_entry["pm2"] = pm25_b
                
            # if both channels are present, and they both have values <= 500, take the average of channel values
            elif pm25_a is not None and pm25_b is not None and 0 < pm25_a <= 500 and 0 < pm25_b <= 500:
                sensor_entry["pm2"] = (pm25_a + pm25_b) / 2
                
            # otherwise, set value to None since requirements above were not met
            else:
                sensor_entry["pm2"] = None
            
            # logic for pm10 calcuation
            # same logic as pm2.5
            if pm10_a is not None and pm10_a <= 500 and pm10_a > 0 and (pm10_b is None or pm10_b > 500 or pm10_b == 0):
                sensor_entry["pm10"] = pm10_a
            elif pm10_b is not None and pm10_b <= 500 and pm10_b > 0 and (pm10_a is None or pm10_a > 500 or pm10_a == 0):
                sensor_entry["pm10"] = pm10_b
            elif pm10_a is not None and pm10_b is not None and 0 < pm10_a <= 500 and 0 < pm10_b <= 500 :
                sensor_entry["pm10"] = (pm10_a + pm10_b) / 2
            else:
                sensor_entry["pm10"] = None
            
            # add today's date
            sensor_entry["date"] = datetime.now().strftime('%Y-%m-%d')
        
            calculated_pm_values.append(sensor_entry)

        # serialize the calculated_pm_values list to bytes
        calculated_pm_values_bytes = bytes(json.dumps(calculated_pm_values), 'utf-8')

        # upload calculated data to S3
        output_file_key = "temp/lambda2output/temp_calculated_daily_purpleair_sensor_data.json"
        s3_client.put_object(Body=calculated_pm_values_bytes, Bucket=S3_BUCKET_NAME, Key=output_file_key)

        # return success response
        return {"statusCode": 200, "body": f"Data saved to S3://{S3_BUCKET_NAME}/{output_file_key}"}
  
    except Exception as e:
        # log any errors that occur during execution
        logger.error(f"Error in lambda_handler: {e}")
        # raise the exception to trigger the error response
        raise e