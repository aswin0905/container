import boto3
import smtplib
import os
import traceback
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from urllib.parse import unquote
from botocore.exceptions import NoCredentialsError
from urllib.parse import urlparse
from common_main import get_secret, connect as db, get_aws_config
now = datetime.now()

#Getting aws configurations
def list_processed_files(cursor):
    aws_config = get_aws_config(cursor)
    if not aws_config:
        print("AWS configuration missing. Cannot list files.")
        return []
    
    aws_region, aws_bucket, aws_access_key_id, aws_secret_access_key = aws_config
    archive_folder = get_secret('archive')
    
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    
    today = datetime.now(timezone.utc).date()  # Get today's date (without time)
    processed_files = {"Patient file": [], "Eligibility file": [], "Benefit file": []}
    
    try:
        response = s3_client.list_objects_v2(Bucket=aws_bucket, Prefix=archive_folder)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                file_name = os.path.basename(file_key)
                last_modified = obj['LastModified'].date()
                
                # Check if the file was modified today
                if last_modified == today:
                    if file_name.startswith("telemedc"):
                        processed_files["Patient file"].append(file_name)
                    elif file_name.startswith(("CAREP_C_", "CAREP_F_", "ELEG-F-", "ELEG-C-")) and file_name.endswith(".TXT"):
                        processed_files["Eligibility file"].append(file_name)
                    elif file_name.startswith("MCS_BEN_"):
                        processed_files["Benefit file"].append(file_name)
        
    except Exception as e:
        print(f"Error fetching S3 file list: {e}")
        traceback.print_exc()
    
    return processed_files


def send_email(processed_files):
    smtp_host = get_secret("SMTP_SERVER")
    smtp_port = get_secret("SMTP_PORT")
    smtp_user = get_secret("SMTP_USER")
    smtp_password = get_secret("SMTP_PASSWORD")
    sender_mail = get_secret("SENDER_MAIL")
    recipient_mail = get_secret("RECIPIENT_MAIL").split(",")
    
    subject = f"MCS Nursing Line Data Load Report - {datetime.now().strftime('%m/%d/%Y')}"

    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #007BFF;
                text-align: center;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            h2 {{
                color: #333;
                border-bottom: 2px solid #007BFF;
                padding-bottom: 5px;
            }}
            .file-category {{
                font-size: 16px;
                font-weight: bold;
                color: #007BFF;
                margin-top: 10px;
            }}
            .file-list {{
                background: #f9f9f9;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                line-height: 1.6;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            table, th, td {{
                border: 1px solid #ddd;
                text-align: left;
            }}
            th, td {{
                padding: 10px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #666;
                text-align: center;
            }}
            .contact-info {{
                font-size: 14px;
                color: #333;
                text-align: center;
                margin-top: 20px;
            }}
            .contact-info a {{
                color: #007BFF;
                text-decoration: none;
            }}
            .lower-section {{
                display: flex;
                justify-content: flex-start;
                align-items: center;
                margin-top: 30px;
            }}
            .thank-you {{
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: left;
            }}
            .lower-logo img {{
                width: 120px; /* Reduce size */
                height: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Centered Logo (Kept As Is, Small Size) -->
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="cid:additional_logo" alt="Additional Image" width="150" height="auto" />
            </div>

            <h1 style="color: black;">Data Load Report</h1>
            <p>Processed On: {datetime.now().strftime('%m/%d/%Y')}</p>
            <p>This is to inform you that the files you shared have been successfully processed and data is now available in the application.</p>
            <h2 style="border-bottom: none;">Details</h2>
    """

    # Adding the details of the processed files
    html_body += "<table><tr><th>File Category</th><th>Files</th></tr>"

    for category, files in processed_files.items():
        file_list = "<br>".join(files) if files else "No files processed"
        html_body += f"<tr><td>{category}</td><td>{file_list}</td></tr>"

    html_body += "</table>"

    html_body += f"""
            <!-- Footer Section with Left-Aligned Logo and Thank You Message -->
            <div class="lower-section">
                <div>
                    <p class="thank-you">Thanks,<br>Equipo Health Inc.</p>
                    <div class="lower-logo">
                        <img src="cid:company_logo" alt="Company Logo" />
                    </div>
                </div>
            </div>

            <!-- Contact Info (Centered, No Intersection) -->
            <div class="contact-info">
                <p>
                    If you have any questions or concerns, please contact us at
                    <a href="mailto:support@equipohealth.com">support@equipohealth.com</a>.
                </p>
                <p></p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_mail
    msg['To'] = ", ".join(recipient_mail)
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))


    # Add the inline image (attach as MIMEImage)
    with open(r'C:\workspace\data\MCS\logo\eq_image.png', 'rb') as img_file:
        img_data = img_file.read()
        image = MIMEImage(img_data, _subtype="jpeg")
        image.add_header('Content-ID', '<company_logo>')
        msg.attach(image)

    # Add the second image (additional logo or image)
    with open(r'C:\workspace\data\MCS\logo\mcsLogo.png', 'rb') as img_file:
        img_data = img_file.read()
        image = MIMEImage(img_data, _subtype="jpeg")
        image.add_header('Content-ID', '<additional_logo>')
        msg.attach(image)



    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_password)  # API key-based authentication
            server.sendmail(sender_mail, recipient_mail, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    connection = db()
    cursor = connection.cursor()
    files = list_processed_files(cursor)
    send_email(files)

