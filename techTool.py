import os
import tarfile
import shutil
import time
import datetime
from datetime import datetime
#from datetime import datetime, timedelta
import subprocess
from pathlib import Path
import chardet
import re
import tempfile
import base64
import logging
import gzip
import argparse



def extract_tar_to_folder(tar_path: str, output_dir: str):
    """
    Extracts the contents of a tar file to a new folder with the same name as the tar file.

    Args:
        tar_path (str): Path to the tar file.
        output_dir (str): Directory where the extracted files will be placed.
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract the tar file
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(path=output_dir)
            #print(f"Extracted contents from {tar_path} to {output_dir}")
    except Exception as e:
        print(f"Error extracting tar file: {e}")

def remove_directory(expand_tree: str):
    """
    Removes a directory and its contents (files and subdirectories).

    Args:
        expand_tree (str): Path to the directory to be removed.
    """
    try:
        shutil.rmtree(expand_tree)
        #print(f"Directory {expand_tree} and its contents removed successfully.")
    except Exception as e:
        if "[Errno 16]" in str(e):
            print(f"Error: Device or resource busy. Checking for open files/processes...")
            # List files in the directory
            files_in_directory = os.listdir(expand_tree)
            for filename in files_in_directory:
                file_path = os.path.join(expand_tree, filename)
                try:
                    os.remove(file_path)
                    print(f"File {file_path} removed successfully.")
                except IsADirectoryError:
                    # If it's a directory, try to remove it directly
                    try:
                        os.rmdir(expand_tree)
                        print(f"Empty directory {expand_tree} removed successfully.")
                    except Exception as dir_error:
                        print(f"Error removing directory: {dir_error}")
        else:
            print(f"Error removing directory: {e}")

def print_file_content(file_name):
    try:
        with open(file_name, 'r') as file:
            content = file.read()
            print(content)
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")



def read_log_file(file_name):
    """Reads the log file and returns its lines."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_name, 'r', encoding=encoding) as log_file:
                return log_file.readlines()
        except UnicodeDecodeError:
            logging.warning(f"Failed to decode '{file_name}' with encoding '{encoding}'. Trying next encoding.")
        except FileNotFoundError:
            logging.error(f"File '{file_name}' not found.")
            return []
        except Exception as e:
            logging.error(f"An error occurred while reading '{file_name}' with encoding '{encoding}': {e}")
            return []

    # If all encoding attempts fail, read the file in binary mode
    try:
        with open(file_name, 'rb') as log_file:
            return log_file.readlines()
    except FileNotFoundError:
        logging.error(f"File '{file_name}' not found.")
        return []
    except Exception as e:
        logging.error(f"An error occurred while reading '{file_name}' in binary mode: {e}")
        return []





from collections import OrderedDict


# Precompile regex patterns and store them with datetime formats
TIMESTAMP_FORMATS = OrderedDict([
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)"), "%Y-%m-%d %H:%M:%S,%f"),
    (re.compile(r"^<DEBUG> (\d{1,2}-\w{3}-\d{4})(::\d{2}:\d{2}:\d{2}\.\d+)?$"), "%d-%b-%Y::%H:%M:%S.%f" if "::" in r"\1" else "%d-%b-%Y"),
    (re.compile(r"^<INFO> (\d{1,2}-\w{3}-\d{4})(::\d{2}:\d{2}:\d{2}\.\d+)?$"), "%d-%b-%Y::%H:%M:%S.%f" if "::" in r"\1" else "%d-%b-%Y"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)"), "%Y-%m-%dT%H:%M:%S.%f"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"), "%Y-%m-%dT%H:%M:%S"),
    (re.compile(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"), "%Y/%m/%d %H:%M:%S"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+);"), "%Y-%m-%d %H:%M:%S.%f"),
    (re.compile(r"^\|(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\|"), "%Y-%m-%d %H:%M:%S.%f"),
    (re.compile(r"^(\w{3} \w{3}  ?\d{1,2} \d{2}:\d{2}:\d{2} \d{4}):"), "%a %b %d %H:%M:%S %Y"),
    (re.compile(r"^(\w{3}  ?\d{1,2} \d{2}:\d{2}:\d{2})"), "%b %d %H:%M:%S"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\.\d{3})"), "%Y-%m-%d %H:%M:%S,%f.%f"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^\|(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^(\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \d{4})"), "%a %b %d %H:%M:%S %Y"),
    # New formats
    (re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{1,2})"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})"), "%b %d %H:%M:%S"),
    (re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"), "%Y-%m-%dT%H:%M:%S"),
    (re.compile(r"^<INFO> (\d{1,2}-\w{3}-\d{4}::\d{2}:\d{2}:\d{2}\.\d{3})"), "%d-%b-%Y::%H:%M:%S.%f")
])

def parse_timestamp(line, TIMESTAMP_FORMATS):
    for pattern, datetime_format in TIMESTAMP_FORMATS.items():
        match = pattern.match(line)
        if match:
            try:
                # Extract the timestamp substring based on the match
                timestamp_str = match.group(1)
                # Parse the extracted timestamp string using the corresponding datetime format
                timestamp = datetime.strptime(timestamp_str, datetime_format)
                # Reformat the timestamp
                formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                # Extract the message by removing the timestamp part from the line
                message = line[len(match.group(0)):].strip()
                return formatted_timestamp, message
            except ValueError:
                continue
    # If no format matches, return None for both timestamp and message
    return None, None

def remove_semicolons(message):
    return message.replace(";", "")

def process_lines(lines, change_hour, file_name):
    """Processes the log lines and adjusts timestamps as needed."""
    last_timestamp = None
    processed_lines = []
    
    current_year = datetime.now().year

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        timestamp, message = parse_timestamp(line , TIMESTAMP_FORMATS)
        if timestamp is None:
            continue

        timestamp_tmp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        year = timestamp_tmp.year        
        if year < 2000:
            # Construct a new datetime object with the current year
            updated_timestamp = timestamp_tmp.replace(year=current_year)
            # Convert the updated timestamp back to string format
            timestamp = updated_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f") +'*'

        base_name = os.path.basename(file_name)
        if len(base_name) < 32:
             file_base = base_name.ljust(32, ' ')
        else:
            file_base = base_name[:32]

        clean_message = remove_semicolons(message)

        processed_lines.append(f"{timestamp}  {file_base} {clean_message}\n")
    #break here
    return processed_lines

def save_processed_lines(processed_lines, output_path, file_name):
    """Saves the processed lines to the output directory."""

    if not processed_lines:
        logging.error(f"No processed lines to save for file '{file_name}'.")
        return

    try:
        output_file_name = os.path.basename(file_name)
        output_file_path = os.path.join(output_path, "WIP", output_file_name)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write('\ufeff')  # Write BOM for UTF-8
            output_file.writelines(processed_lines)
        #logging.info(f"Processed lines are saved to {output_file_path}")
    except Exception as e:
        logging.error(f"An error occurred while saving '{file_name}': {e}")


def process_log_file(file_name, change_hour, output_path):
    """Main function to process the log file."""
    lines = read_log_file(file_name)
    if not lines:
        return
    
    processed_lines = process_lines(lines, change_hour, file_name)
    
    
    # Check if all lines start with specified years
    #if any(line.startswith(('2000', '2001', '2135', '2136')) for line in processed_lines):
    #    logging.info("   File has timestamp from before 2020 / after 2135")
    #    processed_lines = fix_2000(lines)
    
    save_processed_lines(processed_lines, output_path, file_name)


def parse_timestamp_from_line(line):
    try:
        return datetime.strptime(line.split()[0], '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None

def fix_2000(file_path):
     # need to add function
    return None

def zcat(input_file):
    output_file = os.path.splitext(input_file)[0]  # Remove .gz postfix
    try:
        subprocess.run(['zcat', input_file], stdout=open(output_file, 'w', encoding='utf-8'), check=True)
    except subprocess.CalledProcessError:
        pass  # Handle error if needed
    return output_file


def get_all_files(expand_tree, last_week_relative=False):
    """
    Recursively retrieves a list of all files in the specified directory and its sub-directories.
    Optionally filters files to include only those modified in the last week relative to the newest file.
    
    :param expand_tree: The path to the directory.
    :param last_week_relative: Boolean flag to filter files modified in the last week relative to the newest file.
    :return: A list of file paths.
    """
    result = []
    latest_mtime = 0

    # First pass to find the latest modification time
    for root, _, filenames in os.walk(expand_tree):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            mtime = os.path.getmtime(file_path)
            if mtime > latest_mtime:
                latest_mtime = mtime

    # Calculate the threshold time (one week before the latest modification time)
    one_week_seconds = 7 * 24 * 60 * 60
    threshold_time = latest_mtime - one_week_seconds

    # Second pass to collect files based on the threshold time
    for root, _, filenames in os.walk(expand_tree):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if not last_week_relative or os.path.getmtime(file_path) >= threshold_time:
                result.append(file_path)

    return result
     

def read_contents_from_files(all_files):
    """
    Reads contents from a list of text files.
    Returns a list of lines from all files.
    """
    all_lines = []
    for file in all_files:
        lines = read_file_content(file)
        if lines is not None:
            all_lines.extend(lines)  # Append lines to the main list
    return all_lines


def detect_encoding(raw_data):
    """
    Detects the encoding of the given raw data.
    here 
    """
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file_content(file):
    """
    Reads the content of a single file, detecting its encoding.
    Returns a list of lines in the file.
    """
    try:
        with open(file, 'rb') as f:
            raw_data = f.read()
            encoding = detect_encoding(raw_data)
            content = raw_data.decode(encoding, errors='replace')
            lines = content.splitlines()  # Split content into lines
            return lines
    except Exception as e:
        logging.error(f"Error reading {file}: {e}")
        return None

    




def update_timestamps_and_filter_lines(content):
    """
    Updates all timestamps in the content to the specified format and removes lines without timestamps.
    """
    tmpline = None

    supported_formats = [
        "%Y-%m-%d %H:%M:%S,%f",   # For '2023-05-23 14:23:15,123'
        "%d-%b-%Y::%H:%M:%S.%f",  # For '23-May-2023::14:23:15.123'
    ]
    target_format = "%Y-%m-%d %H:%M:%S.%f"
    
    timestamp_patterns = [
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)",             # e.g. 2023-05-23 14:23:15,123
        r"<DEBUG> (\d{2}-\w{3}-\d{4}::\d{2}:\d{2}:\d{2}\.\d+)",   # e.g. <DEBUG> 23-May-2023::14:23:15.123
        r"<ERROR> (\d{2}-\w{3}-\d{4}::\d{2}:\d{2}:\d{2}\.\d+)",   # e.g. <ERROR> 23-May-2023::14:23:15.123
        r"<INFO> (\d{2}-\w{3}-\d{4}::\d{2}:\d{2}:\d{2}\.\d+)",    # e.g. <INFO> 23-May-2023::14:23:15.123
    ]

    def parse_and_format_timestamp(line):
        """
        Tries to parse and format the timestamp in the line. Returns None if no valid timestamp is found.
        """
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                for fmt in supported_formats:
                    try:
                        timestamp = datetime.strptime(timestamp_str, fmt)
                        formatted_timestamp = timestamp.strftime(target_format)
                        tmpline = line.replace(timestamp_str, formatted_timestamp)
                        return line.replace(timestamp_str, formatted_timestamp)
                    except ValueError:
                        continue
        return None

    updated_lines = []
    for line in content.splitlines():
        # Parse and format timestamp
        updated_line = parse_and_format_timestamp(line)
        if updated_line:
            # Remove leading spaces and pipes from the line
            updated_line = updated_line.strip().lstrip('|')
            updated_lines.append(updated_line)







    

def reorder_lines(input_file, output_file):
    lines_with_timestamps = []
    lines_without_timestamps = []

    with open(input_file, 'r') as infile:
        for line in infile:
            timestamp= line.strip()
            if timestamp:
                lines_with_timestamps.append((timestamp, line))
            else:
                lines_without_timestamps.append(line)

    # Sort lines with timestamps by timestamp
    sorted_lines = sorted(lines_with_timestamps, key=lambda x: x[0])

    # Write the sorted contents to the output file
    with open(output_file, 'w') as outfile:
        for _, line in sorted_lines:
            outfile.write(line)
#        for line in lines_without_timestamps:
#            outfile.write(line)
#    print(f"Sorted contents written to '{output_file}'.")



def filter_log_by_timestamp(input_file, start_date, end_date, output_file):
    try:
        # Parse start and end dates
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        # Read input file and filter lines
        with open(input_file, 'r') as infile:
            lines = infile.readlines()
            filtered_lines = [
                line for line in lines 
                if start_datetime <= datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S') <= end_datetime
            ]

        # Write filtered lines to output file
        with open(output_file, 'w') as outfile:
            outfile.writelines(filtered_lines)

        print(f"Filtered log saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")

# Example usage:
# filter_log_by_timestamp('input.log', '2023-01-01 00:00:00', '2023-01-31 23:59:59', 'output.log')


# Filter the files - Assuming all_files and normalized_external_files are defined
     
def filter_files(all_files, external_list_of_files ):
    filtered_files = []
    

    for file in all_files:
        if os.path.getsize(file) >= 200: # Ignore samll files <200 Bytes
            if not any(part in file for part in external_list_of_files):
                filtered_files.append(file)
    
    return filtered_files

def filter_files_min(all_files, min_list_of_files):
    filtered_files = []
    

    for file in all_files:
        if os.path.getsize(file) >= 200: # Ignore samll files <200 Bytes
            if any(part in file for part in min_list_of_files):
                filtered_files.append(file)
    
    return filtered_files





def filter_files_by_time(all_files, start_date_str):
    """
    Filters a list of files, returning only those modified after the start_date.
    
    :param all_files: List of file paths to be checked.
    :param start_date_str: The start date as a string in the format "YYYY-MM-DD HH:MM:SS".
    :return: List of files modified after the start_date.
    """
    # Parse the start_date from the provided string
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    
    filtered_files = []
    
    for file_path in all_files:
        try:
            # Get the last modified time of the file
            modification_time = os.path.getmtime(file_path)
            modification_date = datetime.fromtimestamp(modification_time)
            
            # Compare modification date with start_date
            if modification_date > start_date:
                filtered_files.append(file_path)
        except FileNotFoundError:
            # If file is not found, skip it
            continue
        except Exception as e:
            # Handle other exceptions if needed
            print(f"An error occurred with file {file_path}: {e}")
            continue
    
    return filtered_files






def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'.")

def validate_tar_file(path):
    if not os.path.isfile(path) or not path.endswith(".tar.gz"):
        raise argparse.ArgumentTypeError(f"Not a valid .tar.gz file: '{path}'.")
    return path

def validate_directory(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"Not a valid directory: '{path}'.")
    return path

def main():
    parser = argparse.ArgumentParser(description='Process some parameters.')
    
    parser.add_argument('--tar_file', type=validate_tar_file, default='/dt_bug_info/EM-5521/TC03_QosDSCP2EXPmarkingSubinterface-logs-2024.05.12-06.37.39.tar.gz',
                        help='Full path to the .tar.gz file')
    parser.add_argument('--output_path', type=validate_directory, default='/dt_bug_info/danny1/techTool',
                        help='Full path to the output directory')
    parser.add_argument('--expand_tree', type=validate_directory, default='/dt_bug_info/danny1/techTool',
                        help='Full path to expand the logs from')
    parser.add_argument('--change_hour', type=int, default=3,
                        help='Hour adjustment value')
    parser.add_argument('--start_date', type=valid_date, default="1999-01-01 00:00:00",
                        help='Start date in the format YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--end_date', type=valid_date, default="2222-12-31 23:59:59",
                        help='End date in the format YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--log_mode', type=str, default='max',
                        help='which file list to use')

    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)

    print(f"\n\n")
    logging.info(f"Start Execution \n")

    print(f"tar_file: {args.tar_file}")
    print(f"output_path: {args.output_path}")
    print(f"expand_tree: {args.expand_tree}")
    print(f"change_hour: {args.change_hour}")
    print(f"start_date: {args.start_date}")
    print(f"end_date: {args.end_date}")
    print(f"log_mode: {args.log_mode}")

# Define the execution paramters
# tar_file_path = path of tech support log file .tar.gz
# output_path = path to send the output         - os.path.join(os.path.dirname({args.tar_file}), "techTool")
# expand_tree = from what path and down to open the logs
# change_hour = 3  # Change this to the desired hour adjustment
# start_date = start the log from "2024-05-05T14:48:37"
# end_date = "2024-05-05T17:54:50"
# external_list_of_files = List of file/path (in string) to leave out from the collected logs 
# log_mode = max - take all th log. Min - use a prepare listed



    tar_file = str(args.tar_file)
    output_path = str(args.output_path)
    expand_tree = str(args.expand_tree)
    change_hour = str(args.change_hour)  # Change this to the desired hour adjustment
    start_date = str(args.start_date)
    end_date = str(args.end_date)
    log_mode = str(args.log_mode)

    external_list_of_files = [
        "/vbox/cpm_image/root/var/log/exaware.event",
        "lastlog",
        "/vbox/cpm_image/root/var/log/confderr",
        "/vbox/cpm_image/root/var/log/dmes",
        "/vbox/cpm_image/root/var/log/trace/stats_file.csv",
        "/vbox/cpm_image/root/var/log/trace/sysi_output.trace",
        "root/var/log/trace/sysa_output.trace",
        "sys_profile",
        "/vbox/cpm_image/root/var/log/boot*",
        "root/var/log/sysstat/",
        "var/log/mms_stats/",
        "/vbox/cpm_image/root/var/log/sys_profile",
        "/vbox/cpm_image/root/var/log/confd_cupl",
        "/vbox/cpm_image/root/var/log/boot",
        "/vbox/cpm_image/root/var/log/confd_",
        "faillog",
        "-system-info.txt",
        "-cpm-show.txt",
        "-onl_sys-info.txt",
        "wtmp",
        "onl_sys-info.txt",
        "/vbox/cpm_image/root/var/log/card-type/cardtype_cdb_updater-minilog.txt",
        "dmesg",
        "/var/log/monit.log",
        "bcmrm_ingress_sw_counters.bin",
        "/log/bfd/bfd_mo-minilog.txt",
        "/bcmrm_onl_cmd.log",
        "rest_api_server.log",
        "/bootstrap.log",
        "/var/log/fsck",
        "devel"
    # Add more file names as needed
    ]

    min_list_of_files = [
        "/vbox/cpm_image/root/var/log/trace/bgpd",
        "/vbox/cpm_image/root/var/log/trace/fib",
        "/vbox/cpm_image/root/var/log/trace/nsm",
        "/vbox/cpm_image/root/var/log/trace/arp",
        "/vbox/cpm_image/root/var/log/trace/debug_arp",
        "/var/log/bcm",
    # Add more file names as needed
    ]

    # Deleting previous files
    print(f"\n")
    logging.info(f"Delete previous files\n")
    file_name = remove_directory(output_path)

    # Extracting tar file
    logging.info(f"Extracting tar file\n")
    extract_tar_to_folder(tar_file, output_path)

    # Specify the working path WIP under the output_path
    new_subdirectory = "WIP"
    working_path = os.path.join(output_path, new_subdirectory)
    try:
        os.makedirs(working_path, exist_ok=True)
        print(f"New working path created at: {working_path}")
    except OSError as e:
        print(f"Error creating working path: {e}")

    # Get all files in a expand_tree - all / last_week 
    all_files = get_all_files(expand_tree , last_week_relative=False)
    filtered_files_byList = filter_files(all_files, external_list_of_files)
    if log_mode == "min":  
      filtered_files_byList = filter_files_min(filtered_files_byList, min_list_of_files)  

    print(f"\nFilter filed by list")
    for index, file in enumerate(filtered_files_byList, start=1):
        print(f"{index}: {file}")
        
    
    print(f"\nFilter filed by date")
    filtered_files = filter_files_by_time(filtered_files_byList, start_date)
    logging.info(f"List files founded in path {expand_tree} after {start_date}\n ")
    for index, file in enumerate(filtered_files, start=1):
        print(f"{index}: {file}")
        

    for i, file in enumerate(filtered_files):
        # print(f"     {file}")
        # Check if the file contain with ".gz"
        if ".gz" in file:
            new_file = zcat(file)
            filtered_files[i] = new_file

    #print(f"\n")
    #logging.info(f"Updated list of files after file decompression \n")
    #for file in filtered_files:
    #    print(f"     {file}")
        #print(file)

    print(f"\n")
    logging.info(f"Start processing the filtered logs\n\n")
    filtered_files_copy = filtered_files.copy()  # Create a copy to iterate over while modifying original list
    for file in filtered_files_copy:
        if file is None:
            filtered_files.remove(file)
        else:
            print(f"Working on {file}\n")
            process_log_file(file, change_hour, output_path)
            filter_log_by_timestamp(file, start_date, end_date, file+".trimmed")
            filtered_files.remove(file)
            #print_file_content(file)

### break here

    print(f"\n")
    logging.info(f"Create combine file \n")

    all_proccessed_files = get_all_files(working_path , last_week_relative=True)
    # Read contents from all files
    combined_contents = read_contents_from_files(all_proccessed_files)

    # Write combined contents to a new file
    output_combine_file = 'combined_log.txt'
    output_combine_file = Path(output_path) / f"{output_combine_file}"

    with open( output_combine_file , 'w') as output_file:
        output_file.write("\n".join(combined_contents))
    print(f"    Combined contents written to {output_combine_file}.\n")

    logging.info(f"Create Sorted file \n")
    #sort file by timetamp and save file 
    input_file = os.path.join(output_path, 'combined_log.txt')  # Replace with your actual input file
    output_file = os.path.join(output_path,'sorted_log.txt')
    reorder_lines(input_file, output_file)
    print(f"    Sorted list is written to {output_file}.\n")

    logging.info(f"Trimed list is written to {output_file}-Starting from {start_date} & ends by {end_date}.\n")
    #Trim file by start_date, end_date
    input_file = os.path.join(output_path,'sorted_log.txt')
    output_file = os.path.join(output_path,'Trim_sorted_log.txt')
    filter_log_by_timestamp(input_file, start_date, end_date, output_file)

    logging.info(f"END of Execution \n\n\n")
#================================================================================================================

if __name__ == "__main__":
    main()



#Can work also as external script:
# python3.8 techTool.py --tar_file "/home/danny/ws/techTool/FIBMAN_down-logs-2024.05.05-18.06.28.tar.gz" --output_path "/home/danny/ws/techTool/FIBMAN_down" --expand_tree "/home/danny/ws/techTool/FIBMAN_down" --change_hour 5 --start_date "2024-05-05 13:00:00" --end_date "2024-05-05 14:00:00"


# python3.8 techTool.py --start_date "2024-05-05 13:13:00" --end_date "2024-05-05 14:28:00"
# python script_name.py --tar_file "/path/to/your/tar_file.tar.gz" --output_path "/path/to/output" --expand_tree "/path/to/directory" --change_hour 5 --start_date "2024-05-05 12:00:00" --end_date "2024-05-05 13:00:00"

# need to handle:
# time parsing :  time zone , 2000 





