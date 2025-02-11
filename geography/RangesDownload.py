import os
import time
import csv
from datetime import datetime
from pathlib import Path
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys 

from geography.classes.UserClass import UserClass
from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download
from geography.classes.SearchClass import newsearch

from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, ElementNotInteractableException,
    StaleElementReferenceException, ElementClickInterceptedException)

# basin_code = "gash"
# master_user = "selena"
# download_type = "pdf"

# start_date = '06/30/2008'
# end_date = '06/30/2024'

# currentUser = UserClass(basin_code, master_user, download_type)

# paths = currentUser.getPath(download_type) # returns paths as dicts

# base_path = paths['base_path']
# user_name = paths["user_name"]
# geography_folder = paths["geography_folder"]
# download_folder_temp = paths["download_folder_temp"]
# download_folder = paths["download_folder"]
# status_file = paths["status_file"]

# if os.path.exists(download_folder):
#     print(f"{basin_code}/{download_type} folder already exists")
# else:
#     os.makedirs(download_folder, exist_ok=True) # this isn't exactly right is it? - Yes, I added exists_ok=True to avoid errors if the folder already exists
#     print(f"created folder {basin_code}/{download_type}")

# generic_status_path = f"{geography_folder}data/status/pdf/new_status.csv" # this is a blank df
# # this file will need to be in the repository until we've updated download class to not use status_file
# if os.path.exists(status_file): # though in the future we'll want to just not call in status_file
#     pass
# else:
#     status_file = generic_status_path # if it doesn't exist, just use the blank one...

# pm = PasswordManager()
# if not pm.password:
#     print("No password found, please enter your password")
#     pm.get_password()
#     print("Password saved successfully")
# else: pass

# manager = WebDriverManager(paths)
# #options = manager.setup_options() # not using this ?
# driver = manager.start_driver()

# time.sleep(5)
# login = Login(user_name=user_name, password=pm.password, driver_manager=manager, url=None)

# login._init_login()

# nlc = NoLinkClass(driver, basin_code, download_type, currentUser) 
# download = Download(
#     driver=driver,
#     basin_code=basin_code,
#     user_name=user_name,
#     index=0,  
#     login = login,
#     nlc = nlc,
#     download_folder = download_folder,
#     download_folder_temp = download_folder_temp,
#     status_file=status_file,
#     finished=False,  
#     url=None,  
#     timeout=20 ,
#     download_type='pdf')

# time.sleep(5)

# search = newsearch(nlc, download)
# search.search(start_date, end_date)

# time.sleep(5)
# download.DownloadSetup()

# this part gets the count from result page and creates ranges in download limit
def get_ranges(download, download_folder, download_type='pdf'):

    # get full count from site
    full_count = download.get_result_count(index=0) # this uses a method in download class, but in future iterations shouldn't need an index (no status sheet)

    # this part may not matter, can hard code 500 into it

    if download_type == 'pdf':
        download_limit = 500 # adding this because it may change but for pdf is 500

    else:
        download_limit = 1000 # probably not necessary

    # this generates a list of ranges that will be used in the download dialog box

    ranges = []
    for i in range(1, full_count, download_limit):
        end = min(i + (download_limit - 1), full_count)
        ranges.append(f"{i}-{end}")

    # this matches downloaded files to the ranges
    downloaded_ranges = [f.split("_")[-1].replace(".ZIP", "") for f in os.listdir(download_folder) if f.endswith(".ZIP")]

    # this compares those lists and creates a new list of ranges to be downloaded
    not_downloaded_ranges = sorted(list(set(ranges)^set(downloaded_ranges)), key=lambda x: int(x.split('-')[0]))
    return not_downloaded_ranges


class dialog:
    def __init__(self, download, userclass):
        self.download=download
        self.userclass = userclass
    
    def download_dialog(self, r):
        
        self.open_download_options = "//button[@class='has_tooltip' and @data-action='downloadopt']"
        self.result_range_field = "//input[@id='SelectedRange']"

        try:
            time.sleep(2)
            self.download._click_from_xpath(self.open_download_options)
            time.sleep(2)

        except (ElementClickInterceptedException, StaleElementReferenceException):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # check if we're in dialog box, looking for result range field
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self.result_range_field)))                        
                    break  # Exit the loop if successful

                except (NoSuchElementException, TimeoutException):
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed to open download window, retrying in 10 seconds")
                        time.sleep(10)
                        self._click_from_xpath(self.open_download_options)  # Try opening the download options again
                        time.sleep(2)
                    else:
                        print("could not open dialog box, will reset login")
                        self.download.reset()
                        # and then try to click again
                        time.sleep(2)
                        self.download._click_from_xpath(self.open_download_options)
                        time.sleep(2)

        # enter range once we're in dialog box
        self.download._send_keys_from_xpath(self.result_range_field, r) # ensure r is set somewhere

        # click MS word option
        MSWord_option = "//input[@type= 'radio' and @id= 'Docx']"
        self.download._click_from_xpath(MSWord_option)

        separate_files_option = "//input[@type= 'radio' and @id= 'SeparateFiles']"
        self.download._click_from_xpath(separate_files_option)

        # click on download
        download_button = "//button[@type='submit' and @class='button primary' and @data-action='download']"
        self.download._click_from_xpath(download_button)

    def check_clear_downloads(self, r): 
        # Find file matching pattern
        default_download_pattern = r"Files \(\d+\)\.ZIP"
        matching_files = [f for f in os.listdir(self.userclass.download_folder_temp) if re.match(default_download_pattern, f)]
        
        if matching_files:  # If any matching files found
            print("There's an unsorted file in downloads")
            self.create_unsorted_folder(r)
            self.move_unsorted(r, matching_files[0])  # Pass the filename to move_unsorted

    def create_unsorted_folder(self, r):
        self.unsorted_folder = Path(f"{self.userclass.download_folder}/{self.userclass.basin_code}_unsorted")
        if not os.path.exists(self.unsorted_folder):
            print(f"Creating unsorted folder {self.unsorted_folder}")
            os.makedirs(self.unsorted_folder)

        print("+" * 48)
        print(f"Check unsorted download found in range {r}")
        print("+" * 48)

    def move_unsorted(self, r, original_filename):
        # Use the original file's full path
        original_path = os.path.join(self.userclass.download_folder_temp, original_filename)
        
        unsorted_filename = f"foundinrange_{r}.ZIP"
        unsorted_moved_path = os.path.join(self.unsorted_folder, unsorted_filename)
        
        os.rename(original_path, unsorted_moved_path)
        print(f"File {unsorted_filename} moved to {self.userclass.basin_code} download folder")

# dialog = dialog(download) # make sure to change this, maybe to "dialog_box"

# #have to do this each time to reset the list based on what's in the downloaded folder
# ranges_to_download = get_ranges() 

# # and this is the process
# for r in ranges_to_download:
#     dialog.check_clear_downloads(r) # and these will need to be dialog_box... as well
#     dialog.download_dialog(r) # ibid ^ dialog_box...
#     print(f"preparing to download range {r}")

#     download.wait_for_download()
    
#     # Find matching file
#     default_filename = [f for f in os.listdir(download_folder_temp) if re.match(r"Files \(\d+\)\.ZIP", f)]

#     if default_filename:  # If we found any matching files
#         # Use the first matching file
#         default_download_path = os.path.join(download_folder_temp, default_filename[0])
#         geography_download_path = f"{download_folder}{basin_code}_results_{r}.ZIP"

#         # Check if file exists and move it
#         if os.path.isfile(default_download_path):
#             os.rename(default_download_path, geography_download_path)
#             print(f"moving file to {geography_download_path}")

#     download.reset()

# ranges_to_download = get_ranges() # run this again when loop is complete

# # get_ranges() will return not_downloaded_ranges as a list

# if not ranges_to_download:
#     print("all ranges for basin downloaded")

# else:
#     print("ranges remaining:")
#     print(ranges_to_download)