import os
import sys

import django
import ipdb

from pathlib import Path

from management_before_django.table_managements.modules.create_model import create_model_from_database
from utils.variables.paths import models_file_path
from utils.functions.do_we_have_model import do_we_have_model

# Empty models case:
if not do_we_have_model(models_file_path):
    create_model_from_database()

# Preparing django to run outside its dir:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finances_table_filter_mail_project.settings')
sys.path.append("./dj_project")
django.setup()

from dj_project.model_to_email.views import EmailAttachByTable

from management_before_django.table_managements.scripts import tables_to_db

from robot_sharepoint.modules.robots.robot_to_upload_files import upload_files_to_sharepoint
from robot_sharepoint.modules.robots.robot_to_download_database_spreadsheet import download_database_from_sharepoint
from robot_sharepoint.modules.robots.robot_to_download_contacts import download_contacts_from_sharepoint
from robot_sharepoint.reports.reports_utils.join_reports import join_reports

from utils.functions.path_length import do_we_have_spreadsheets
from utils.functions.deleting_elements import do_we_have_things_to_delete
from utils.variables.envs import download_directory, user_email, password, raw_table_directory, sharepoint_for_database_and_upload_url, sharepoint_measurements_url
from utils.variables.paths import edited_tables_path, models_file_path, raw_tables_path, reports_path
from utils.variables.report_files import not_found_list, sent_list, elements_reports_list, sent_title


# django app dir for working with view attachments:
root_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = str(root_directory)

# Clean up former final reports:
do_we_have_things_to_delete(reports_path, "relatorio_diario.txt")

# Drafts for deleting edited table after month turn:
delete_me_FLAG = "DELETE_ME_BEFORE_FIRST_MONTH_OPERATION.txt"

if not Path(delete_me_FLAG).exists():
    do_we_have_things_to_delete(raw_tables_path, ".xlsx")
    do_we_have_things_to_delete(edited_tables_path, ".xlsx")
    
    Path(delete_me_FLAG).touch()
    with open(delete_me_FLAG, 'w') as file:
        file.write("Only delete me when it will be the first operation of the month...")
    
    # Raw reports creation for new database spreadsheet::
    with reports_path.joinpath(sent_list).open("w") as file:
        file.write(sent_title)

do_we_have_table_to_work_with = do_we_have_spreadsheets(raw_tables_path, 2)

if not do_we_have_table_to_work_with:
    print("DOWNLOADING SHAREPOINT SPREADSHEETS.")
    download_contacts_from_sharepoint(user_email, password, sharepoint_for_database_and_upload_url, raw_tables_path)
    download_database_from_sharepoint(user_email, password, sharepoint_for_database_and_upload_url, raw_tables_path)

try:
    tables_to_db.tables_to_db()
    EmailAttachByTable().post(root_directory)
except Exception as e: 
    print(f"PROCESS INTERRUPTED! Error: {e} CONTACT THE DEV RESPONSIBLE.")
finally: 
    print("ELABORATING FINAL REPORT AND UPLOADING....")
    join_reports(not_found_list, sent_list, elements_reports_list, reports_path)
    upload_files_to_sharepoint(user_email, password, reports_path, sharepoint_for_database_and_upload_url)
    print("PROCESS FINISHED! CHECK REPORT UPLOADED.")
