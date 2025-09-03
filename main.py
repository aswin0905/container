import logging
from datetime import datetime
import os
import subprocess
import sys
import traceback

# Get the path to the directory containing main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
common_module_path = os.path.normpath(os.path.join(current_dir, '..'))
sys.path.append(common_module_path)

from common_main import get_secret,send_slack_message

# Set up logging
log_path = get_secret('eligibility_log_location')
if not os.path.exists(log_path):
    os.makedirs(log_path)
now = datetime.now()
logName = os.path.join(log_path, f"{now.strftime('%Y-%m-%d')}_Eligibility_Dataload.log")
logging.basicConfig(filename=logName, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def run_pentaho_job(job_name):
    """Run the specified Pentaho job."""
    try:
        pentaho_job_directory = get_secret('pentaho_job_directory')
        pentaho_log = get_secret('pentaho_log')
        
        # Construct the job path and log file name
        job_path = os.path.join(pentaho_job_directory, job_name)
        log_file = os.path.join(
            pentaho_log,
            f"{job_name.replace('.kjb', '')}_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        )

        # Execute the Pentaho job
        #child = subprocess.Popen(
         #   f"/home/aswin/Desktop/sample/data-integration/kitchen.sh -file={job_path} -LEVEL=NORMAL -logfile={log_file}",
          #  cwd='/home/aswin/Desktop/sample/data-integration',
           # shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        #)
        child = subprocess.Popen(
                "call C:\pdi-ce-8.2.0.0-342\data-integration\kitchen.bat /file:" + pentaho_job_directory + job_name + " -LEVEL=NORMAL -logfile=" + pentaho_log + job_name.replace(
                    "_All.kjb", "") + "_log_%date:~4,2%%date:~7,2%%date:~10,4%_%time:~0,2%%time:~3,2%%time:~6,2%.log",
                cwd='C:\pdi-ce-8.2.0.0-342\data-integration', shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        output, error = child.communicate()

        if child.returncode != 0:
            logging.error(f"ETL Job Failed for {job_name}:\n{error.decode()}")
            print(f"ETL Job Failed for {job_name}!")
            return False
        else:
            logging.info(f"ETL Job Successful for {job_name}")
            print(f"ETL Job Successful for {job_name}!")
            return True

    except Exception as e:
        logging.error(f"Error running Pentaho job {job_name}: {traceback.format_exc()}")
        print(f"Error running Pentaho job {job_name}: {e}")
        return False

def load_data(job_name):
    """Load data using Pentaho jobs."""
    try:
        logging.info("Starting Pentaho jobs...")
        send_slack_message(get_secret("slack_webhook_devops"),f"Starting Pentaho jobs...",)
        # pentaho_jobs = get_secret('pentaho_jobs')

        # # Loop through each Pentaho job and execute it
        # for job_key, job_name in pentaho_jobs.items():
        logging.info(f"Running Pentaho job: {job_name}")
        flag_id =run_pentaho_job(job_name)
        logging.info(f"{job_name} jobs completed successfully.")
        send_slack_message(get_secret("slack_webhook_devops"),f"{job_name} jobs completed successfully.",)
        return flag_id
        
    except Exception as e:
        logging.error(f"Error in load_data function: {traceback.format_exc()}")
        print(f"Error in load_data function: {e}")
        return flag_id

# if __name__ == "__main__":
#     try:
#         logging.info("Job Started...")
#         print("Job Started...")
#         print("Start time:", datetime.now())

#         load_data()

#         logging.info("Job Ended.")
#         print("Job Ended...")
#         print("End time:", datetime.now()) 
#     except Exception as e:
#         logging.error(f"An unexpected error occurred: {traceback.format_exc()}")
#         print(f"An unexpected error occurred: {e}")
