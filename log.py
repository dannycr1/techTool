import subprocess

def zcat_and_redirect(input_file, output_file):
    try:
        # Use zcat to extract the content and redirect it to the output file
        subprocess.run(["zcat", input_file], stdout=open(output_file, 'w'), check=True)
        print(f"File extracted using zcat and saved to {output_file}")
    except subprocess.CalledProcessError:
        print(f"Error extracting file using zcat. File '{input_file}' cannot be read or opened.")

# Example usage:
input_file_name = "/home/danny/ws/techTool/FIBMAN_down/vbox/cpm_image/root/var/log/trace/aaad_trace_buffer.trace.gz"
output_file_name = "/home/danny/ws/techTool/FIBMAN_down/aaad_trace_buffer.trace"
zcat_and_redirect(input_file_name, output_file_name)



import datetime
from pathlib import Path

# Example working path and file name
working_path = r'C:\Users\username\Documents\folder1\folder2'
filename = 'AG' + datetime.date.today().strftime("%m%d%Y")

# Construct the full file path
output_file = Path(working_path) / f"{filename}.csv"

print(output_file)  # C:\Users\username\Documents\folder1\folder2\AG05072020.csv
