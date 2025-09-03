import os
import sys
import logging
import pandas as pd
import numpy as np
import random
import json
from datetime import datetime
import time
import zlib
import traceback
import boto3
from urllib.parse import unquote
from botocore.exceptions import NoCredentialsError
from urllib.parse import urlparse
import main as main_script
from common_main import get_secret, connect as db, get_aws_config,send_slack_message
import mysql.connector

# Add the project directory to the Python path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_path)

connection = db()
cursor = connection.cursor()

now = datetime.now()

from common_main import get_secret, connect as db, get_aws_config

def archive_csv_files_in_s3(bucket_name, aws_config):
    """Directly archive .csv files in S3 without downloading them."""
    folder_name = get_secret('folder_name')
    archive_folder = "archive"
    # archive_folder = get_secret('archive_folder')
    
    if not aws_config:
        print("AWS configuration missing. Please provide valid credentials.")
        return
    
    aws_region, aws_bucket, aws_access_key_id, aws_secret_access_key = aws_config
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    archive_folder= "archive"
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        if 'Contents' not in response:
            print("No files found in the folder.")
            return
        
        for obj in response['Contents']:
            file_key = obj['Key']
            file_name = os.path.basename(file_key)
            
            if file_name.endswith(".CSV") and (
                file_name.startswith("CAREX_C_")
                or file_name.startswith("ELEG-C-")
                or file_name.startswith("CAREX_F_")
                or file_name.startswith("ELEG-F-")
            ):
                archive_key = f"{archive_folder}/{file_name}"
                print(f"Archiving {file_key} to {archive_key}...")
                send_slack_message(get_secret("slack_webhook_devops"),f"Archiving {file_key} to {archive_key}...",)
                
                s3_client.copy_object(
                    Bucket=bucket_name,
                    CopySource={'Bucket': bucket_name, 'Key': file_key},
                    Key=archive_key,
                )
                
                print(f"Removing {file_key} from S3 bucket...")
                send_slack_message(get_secret("slack_webhook_devops"),f"Removing {file_key} from S3 bucket...",)
                s3_client.delete_object(Bucket=bucket_name, Key=file_key)
                
    except Exception as e:
        print(f"Error archiving .csv files: {e}")
        traceback.print_exc()

def download_file_from_s3(bucket_name, local_filename, aws_config):
    #group_id = get_secret('group_id')
    folder_name = get_secret('folder_name')

    if not aws_config:
        print("AWS configuration missing. Please provide valid credentials.")
        return []

    aws_region, aws_bucket, aws_access_key_id, aws_secret_access_key = aws_config
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    try:
        os.makedirs(local_filename, exist_ok=True)
        txt_response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        txt_files = []

        if 'Contents' in txt_response:
            for obj in txt_response['Contents']:
                file_key = obj['Key']
                file_name = os.path.basename(file_key)

                if file_name.endswith(".TXT") and (
                    file_name.startswith("CAREP_C_")
                    or file_name.startswith("ELEG-C-")
                    or file_name.startswith("CAREP_F_")
                    or file_name.startswith("ELEG-F-")
                ):
                    local_file_path = os.path.join(local_filename, os.path.relpath(file_key, folder_name))

                    # Normalize path to prevent issues
                    local_file_path = os.path.normpath(local_file_path)

                    # Remove any unwanted S3 metadata
                    local_file_path = local_file_path.split("s3.uploadpath=")[0].strip()

                    try:
                        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    except OSError as e:
                        print(f"Error creating directory for {local_file_path}: {e}")
                        send_slack_message(get_secret("slack_webhook_devops"),f"Error creating directory for {local_file_path}: {e}",)
                        continue
                    # Try downloading file
                    try:
                        print(f"Downloading {file_key} to {local_file_path}...")
                        send_slack_message(get_secret("slack_webhook_devops"),f"Downloading {file_key} to {local_file_path}...",)
                        s3_client.download_file(bucket_name, file_key, local_file_path)

                        if not os.path.exists(local_file_path):  # Ensure file was actually downloaded
                            print(f"Error: File was not downloaded successfully -> {local_file_path}")
                        else:
                            txt_files.append((file_key, local_file_path))  # Append only if successful
                            send_slack_message(get_secret("slack_webhook_devops"),f"Downloaded {file_key} to {local_file_path}...",)
                    except Exception as e:
                        print(f"Failed to download {file_key}: {e}")
                        send_slack_message(get_secret("slack_webhook_devops"),f"Failed to download {file_key}: {e}",)

        if not txt_files:
            print(f"No .txt files of Eligibility found in the folder '{folder_name}'.")
            send_slack_message(get_secret("slack_webhook_devops"),f"No .txt files of Eligibility found in the folder '{folder_name}'.",)
            return []

        return txt_files

    except Exception as e:
        print(f"Failed to retrieve or download .txt files: {e}")
        send_slack_message(get_secret("slack_webhook_devops"),f"Failed to retrieve or download .txt files: {e}",)
        traceback.print_exc()
        return []

def execute_query():
    """Execute the SQL query to update the database."""
    try:
        logging.info("Connecting to the database...")
        
        # Establish a database connection
        cursor = connection.cursor()

        # Execute the query
        query = f"UPDATE equipo_call_center.patients_medilinea_md_eligibility_roster SET status = 0;"
        cursor.execute(query)
        connection.commit()

        logging.info("Database updated successfully.")
        print("Database updated successfully.")
        send_slack_message(get_secret("slack_webhook_devops"),f"Status Inactivate updated successfully.",)
        
        # Close the connection
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        print(f"Database error: {err}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {traceback.format_exc()}")
        print(f"Unexpected error: {e}")
        raise


def process_and_cleanup_files(txt_files, bucket_name, archive_folder, aws_config):
    aws_region, aws_bucket, aws_access_key_id, aws_secret_access_key = aws_config
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    archive_folder= "archive"

    for txt_file_key, txt_file_path in txt_files:
        try:
            # Archive the file
            archive_key = f"{archive_folder}/{os.path.basename(txt_file_key)}"
            print(f"Archiving {txt_file_key} to {archive_key}...")
            send_slack_message(get_secret("slack_webhook_devops"),f"Archiving {txt_file_key} to {archive_key}...",)
        
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': txt_file_key},
                Key=archive_key,
            )

            # Remove the file from the S3 bucket
            print(f"Removing {txt_file_key} from S3 bucket...")
            send_slack_message(get_secret("slack_webhook_devops"),f"Removing {txt_file_key} from S3 bucket...",)
        
            s3_client.delete_object(Bucket=bucket_name, Key=txt_file_key)

            # Remove the local file
            if os.path.exists(txt_file_path):
                os.remove(txt_file_path)
                print(f"Removed local file: {txt_file_path}")
                # send_slack_message(get_secret("slack_webhook_devops"),f"Removed local file: {txt_file_path}",)

        except Exception as e:
            print(f"Error during cleanup for {txt_file_key}: {e}")
            send_slack_message(get_secret("slack_webhook_devops"),f"Error during cleanup for {txt_file_key}: {e}",)

            traceback.print_exc()

def main():
    try:
        print("Running common_main.py utilities...")
        aws_config = get_aws_config(cursor)

        # print("Downloading files from S3...")
        send_slack_message(get_secret("slack_webhook_devops"),f"Downloading files from S3...",)

        bucket_name = get_secret('nl_bucket_name')
        local_file_path = get_secret('eligibility_file_path')
        archive_csv_files_in_s3(bucket_name, aws_config)
        txt_files = download_file_from_s3(bucket_name, local_file_path, aws_config)
        
       

        if not txt_files:
            print("No files to process. Exiting job.")
            return
        # Update the database ONLY if files are found
        execute_query()

        print("Running main.py for Pentaho job and data loading...")
        # send_slack_message(get_secret("slack_webhook_devops"),f"Triggering Pentaho job...",)
        try:
            eligibility_jobs = get_secret('eligibility_jobs')

            # Loop through each Pentaho job and execute it
            for job_key, job_name in eligibility_jobs.items():
                logging.info(f"Running Pentaho job: {job_name}")
                # Call Pentaho job to load data
                flag = main_script.load_data(job_name)
                if flag == False:
                    print("Exiting the job...")
                    send_slack_message(get_secret("slack_webhook_devops"),f"Pentaho job Failed...",)
                    sys.exit()

        except Exception as e:
            print("Pentaho job failed. Skipping file cleanup.")
            send_slack_message(get_secret("slack_webhook_devops"),f"Pentaho job failed. Skipping file cleanup.",)
            traceback.print_exc()
            return

        print("Processing and cleaning up files...")
        send_slack_message(get_secret("slack_webhook_devops"),f"Processing and cleaning up files...",)
            
        archive_folder = get_secret('archive')
        process_and_cleanup_files(txt_files, bucket_name, archive_folder, aws_config)
        

    except Exception as e:
        print(f"An error occurred: {traceback.format_exc()}")


if __name__ == "__main__":
    print("Job Started...")
    print("Start time: " + str(datetime.now()))
    send_slack_message(
            get_secret("slack_webhook_devops"),
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: MCS Nursing Line Eligiblity Job Starting...",
        )
    main()
    print("Job Ended...")
    print("End time: " + str(datetime.now()))
    send_slack_message(
            get_secret("slack_webhook_devops"),
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: MCS Nursing Line Eligiblity Job Completed...",
        )
