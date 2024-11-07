import platform
import sys
import subprocess
import re
import requests
import os
import shutil
import json
from zipfile import ZipFile
from io import BytesIO
from tqdm import tqdm
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# call this a class
# in download chromedriver
# return variable "service" as path of driver location
# and import this class in webdriver manager, export service object, import in loginclass
# which gets carried into full process
# and add a check to loginclass (maybe?) if it's the correct chromedriver

class SetupDriver:
    def __init__(self):
        self.service = None
            
        if os.path.exists("./chromedriver"):
            self.service = Service(executable_path="./chromedriver")

        else:
            os.makedirs("./chromedriver", exist_ok=True)

# class SetupDriver:
#     def __init__(self):
#         self.service = None
        
#         if os.path.exists("./chromedriver"):
#             self.service = Service(executable_path="./chromedriver")

#         else:
#             os.makedirs("./chromedriver", exist_ok=True)

#     def get_operating_system(self):
#         system = platform.system().lower()
#         if system == "darwin":
#             return "mac"
#         elif system == "windows":
#             return "windows"
#         elif system == "linux":
#             return "linux"
#         else:
#             print(f"Unsupported operating system: {system}")
#             sys.exit(1)

#     def get_chrome_version(self):
#         op_sys = self.get_operating_system()
#         try:
#             if op_sys == "mac":
#                 process = subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], stdout=subprocess.PIPE)
#             elif op_sys == "windows":
#                 process = subprocess.Popen(['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#             elif op_sys == "linux":
#                 process = subprocess.Popen(['google-chrome', '--version'], stdout=subprocess.PIPE)
#             #elif #for streamlit app
#             output, _ = process.communicate()
#             version = re.search(r'\d+\.\d+\.\d+\.\d+', output.decode('utf-8')).group(0)
#             return version
#         except Exception as e:
#             print(f"Error detecting Chrome version: {e}")
#             return None

#     def get_matching_chromedriver_version(self, chrome_version):
#         base_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
#         response = requests.get(base_url)
#         if response.status_code == 200:
#             versions_data = json.loads(response.text)
#             for version_entry in versions_data['versions']:
#                 if version_entry['version'] == chrome_version:
#                     return version_entry['version']
#             print(f"Exact match not found. Searching for closest version...")
#             # If exact match not found, find the closest lower version
#             chrome_version_parts = list(map(int, chrome_version.split('.')))
#             closest_version = None
#             for version_entry in versions_data['versions']:
#                 entry_version_parts = list(map(int, version_entry['version'].split('.')))
#                 if entry_version_parts <= chrome_version_parts and (closest_version is None or entry_version_parts > list(map(int, closest_version.split('.')))):
#                     closest_version = version_entry['version']
#             if closest_version:
#                 print(f"Found closest version: {closest_version}")
#                 return closest_version
#         else:
#             print(f"Failed to fetch ChromeDriver versions. Status code: {response.status_code}")
#         return None

#     def download_chromedriver(self, version, os_type):

#         geo_root = os.path.dirname(os.path.dirname(__file__))

#         if not version:
#             print("No matching ChromeDriver version found.")
#             return False
        
#         base_url = "https://storage.googleapis.com/chrome-for-testing-public"
#         if os_type == "mac":
#             os_string = f"mac-x64" # added new variable to match desired string path format
#             file_name = f"chrome-mac-x64.zip" # testing to match
#         elif os_type == "windows":
#             file_name = f"chromedriver-win32.zip" # may also need to be changed to match
#         elif os_type == "linux":
#             file_name = f"chromedriver-linux64.zip"

#         source_path = os.path.join(geo_root, "chromedriver", file_name.split(".")[0])
#         dest_path = os.path.join(geo_root, "chromedriver")
#         print(dest_path)

#         if not os.path.exists(dest_path): # what if the version is wrong    
#             download_url = f"{base_url}/{version}/{os_string}/{file_name}" #changed os_type to new variable os_name
            
#             print(f"Downloading ChromeDriver from: {download_url}")
#             try:
#                 response = requests.get(download_url, stream=True, timeout=30)
#                 response.raise_for_status()  # Raises an HTTPError for bad requests (4xx or 5xx)
                
#                 total_size = int(response.headers.get('content-length', 0))
#                 block_size = 1024  # 1 KB

#                 with tqdm(total=total_size, unit='iB', unit_scale=True) as progress_bar:
#                     #with open(f"./chromedriver_temp_{file_name}", 'wb') as file:
#                     with open(os.path.join(geo_root, f"chromedriver_temp_{file_name}"), 'wb') as file:
#                         # ideally this points to the correct version
#                         # and then use service to direct to the version
#                         for data in response.iter_content(block_size):
#                             size = file.write(data)
#                             progress_bar.update(size)
                
#                 print("ChromeDriver downloaded successfully.")
                
#                 #with ZipFile(f"./chromedriver_temp_{file_name}", 'r') as zip_ref:
#                 with ZipFile(os.path.join(geo_root, f"chromedriver_temp_{file_name}"), 'r') as zip_ref:
#                     #zip_ref.extractall("./chromedriver")
#                     zip_ref.extractall(os.path.join(geo_root, "chromedriver"))
                
#                 #source_path = f"./chromedriver/{file_name.split(".")[0]}"
#                 #dest_path = "./chromedriver"
                
#                 shutil.move(source_path, dest_path)
#                 os.removedirs(source_path)
#                 print(f"ChromeDriver moved to: {dest_path}")
#                 if os_type != "windows":
#                     os.chmod(dest_path, 0o755)  # Make executable on Unix-like systems
#                     print("ChromeDriver permissions updated.")

#                 #os.remove(f"./chromedriver_temp_{file_name}")
#                 os.remove(os.path.join(geo_root, f"chromedriver_temp_{file_name}"))

#                 print("ChromeDriver extracted successfully.")
#                 #self.service = Service(executable_path="./chromedriver")
#                 self.service = Service(executable_path=os.path.join(geo_root, "chromedriver"))

#                 return True
#             except requests.exceptions.RequestException as e:
#                 print(f"Error downloading ChromeDriver: {e}")
#                 return False
#         else:
#             print("Driver already downloaded.")
    
#     def setup_webdriver(self):
#         os_type = self.get_operating_system()
#         chrome_version = self.get_chrome_version()
#         closest_version = self.get_matching_chromedriver_version(chrome_version)
#         self.download_chromedriver(closest_version, os_type)


# can skip this
'''
def move_chromedriver(os_type):
    # Find the chromedriver file
    if os_type == "mac":
        source_path = glob.glob("./chrome-mac-x64/**/chromedriver", recursive=True)
    elif os_type == "windows":
        source_path = glob.glob("./chrome-win32/**/chromedriver.exe", recursive=True)
    elif os_type == "linux":
        source_path = glob.glob("./chrome-linux64/**/chromedriver", recursive=True)
    else:
        raise ValueError(f"Unsupported OS type: {os_type}")

    if not source_path:
        raise FileNotFoundError("ChromeDriver not found in the expected location.")
    
    source_path = source_path[0]  # Take the first match

    # Set destination path to user's home bin directory
    home_dir = os.path.expanduser("~")
    bin_dir = os.path.join(home_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)  # Create bin directory if it doesn't exist
    
    dest_path = os.path.join(bin_dir, "chromedriver")
    if os_type == "windows":
        dest_path += ".exe"

    try:
        shutil.move(source_path, dest_path)
        print(f"ChromeDriver moved to: {dest_path}")
        if os_type != "windows":
            os.chmod(dest_path, 0o755)  # Make executable on Unix-like systems
            print("ChromeDriver permissions updated.")
    except Exception as e:
        print(f"Error moving ChromeDriver: {e}")
        print("You may need to run this script with administrator/root privileges.")
    
    # Clean up temporary directory
    chrome_dir = os.path.dirname(os.path.dirname(source_path))
    shutil.rmtree(chrome_dir)

    # Don't forget to update your PATH
    print(f"Please add {bin_dir} to your PATH if it's not already there.")
    print("You can do this by adding the following line to your ~/.bash_profile or ~/.zshrc:")
    print(f"export PATH=\"{bin_dir}:$PATH\"")
     '''

# Main execution
'''
setup = SetupDriver()

os_type = setup.get_operating_system()
print(f"Detected operating system: {os_type}")

chrome_version = setup.get_chrome_version()
if chrome_version:
    print(f"Detected Chrome version: {chrome_version}")
    chromedriver_version = setup.get_matching_chromedriver_version(chrome_version)
    if chromedriver_version:
        print(f"Matching ChromeDriver version: {chromedriver_version}")
        if setup.download_chromedriver(chromedriver_version, os_type):
            #move_chromedriver(os_type)
            print("downloaded")
    else:
        print("Failed to find a matching ChromeDriver version. Please ensure you have the latest version of Chrome installed.")
else:
    print("Could not detect Chrome version. Please ensure Chrome is installed and you have the latest version.")
service = setup.service
wd = webdriver(service=service)

'''