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

from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download
from geography.classes.SearchClass import newsearch

from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, ElementNotInteractableException,
    StaleElementReferenceException, ElementClickInterceptedException)

# this part gets the count from result page and creates ranges in download limit
def get_ranges(download, download_folder):
    
    # get full count from site
    full_count = download.get_result_count() 
    
    # hard-coding limit of 500 to it because that's the nexis uni limit for word full text
    download_limit = 500 

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
    def __init__(self, download, username, basin_code, download_folder, download_folder_temp):
        """
        REMOVED: userclass parameter - now accepting individual parameters
        """
        self.download = download
        self.username = username  # Consistent naming
        self.basin_code = basin_code
        self.download_folder = download_folder
        self.download_folder_temp = download_folder_temp
    
    def download_dialog(self, r):
        
        self.open_download_options = "//button[@data-action='downloadopt' and @aria-label='Download']"
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
                    WebDriverWait(self.download.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self.result_range_field)))                        
                    break  # Exit the loop if successful

                except (NoSuchElementException, TimeoutException):
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        print(f"Attempt {attempt + 1} failed to open download window, retrying in 10 seconds")
                        time.sleep(10)
                        self.download._click_from_xpath(self.open_download_options)  # Try opening the download options again
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
        matching_files = [f for f in os.listdir(self.download_folder_temp) if re.match(default_download_pattern, f)]
        
        if matching_files:  # If any matching files found
            print("There's an unsorted file in downloads")
            self.create_unsorted_folder(r)
            self.move_unsorted(r, matching_files[0])  # Pass the filename to move_unsorted

    def create_unsorted_folder(self, r):
        self.unsorted_folder = Path(f"{self.download_folder}/{self.basin_code}_unsorted")
        if not os.path.exists(self.unsorted_folder):
            print(f"Creating unsorted folder {self.unsorted_folder}")
            os.makedirs(self.unsorted_folder)

        print("+" * 48)
        print(f"Check unsorted download found in range {r}")
        print("+" * 48)

    def move_unsorted(self, r, original_filename):
        # Use the original file's full path
        original_path = os.path.join(self.download_folder_temp, original_filename)
        
        unsorted_filename = f"foundinrange_{r}.ZIP"
        unsorted_moved_path = os.path.join(self.unsorted_folder, unsorted_filename)
        
        os.rename(original_path, unsorted_moved_path)
        print(f"File {unsorted_filename} moved to {self.basin_code} download folder")