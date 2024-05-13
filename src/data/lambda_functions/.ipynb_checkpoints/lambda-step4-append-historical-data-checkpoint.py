# Lambda scripts, Step 4 of 5
# This script is triggered to run whenever a file is added to the directory "temp/lambda3output",
# which is done in Step 3
# The purpose of this script is to save the data from Step 3 as its own daily file, in case it is needed.
# More importantly, this script adds today's data to all historical data so that it can be accessed
# by the application.

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

# initialize S3 client and bucket name
s3_client = boto3.client("s3")
S3_BUCKET_NAME = 'ai4aq-prelim'

def lambda_handler(event, context):
    try:
        # load daily sensor data with all values, daily and static from JSON
        purple_air_daily_final_object_key = "temp/lambda3output/temp_calculated_daily_purpleair_sensor_data_with_static.json"
        pa_daily_final = s3_client.get_object(
            Bucket=S3_BUCKET_NAME, Key=purple_air_daily_final_object_key)["Body"].read()
        daily_sensor_data_final = json.loads(pa_daily_final)
        
        # load the current state of the entire historical dataset from CSV
        historical_data_key = "data/all_history/slc_daily_pm2.5_pm10_2016_present.csv"
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=historical_data_key)
        historical_data_csv = response['Body'].read().decode('utf-8').splitlines()
        
        # create empty list to house CSV data,
        # it will first hold historic up until today, and then we will add today
        historical_data_current = []
        
        # parse the CSV data
        csv_reader = csv.reader(historical_data_csv)
        for row in csv_reader:
            historical_data_current.append(row)
        
        # convert daily JSON data to list of lists
        daily_data_list = [list(inner_dict.values()) for inner_dict in daily_sensor_data_final]
        
        # append new JSON data to historical CSV data
        for row in daily_data_list:
            historical_data_current.append(row)
        
        # convert updated historical data to CSV format
        historical_data_csv = '\n'.join([','.join(map(str, row)) for row in historical_data_current])
        
        # save 2 files as CSVs
        # 1) entire history thru today
        save_entire_history('ai4aq-prelim', 'data/all_history/slc_daily_pm2.5_pm10_2016_present', historical_data_current)

        # 2) just today's data
        save_todays_data('ai4aq-prelim', 'data/daily/slc_daily_pm2.5_pm10_daily', daily_data_list)
                
    except Exception as e:
        # log any errors that occur during execution
        logger.error(f"Error in lambda_handler: {e}")
        # raise the exception to trigger the error response
        raise e
        
    print(datetime.today().strftime('%Y%m%d'))

    return {
        'statusCode': 200,
        'body': 'CSV file saved successfully'
    }

def save_entire_history(s3_bucket_name_, output_file_key_, data):
    """
    This function saves the entire history of PurpleAir sensors, back to 2016
    NOTE: It will overwrite the existing file to contain today's data
    
    Parameters
    ----------
    s3_bucket_name_ : str
        The name of the S3 bucket where the file will be saved to
    output_file_key_ : str
        The relative filepath name of the document that will be saved in the S3 bucket
    data: object
        The data that will be loaded into the file
    """
    
    # upload updated CSV data to S3, first by
    # saving CSV data to a temporary file and then uploading it to S3
    temp_file = None  # declare temp_file outside the try block
    output_file_key = f"{output_file_key_}.csv" # name the final output file
    historical_data_current = data
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='') as tf:
            temp_file = tf  # assign the file object to temp_file
            writer = csv.writer(temp_file)
            writer.writerows(historical_data_current)
        
        # upload the CSV file to S3
        s3_client.upload_file(temp_file.name, s3_bucket_name_, output_file_key)
        print(f"CSV file saved to s3://{s3_bucket_name_}/{output_file_key}")
    except ClientError as e:
        print("Error:", e)
        return {
            'statusCode': 500,
            'body': 'Error saving CSV file to S3'
        }
    finally:
        if temp_file is not None:
            temp_file.close()
            
def save_todays_data(s3_bucket_name_, output_file_key_, data):
    """
    This function saves today's data in its own CSV

    Parameters
    ----------
    s3_bucket_name_ : str
        The name of the S3 bucket where the file will be saved to
    output_file_key_ : str
        The relative filepath name of the document that will be saved in the S3 bucket
    data: object
        The data that will be loaded into the file
    """
    # upload updated CSV data to S3, first by
    # saving CSV data to a temporary file and then uploading it to S3
    temp_file = None  # declare temp_file outside the try block
    output_file_key = f"{output_file_key_}_{datetime.today().strftime('%Y%m%d')}.csv" # name the final output file and append with today's date
    todays_data = data
    
    # initiate list with column names
    daily_data = [['sensor_id', 'pm2', 'pm10', 'date', 'latitude', 'longitude',
                    'date_created', 'model', 'hardware', 'position_rating', 'altitude']]
    
    # append each observation from todays_data                
    for row in todays_data:
        daily_data.append(row)
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='') as tf:
            temp_file = tf  # assign the file object to temp_file
            writer = csv.writer(temp_file)
            writer.writerows(daily_data)
        
        # upload the CSV file to S3
        s3_client.upload_file(temp_file.name, s3_bucket_name_, output_file_key)
        print(f"CSV file saved to s3://{s3_bucket_name_}/{output_file_key}")
    except ClientError as e:
        print("Error:", e)
        return {
            'statusCode': 500,
            'body': 'Error saving CSV file to S3'
        }
    finally:
        if temp_file is not None:
            temp_file.close()