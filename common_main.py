import base64
import json
import traceback

from mysql.connector import pooling
import pymysql
import requests
import mysql.connector
import os
import datetime
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import pymysql.cursors

#  to take the current dir
current_directory = os.getcwd()
secrets_file_path = "secrets.json"
module_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(module_directory, secrets_file_path)



def get_secret(
        setting_name,
        secrets_file_path=full_path,
):
    """Retrieve a secret setting from the specified secrets JSON file or raise an exception if not found"""
    with open(secrets_file_path) as secrets_file:
        secrets_data = json.load(secrets_file)
    try:
        return secrets_data[setting_name]
    except KeyError:
        raise Exception("The '{}' setting is not found in the secrets file.".format(setting_name))




def establish_db_connection():
    try:
        db_connection = mysql.connector.connect(
            host=get_secret("DB_HOST"),
            user=get_secret("DB_USER"),
            password=get_secret("DB_PASSWORD"),
            db=get_secret("DB_NAME"),
        )
        return db_connection
    except Exception as e:
        print("error connecting db", e)


def connect():
    connection = pymysql.connect(host=get_secret('DB_HOST'), user=get_secret('DB_USER'),
                                 password=get_secret('DB_PASSWORD'), database=get_secret('DB_NAME'), 
                                #   port = get_secret('port'),
                                 autocommit=True,
                                 charset='utf8mb4')  # Set the character encoding here
    return connection


def send_slack_message(webhook_url, message):
    slack_data = {'text': message}
    # print(slack_data)
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        return f'Request to slack returned an error {response.status_code}, {response.text}'




def create_log_folder(log_folder):
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)


def write_to_text_file(file_name, content):
    try:
        with open(file_name, 'w') as f:
            f.write(content)
        print(f"Content successfully written to {file_name}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_aws_config(cursor):
    try:
        check_file_ins3_query = """
        SELECT JSON_UNQUOTE(JSON_EXTRACT(config_detail, '$.REGION')) AS aws_region,
            JSON_UNQUOTE(JSON_EXTRACT(config_detail, '$.AWS_BUCKET')) AS aws_bucket,
            JSON_UNQUOTE(JSON_EXTRACT(config_detail, '$.AWS_ACCESS_KEY_ID')) AS aws_access_key_id,
            JSON_UNQUOTE(JSON_EXTRACT(config_detail, '$.AWS_SECRET_ACCESS_KEY')) AS aws_secret_access_key
        FROM equipo_external_interface.external_vendor_config
        WHERE tag = 'nursing_line'
        LIMIT 1;
                """
        cursor.execute(check_file_ins3_query)
        results = cursor.fetchall()
        # print(results)
        return results[0] if results else None
    except Exception as e:
        print("Error querying S3 repository:", traceback.format_exc())
        return None