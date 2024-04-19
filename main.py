import psutil
import smtplib
from email.mime.text import MIMEText
import logging
import datetime

# Email AH
smtp_server = "smtpserver"
smtp_port = PortNumber
username = "emailadd"
password = "PassAddHere"
from_email = "emailadd"
to_email = "ReceiverEmail"
subject = "Drive Space Report"

# Specify the list of servers and their thresholds
server_thresholds = [
    {
        "server": r"\\PC03-w3",
        "c_drive_threshold": 300,
        "other_drive_threshold": 25
    }
#    {
#        "server": "\\srv12",
#        "c_drive_threshold": 20,
#        "other_drive_threshold": 30
#    },
#    {
#        "server": "\\srv13",
#        "c_drive_threshold": 25,
#        "other_drive_threshold": 40
#    }
]

message_body = "Server/Disk       |   Size          |  Free Space\n"

is_alert = False

for server_info in server_thresholds:
    server = server_info["server"]
    c_drive_threshold = server_info["c_drive_threshold"]
    other_drive_threshold = server_info["other_drive_threshold"]

    # Generate the list of physical disks to check
    partitions = psutil.disk_partitions(all=False)
    physical_disks = [drive for drive in partitions if "cdrom" not in drive.opts and "removable" not in drive.opts]

    for drive in physical_disks:
        try:
            usage = psutil.disk_usage(drive.mountpoint)
            free_space_gb = usage.free / (1024 ** 3)
            total_space_gb = usage.total / (1024 ** 3)
            percentage_free = usage.percent
            drive_name = server + " " + drive.mountpoint.replace('\\', '/')
            message_body += f"{drive_name:<15} {total_space_gb:>10.2f} GB  {free_space_gb:>10.2f} GB\n"
            if drive.device.endswith("\\c:") and free_space_gb < c_drive_threshold:
                message_body = message_body.replace(drive_name, f"<span style='color:red'>{drive_name}</span>")
                logging.warning(f"Low disk space on {drive_name}")
                is_alert = True
            elif free_space_gb < other_drive_threshold:
                message_body = message_body.replace(drive_name, f"<span style='color:red'>{drive_name}</span>")
                logging.warning(f"Low disk space on {drive_name}")
                is_alert = True
            else:
                logging.info(f"Disk space on {drive_name} is OK")
        except PermissionError as e:
            logging.error(f"PermissionError occurred while checking drive {drive.mountpoint}: {e}")
        except FileNotFoundError as e:
            logging.error(f"FileNotFoundError occurred while checking drive {drive.mountpoint}: {e}")
        except Exception as e:
            logging.error(f"Error occurred while checking drive {drive.mountpoint}: {e}")

# Generate email message
subject_prefix = "Alert: " if is_alert else ""
subject = f"{subject_prefix}{subject}"

if message_body:
    message_body = "<pre>" + message_body + "</pre>"
else:
    message_body = "No issues found"

msg = MIMEText(message_body, 'html')
msg['Subject'] = subject
msg['From'] = from_email
msg['To'] = to_email

# Send email
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(username, password)
    server.send_message(msg)
    logging.info("Email sent")

# Record end time
end_time = datetime.datetime.now()
logging.info("Script ended at {}".format(end_time))
