__author__ = "Rahul Puram (uig54526)"
__copyright__ = "2024-2023, Continental AG"

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import datetime

# Importing BeautifulSoup class from the bs4 module 
from bs4 import BeautifulSoup
import re
 
def send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body_html):
    # Create a multipart message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_email)
    msg['Subject'] = subject
    
    #greetings = "Hello Team,\n\n\n"
    #regards = "Thanks,\n"+"FFL CL Jenkins\n"

    full_text = f"Hello Team,{body_html}<br/>Thanks and Regards,<br/>FFL CL Jenkins"
    html_part = MIMEText(full_text, 'html')
    msg.attach(html_part)
 
    # # Attach the file
    # if attachment_path:
    #     filename = attachment_path.split('\\')[-1]
    #     part = MIMEBase('application', 'octet-stream')
    #     with open(attachment_path, 'rb') as file:
    #         part.set_payload(file.read())
    #     encoders.encode_base64(part)
    #     part.add_header('Content-Disposition', f'attachment; filename={filename}')
    #     msg.attach(part)
 
    # Set up the SMTP server
    try:
    # Connect to the SMTP server
        server = smtplib.SMTP('SMTPHubEU.contiwan.com', 587)
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(sender_email, sender_password)  # Log in to the SMTP server
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)  # Send the email
        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {e}')
    finally:
        server.quit()  # Close the connection to the SMTP server
 
def retrieve_html_info(report_file):
    # Opening the html file 
    HTMLFile = open(report_file, "r")

    # Creating a BeautifulSoup object and specifying the parser 
    soup = BeautifulSoup(HTMLFile, 'html.parser') 

    # Find the table using the class attribute
    project_table = soup.find('table', class_='table-sm table-striped mb-3')

    # Find the table using the id attribute
    tc_table = soup.find('table', id='tc_overview')

    project_table_dict = {}
    for k in project_table.tbody.find_all('tr'):
        rows = k.find_all('th')
        cols = k.find_all('td')
        for i, j in zip(rows, cols):
            project_table_dict[i.text.replace(':', '')] = j.text
    #print(project_table_dict)

    test_case_table_dict = {}
    for k in tc_table.tbody.find_all('tr'):
        rows = k.find_all('td')
        for i in range(0, len(rows), 2):
            test_case_table_dict[rows[i].text] = rows[i+1].text
    #print(test_case_table_dict)
    return project_table_dict, test_case_table_dict

if __name__ == "__main__":
    sender_email = 'uig88154@contiwan.com'
    sender_password = 'Helloworld@123'
    #recipient_email = ['shashikala.r.s@continental-corporation.com','devendra.ogi@continental-corporation.com','madhurika.rao.k.s@continental-corporation.com']
    recipient_email = ['shashikala.r.s@continental-corporation.com']   
    subject = '[SYS230TM14] Closed Loop FFL JENKINS CI/CD'
    body_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    #banner
    {{
        background-color: blue;
        color: white;
        text-align: left;
    }}
    tr 
    {{
        text-align: center;
    }}
    table 
    {{
        width: fit-content;
        border: none;
    }}
    </style>
    </head>

    <body>
        <br/>
        <table>
            <td id="banner" colspan="3"><b>Jenkins</b></td>
            <tr>
                <td><b>URL</b></td>
                <td><b>:</b></td>
                <td><b><a href="{url_link}">{url_link}</a></b></td>
            </tr>
            <td id="banner" colspan="3"><b>Test Execution Information</b></td>
            <tr>
                <td><b>Start date & time</b></td>
                <td><b>:</b></td>
                <td>{datetime}</td>
            </tr>
            <tr>
                <td><b>Software Version</b></td>
                <td><b>:</b></td>
                <td>{sw_version}</td>
            </tr>
            <tr>
                <td><b>Simulation GitHub URL</b></td>
                <td><b>:</b></td>
                <td><b><a href="{simulation_github_url}">{simulation_github_url}</a></b></td>
            </tr>
            <tr>
                <td><b>Validation GitHub URL</b></td>
                <td><b>:</b></td>
                <td><b><a href="{validation_github_url}">{validation_github_url}</a></b></td>
            </tr>
            <tr>
            <tr>
                <td><b>Contest GitHub URL</b></td>
                <td><b>:</b></td>
                <td><b><a href="{contest_github_url}">{contest_github_url}</a></b></td>
            </tr>
            <tr>
                <td><b>Target platform</b></td>
                <td><b>:</b></td>
                <td>Dummy Platform</td>
            </tr>
            <tr>
                <td><b>Report file</b></td>
                <td><b>:</b></td>
                <td><b>{report_file}</b></td>
            </tr>
            <tr>
                <td><b>Test execution duration</b></td>
                <td><b>:</b></td>
                <td>{test_execution_duration}</td>
            </tr>
            <td id="banner" colspan="3"><b>Overall Result</b></td>
            <tr>
                <td><b>Executed Test Cases</b></td>
                <td><b>:</b></td>
                <td>{executed_test_cases}</td>
            </tr>
            <tr>
                <td><b>Passes Test Cases</b></td>
                <td><b>:</b></td>
                <td>{passed_test_cases}</td>
            </tr>
            <tr>
                <td><b>Failed Test Cases</b></td>
                <td><b>:</b></td>
                <td>{failed_test_cases}</td>
            </tr>
            <tr>
                <td><b>N/A Test Cases</b></td>
                <td><b>:</b></td>
                <td>{na_test_cases}</td>
            </tr>
            <tr>
                <td><b>Other Executed Test Cases</b></td>
                <td><b>:</b></td>
                <td>{other_executed_test_cases}</td>
            </tr>
        </table>
    </body>
    </html>
    """

    txt_dict = {}
    txt_key_list = ['output_folder', 'url', 'simulation_repo', 'validation_repo','contest_repo']

    # basepath
    basepath = r'\\cw01.contiwan.com\Root\Loc\blr3\didr3320\ADC544NN-Nissan\FFL_CL_Report_TATA_LVMD'
    # Fetch information from the text file related to the Jenkin jobs
    with open(basepath + '\Jenkin_information.txt') as txt:
        for key, line in zip(txt_key_list, txt.readlines()):
            txt_dict[key] = line.strip().replace('\n', '')

    # Fetch information from the html related to the test cases
    report_file = txt_dict['output_folder'] + r"\out\report\html\index.html"

    project_table_dict, test_case_table_dict = retrieve_html_info(report_file)

    body_html = body_html.format(url_link=txt_dict['url'], datetime=datetime.datetime.now(), \
                                 sw_version=project_table_dict['Subject under Test'], simulation_github_url=txt_dict['simulation_repo'], \
                                 validation_github_url=txt_dict['validation_repo'],contest_github_url=txt_dict['contest_repo'], report_file=txt_dict["output_folder"], \
                                 test_execution_duration=None, executed_test_cases=test_case_table_dict['Executed Test Cases'], \
                                 passed_test_cases=test_case_table_dict['PASSED Test Cases'], failed_test_cases=test_case_table_dict['FAILED Test Cases'], \
                                 na_test_cases=test_case_table_dict['N/A Test Cases'], other_executed_test_cases=test_case_table_dict['Other Executed Test Cases'])
    
    # # Creating the ZIP file
    # if not os.path.exists(base_path + r'\report.zip'):
    #     archived = shutil.make_archive(base_path + r'\report', 'zip', base_path + r'\out')
    #     print(" zip file created ")
    # else:
    #     print("Deleted existing zip file and creating new one")
    #     shutil.rmtree(base_path + r'\report.zip')
    #     archived = shutil.make_archive(base_path + r'\report', 'zip', base_path + r'\out')

    # attachment_path = base_path + r'\report.zip'
    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body_html)
