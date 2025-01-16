from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
# is all this above only useful in full process?

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys 
from datetime import datetime

from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, 
    ElementClickInterceptedException, ElementNotInteractableException, 
    NoSuchElementException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from pathlib import Path

import pandas as pd
import time
import sys
import os

#sys.path.append("..") #I'm not sure if I need this

from classes.LoginClass import Login
from classes.NoLinkClass import NoLinkClass
#from classes.conversions.combine_results import CombineResults
#from geography.classes.conversions.status_excel_to_pdf import convert_pdf

class ResetRequiredException(Exception):
    pass

class SkipRowException(Exception):
    pass

class SingleResultException(Exception):
    pass

class Download:

    def __init__(self, driver, basin_code, user_name, index, login, nlc, download_type, download_folder: str, download_folder_temp, status_file, finished, url = None, timeout = 20):
        self.driver = driver
        self.basin_code = basin_code
        self.user_name = user_name
        self.index = index
        self.login = login
        self.nlc = nlc
        self.download_type = download_type
        self.status_file = status_file
        self.finished = finished 
        self.url = url
        self.timeout = timeout
        self.download_folder = download_folder
        self.download_folder_temp = download_folder_temp 
        
        #Set Basin Status CSV File 
        if os.path.exists(status_file):
            self.status_data = pd.read_csv(status_file, index_col=0)
        else:
            df = pd.DataFrame()
            df.to_csv(status_file)
            self.status_data = pd.read_csv(status_file, index_col=0)
        #self.result_tally = 0  # initialize it at 0
    
    def _click_from_xpath(self, xpath):
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
        except TimeoutException:
            raise NoSuchElementException(f"Element with xpath '{xpath}' not found")

    def _send_keys_from_xpath(self, xpath, keys):
        wait = WebDriverWait(self.driver, self.timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath))) 
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        element.send_keys(keys)

    def _click_from_css(self, css_selector):
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
            )
            element.click()
        except TimeoutException:
            raise NoSuchElementException(f"Element with selector '{css_selector}' not found")

       
    def _send_keys_from_css(self, css_selector, keys):
        element = WebDriverWait(self.driver, self.timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(keys)

    def open_timeline(self):
        timeline_button = '#podfiltersbuttondatestr-news' # this is CSS selector
        self._click_from_css(timeline_button)
        time.sleep(10)
        # instead try with XPath
        #wait = WebDriverWait(driver, 10)
        #timeline_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/main/ln-gns-resultslist/div[2]/div/div[1]/div[1]/div[2]/div/aside/button[2]")))
        #timeline_button.click()
        #time.sleep(5)

    def parse_date(self, date_string):
        date_formats = [
            '%m/%d/%y',  # 8/1/08
            '%m/%d/%Y',  # 8/1/2008
            '%Y-%m-%d',  # 2008-08-01
            '%d-%m-%Y',  # 01-08-2008
            '%Y/%m/%d',  # 2008/08/01
            # Add more formats as needed
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_string, date_format)
            except ValueError:
                continue
        
        # If no format worked, raise an error
        raise ValueError(f"Unable to parse date string: {date_string}")
        # this would be a good place to add an exception
        #and then maybe add in a skip/break of the loop, move to next index #
        
    def set_date_range(self, index):

        #START_DATE AND END_DATE get established here
        row = self.status_data.index.get_loc(index)
        start_date_column = self.status_data.columns.get_loc('start_date')
        end_date_column = self.status_data.columns.get_loc('end_date')

        self.start_date_raw = self.status_data.iloc[row, start_date_column]
        self.end_date_raw = self.status_data.iloc[row, end_date_column]

        try:
            start_date_str = self.parse_date(self.start_date_raw)
            end_date_str = self.parse_date(self.end_date_raw)
        except ValueError as e:
            print(f"Error parsing dates for index {index}: {e}")
            return

        self.start_date = start_date_str.strftime('%m/%d/%Y')
        self.end_date = end_date_str.strftime('%m/%d/%Y')

        print(f"Setting the date range from {self.start_date} to {self.end_date}")
        time.sleep(1)
              
        # these are css selectors
        #self.min_date_field = '#refine > div.supplemental.timeline > div.date-form > div.min-picker > input'
        #self.max_date_field = '#refine > div.supplemental.timeline > div.date-form > div.max-picker > input'
        
        # trying again with xpaths instead of css selector
        self.min_date_field = "//input[@class='min-val' and @aria-label='Input Min Date']"
        self.max_date_field = "//input[@class='max-val' and @aria-label='Input Max Date']"

        # need to include error handling for when timeline freezes, see what David did
        
        try:
            self._click_from_xpath(self.min_date_field)
            
        except NoSuchElementException:
            print('timeline closed or frozen')
            self.open_timeline()
            time.sleep(5)

        # Clear out the default min date
        time.sleep(5)
        self.select_all = Keys.COMMAND, "a"
        #self._send_keys_from_css(min_date_field, select_all); 

        # try with xpath
        self._send_keys_from_xpath(self.min_date_field, self.select_all); 
        # Put the new min date in 
        self._send_keys_from_xpath(self.min_date_field, self.start_date)
        print (f"Min date set to {self.start_date}")
        time.sleep(3)

        # Clear out the default max date 
        self._send_keys_from_xpath(self.max_date_field, self.select_all); 
        # Put the new max date in 
        self._send_keys_from_xpath(self.max_date_field, self.end_date)
        print (f"Max date set to {self.end_date}")
        time.sleep(3)

        timeline_ok_button = '#refine > div.supplemental.timeline > div.date-form > button'

        try:
            self._click_from_css(timeline_ok_button)
            time.sleep(10) 
        except NoSuchElementException:
            self.driver.refresh()
            print (f"resetting dates to default")
            raise SingleResultException
        
    def check_datefilter(self):
        self.timeline_reset_button = '#sidebar > div.search-controls > div.filter-container.filterpanel-target > ul > li:nth-child(2) > button > span'
        try:
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, self.timeline_reset_button)))
            #print("results already have a timeline filter applied")
            return True
        except TimeoutException:
            #print("no timeline filter applied to results")
            return False

    def timeline_reset(self): 
        
        if self.check_datefilter():
            self._click_from_css(self.timeline_reset_button)
            print("Cleared previous timeline filter")
            time.sleep(10)
        else:
            #print("Default time filter")
            self.open_timeline()

    def group_duplicates(self):
        actions_dropdown_xpath = "//button[@id='resultlistactionmenubuttonhc-yk' and text()='Actions']"
        time.sleep(5)
        self._click_from_xpath(actions_dropdown_xpath)
        time.sleep(5)
        moderate_button = "//button[contains(@class, 'action') and @data-action='changeduplicates' and @data-value='moderate']"
        self._click_from_xpath(moderate_button)
        print("group duplicate results by moderate similarity")
        time.sleep(10)
    
    def sort_by_date(self):
        sortby_dropdown_css = '#select'
        oldestnewest_option_text = 'Date (oldest-newest)'
            
        def handle_popup():
            analytics_popup = "//button[@class='_pendo-close-guide' and @aria-label='Close' and contains(@id, 'pendo-close-guide')]"
            try:
                popup_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, analytics_popup))
                )
                popup_element.click()
                print("Popup closed")
                time.sleep(2)
            except TimeoutException:
                print("No popup found") 

        for attempt in range(3):  # Try up to 3 times
            try:
                # Check for and close popup before interacting with dropdown
                handle_popup()

                # Wait for the dropdown to be clickable
                dropdown = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sortby_dropdown_css))
                )
                
                # Use Select class to interact with the dropdown
                select = Select(dropdown)
                select.select_by_visible_text(oldestnewest_option_text)
                
                print("Selected 'Date (oldest-newest)' option")
                time.sleep(5)  # Wait for the page to update
                return  # Success, exit the function
                
            except StaleElementReferenceException:
                print("Stale element, retrying...")
                time.sleep(2)
                continue
                
            except (TimeoutException, NoSuchElementException):
                print(f"Attempt {attempt + 1}: Can't find sort-by dropdown, refreshing the page")
                self.driver.refresh()
                time.sleep(5)
                continue
                
            except ElementClickInterceptedException:
                print("Popup is in the way, attempting to close it")
                handle_popup()
                continue
                
            except ElementNotInteractableException:
                print("Element not interactable, attempting to close popup if present")
                handle_popup()
                continue
        
        print("Failed to sort by date after multiple attempts")


    def DownloadSetup(self):
        self.group_duplicates()
        self.sort_by_date()

    def get_result_count(self, index, max_attempts=3):
       for attempt in range(max_attempts):
            try:
                # Wait for the element to be present
                count_element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#sidebar > div.search-controls > div.content-type-container.isBisNexisRedesign > ul > li.active"))
                )
                
                # Wait for the attribute to be non-empty
                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: count_element.get_attribute("data-actualresultscount") != ""
                )
                
                result_count_element = count_element.get_attribute("data-actualresultscount")
                self.result_count = int(result_count_element)
                return self.result_count

            except TypeError:
                print("Result count type error, waiting 20s for count to appear")
                time.sleep(20)
                continue

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    print("Refreshing page and retrying...")
                    self.driver.refresh()
                    time.sleep(5)  # Wait for page to reload
                else:
                    print("Max attempts reached. Could not retrieve result count.")
                    if self.download_type == 'excel':
                        self.status_data.loc[index, 'basin_count'] = None
                    else:
                        self.status_data.loc[index, 'total_count'] = None
                    self.status_data.to_csv(self.status_file)
                    return None

            except ValueError as e:
                print(f"Error converting result count to integer: {str(e)}")
                if self.download_type == 'excel':
                    self.status_data.loc[index, 'basin_count'] = None
                else:
                    self.status_data.loc[index, 'total_count'] = None
                self.status_data.to_csv(self.status_file)
                return None
                
    def result_count_to_df(self, index):
               
        if self.download_type == 'excel':
            # Update status data and return result
            self.status_data.loc[index, 'basin_count'] = self.result_count
            self.status_data.to_csv(self.status_file)
            print(f"row {index} updated with {self.result_count} results in date range")
            return self.result_count

        else: #if self.download_type == 'pdf':
            self.start_count = self.status_data.loc[index, 'start_count']
            self.stop_count = self.status_data.loc[index, 'stop_count']

            # if the range of results exceeds results to be downloaded in this row
            if self.result_count > self.stop_count:
                self.file_count = int((self.stop_count - self.start_count) + 1)
                self.status_data.loc[index, 'total_count'] = self.file_count
                print(f"row {index} updated with {self.file_count} results to be downloaded")
                self.status_data.to_csv(self.status_file)
                
            else: # if the results end in this row / result_count is lower than stop_count
                # update end count
                self.file_count = int((self.result_count - self.start_count) + 1)
                self.status_data.loc[index, 'total_count'] = self.file_count
                #self.status_data.loc[index, 'stop_count'] = self.result_count
                print(f"row {index} updated with {self.file_count} results to be downloaded")
                self.status_data.to_csv(self.status_file)

                if self.result_count < 501:
                    self.next_row = index + 1
                    print(f"row {index} includes all results in date range")
                    print(f"updating row {self.next_row} status to automatically skip")
                    self.status_data.loc[self.next_row, 'total_count'] = 0
                    self.status_data.loc[self.next_row, 'finished'] = 1
                    #self.status_data.loc[next_row, 'start_count'] = 0
                    #self.status_data.loc[next_row, 'stop_count'] = 0
                    self.status_data.to_csv(self.status_file)

                else:
                    pass

            # add a bit of over_thousand-ing here ??
            #if self.result_count > 1000:
                # add row to the end of the dataframe
                # and this is the code for like changing a cell
                #self.status_data.loc[index, 'basin_count'] = self.result_count
                #self.status_data.to_csv(self.status_file)


    
    def result_count_handling(self, index):

        if self.result_count < 1000:
            self.result_count_to_df(index)        

        else:
            # If result count is 1000 or more, check one more time
            print("Result count is 1000 or more. Checking again...")
            time.sleep(5)  # Wait a bit before checking again

            if not self.check_datefilter():
                print("timeline isn't filtered")
                self.DateFilter(index)

            else:
                print('result_count is over one thousand')
            # Repeat the process to get the count again
            count_element = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#sidebar > div.search-controls > div.content-type-container.isBisNexisRedesign > ul > li.active"))
            )
            result_count_element = count_element.get_attribute("data-actualresultscount")
            self.result_count = int(result_count_element)
            print(f"Second check result count for row {index} is {self.result_count}")

            if self.result_count < 1000:
                self.result_count_to_df(index) 

            else:
                self.DateFilter(index)    
                time.sleep(5)
                
                if self.result_count < 1000:
                    self.result_count_to_df(index) 
                else:
                    # If still 1000 or more, update status data and raise SkipRowException
                    if self.download_type == 'excel':
                        self.status_data.loc[index, 'basin_count'] = self.result_count
                    else:
                        self.status_data.loc[index, 'total_count'] = self.result_count
                    self.status_data.loc[index, 'over_one_thousand'] = 1
                    self.status_data.to_csv(self.status_file)
                    raise SkipRowException(f"Result count is still {self.result_count} after third check.")


    def DateFilter(self, index):

        if self.check_datefilter():
            print("need to clear date filter")
            self.timeline_reset() 

        print("Setting new date range")
        try:
            self.set_date_range(index)
            
        except NoSuchElementException:
            self.open_timeline()
            self.set_date_range(index)

        try:
            self.get_result_count(index)
            self.result_count_handling(index)

        except SkipRowException:
            raise
            #end the loop, go to next one

    def ExcelSegments(self):
        # we just want headline, summary, publication, date
        self.checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
        self.keep_checked_ids = ['HEA', 'PUB', 'PDT'] # headline, publication, published date
        # Scroll into view and uncheck each checkbox if it is checked
        for checkbox in self.checkboxes:
            id = checkbox.get_attribute('id')
            try:    
                if checkbox.is_selected() and id not in self.keep_checked_ids:
                    ActionChains(self.driver).move_to_element(checkbox).perform()
                    checkbox.click()
            except Exception as e:
                #print(f"Error processing checkboxes: {e}")
                #print(f"Error processing checkboxes") # terminal looks messy printing the whole error but I can keep this if necessary
                pass
        print("unchecked unnecessary columns")

    def get_filename(self, index):
        if self.download_type == 'excel':
            self.filename = f'ResultsList_{self.basin_code}_index{index}'
            return self.filename
        else:
            self.filename = f'FullText_{self.basin_code}_index{index}'
            return self.filename

    def excelDownloadOptions(self):
    
        results_list_option = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable
                            ((By.XPATH, "//input[@type='radio' and @id='ResultsListOnly']")))
        results_list_option.click()
        print("choose resultslist download type")
        
        #self.result_list_field = '#SelectedRange' #css
        #self.result_list_field = '//*[@id="SelectedRange"]' #xpath copied
        #self.result_list_field = "//input[@type='text' and @id='SelectedRange']" #xpath my guess

        try:
            self.result_range_string = f"1-{self.result_count}"
            print(f"Results {self.result_range_string}")
            time.sleep(2)
        except SingleResultException:
            self.result_range_string = f"{self.result_count}"
            print(f"Only one result to download")
            time.sleep(2)

        # put in results count to download
        self._send_keys_from_xpath(self.result_range_field, self.result_range_string)
        
        self.filetype_excel_option = "//input[@type='radio' and @id='XLSX']"
        print("choose excel option")
        self._click_from_xpath(self.filetype_excel_option)
        time.sleep(2)

        # un-select unnecessary columns
        self.ExcelSegments()
        time.sleep(2)

    def pdfDownloadOptions(self, index):
            #status_data... unless it's defined outside the class??
            #self.start_count = self.status_data.loc[index, 'start_count']
            #self.stop_count = self.status_data.loc[index, 'stop_count']
            try:
                string_end_count = (self.start_count - 1) + self.file_count
                self.result_range_string = f"{self.start_count}-{string_end_count}"
                print(f"Results {self.result_range_string}")
                time.sleep(2)

            except SingleResultException:
                self.result_range_string = f"{self.result_count}"
                print(f"Only one result to download")
                time.sleep(2)  

            MSWord_option = "//input[@type= 'radio' and @id= 'Docx']"
            self._click_from_xpath(MSWord_option)

            separate_files_option = "//input[@type= 'radio' and @id= 'SeparateFiles']"
            self._click_from_xpath(separate_files_option)

            #zip_option = "//input[@type= 'checkbox' and @id= 'ZipFile']"
            #self._click_from_xpath(zip_option) # it's selected by default when saving individual files
            time.sleep(2)

            self._send_keys_from_xpath(self.result_range_field, self.result_range_string)
            time.sleep(2)

    def DownloadDialog(self, index):
        open_download_options = "//button[@class='has_tooltip' and @data-action='downloadopt']"
        self._click_from_xpath(open_download_options)
        time.sleep(5) 

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Wait for the element to be clickable
                self.result_range_field = "//input[@id='SelectedRange']"
                
                # <input type="text" id="SelectedRange" name="SelectedRange" class="" placeholder="Enter one or more row ranges to export.">

                # check if we're in the dialog box by looking for clickable field button
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self.result_range_field)))
                                                     
                break  # Exit the loop if successful

                # can i change this to like
                #if results_list_option:
                #   results_list_option.click()

            except (NoSuchElementException, TimeoutException):
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed to open download window, retrying in 10 seconds")
                    time.sleep(10)
                    self._click_from_xpath(open_download_options)  # Try opening the download options again
                    time.sleep(5)
                else:
                    print("download limit banner appeared, need to reset login")
                    self.reset_needed = True
                    raise ResetRequiredException()

        if self.download_type == 'excel':
            self.excelDownloadOptions(index)

        else:
            self.pdfDownloadOptions(index)
        
        # rename file name
        self.filename_field = "//input[@type='text' and @id='FileName']"
        self._send_keys_from_xpath(self.filename_field, (Keys.COMMAND, "a"))
        self.filename = self.get_filename(index)
        print(f'changing filename to {self.filename}')
        self._send_keys_from_xpath(self.filename_field, self.filename)
        print(f"{self.download_folder_temp}")
        self.check_clear_downloads(index)
        time.sleep(5)
        self.click_download(index)

        #I actually forget where all of this came from 
        '''
        try:
            # Your existing pre-download steps
            # (like clicking buttons, setting up the download, etc)
            
            # Use our new download handler for the actual download
            if not self.download_handler.process_download(index):
                raise SkipRowException("Download failed")
                
            # Update status if successful
            self.status_data.at[index, 'finished'] = 1
            
        except Exception as e:
            print(f"Error in download process: {str(e)}")
            #self.reset_needed = True
            raise SkipRowException("Error during download")
        '''
    def check_clear_downloads(self, index): # for a manual check
        #if file in default_download contains the name "Files (" move it to a folder
        self.default_download_name = f"Files ({self.file_count}).ZIP"
        self.unsorted_past_download = f"{self.download_folder_temp}/{self.default_download_name}"
        if os.path.exists(os.path.join(self.download_folder_temp, self.default_download_name)):
            print(f"there's an unsorted file matching {self.default_download_name} name in downloads")
            self.create_unsorted_folder(index)
            self.move_unsorted()
        # or can do regular expression with just "Files ("
        #
        #self.create_unsorted_folder(index)
        # if self.unsorted_past_download.is_dir():
        #     print(f"there's an unsorted file matching {self.default_download_name} name in downloads")

        #     self.move_unsorted()
        # else:
        #     print("didn't find a matching file")
        #     pass


    def create_unsorted_folder(self, index):
        self.unsorted_folder = Path(f"{self.download_folder}/{self.basin_code}_unsorted_foundindex{index}") # in default download
        if self.unsorted_folder.is_dir():
            pass

        else:
            print(f"creating unsorted folder {self.unsorted_folder}")
            os.makedirs(self.unsorted_folder)

        print(f"to move missing download {self.unsorted_past_download}: check status sheet before index {self.index} for matching file count and check file header for date range to confirm")

    def move_unsorted(self):
        unsorted_moved_path = f"{self.unsorted_folder}/{self.default_download_name}"
        os.rename(self.unsorted_past_download, unsorted_moved_path)
        print(f"file {self.filename} in {self.basin_code} download folder")

    def click_download(self, index): 

        # check for a file in downloads with the naming convention and handle it!!
        # maybe move it to a folder called "incomplete_discovered_index12"

        try:
            self.download_button = "//button[@type='submit' and @class='button primary' and @data-action='download']"
            self._click_from_xpath(self.download_button)
            print(f"downloading {self.filename}")
            time.sleep(10)
            
            # Wait for and confirm download
            if not self.wait_for_download():
                print(f"Download failed for index {index}")
                return False

            time.sleep(5)
            # Move file to correct location
            #if not self.move_file(index):
            #    print(f"Failed to move file for index {index}")
            #    return False

            return True

        except Exception as e:
            print(f"Error processing download for index {index}: {str(e)}")
            return False
    
        #self.result_count = self.get_result_count(index)       

    def wait_for_download(self):

        try:
            # First, wait for UI indication that download started
            print("Waiting for download to start...")
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            print("Download started, processing...")
            
            # Wait for UI indication that browser finished
            WebDriverWait(self.driver, 1000).until_not(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            print("Browser reports download complete!")
            return True
            # Check Downloads for file default
            #actually maybe I want another method
    
            
        except Exception as e:
            print(f"Error: {str(e)}")
            if "presence_of_element_located" in str(e):
                print("Download popup never appeared")
            else:
                print("Download didn't complete within the timeout period")

    def move_file(self, index):
        self.filename = self.get_filename(index)
        self.file_count = int(self.status_data.loc[index, 'total_count'])

        if self.download_type == 'excel':

            self.default_download_path = f"{self.download_folder_temp}/{self.filename}.ZIP"

        else:
            # for some reason the PDF download filename defaults to 
            #self.default_download_name = f"Files ({self.file_count}).ZIP"
            self.default_download_path = f"{self.download_folder_temp}/{self.default_download_name}"
            print(f"looking for {self.default_download_name} in default downloads folder")

        self.geography_download_path = f"{self.download_folder}/{self.filename}.ZIP"

        try:
            os.rename(self.default_download_path, self.geography_download_path)
            print(f"file {self.filename} in {self.basin_code} download folder")
            time.sleep(2)
            return True

        except FileNotFoundError:
            print(f"file not found")
            time.sleep(10)

            try:
                self.driver.refresh() # maybe a coincidence but this did the trick last time?
                time.sleep(5)
                os.rename(self.default_download_path, self.geography_download_path)
                print(f"file successfully moved to {self.basin_code} download folder")
                time.sleep(2)

            except FileNotFoundError:
                print(f"file missing or not moved, check default download folder")
                time.sleep(2)

    def update_status(self, index):
        self.filename = self.get_filename(index)
        self.downloaded_file = self.filename + ".ZIP"
        #self.result_count = self.get_result_count(index)
        #filename_column
        #finished_column
        
        downloaded_file_path = os.path.join(self.download_folder, self.downloaded_file)
        file_exists = os.path.isfile(downloaded_file_path)

        if file_exists:
            self.status_data.loc[index, 'file_name'] = self.filename
            self.status_data.loc[index, 'finished'] = 1
            self.status_data.to_csv(self.status_file)
            print(f"status sheet row {index} updated")
        else:
            self.status_data.loc[index, 'finished'] = 0
            print(f"row {index} not marked as finished")

    def file_handling(self, index):
        self.move_file(index)
        self.update_status(index)

    def DownloadProcess(self, index):
        self.DateFilter(index)
        try:
            self.DownloadDialog(index) # i had these indented too... the logic was that these don't need to happen if reset
            self.file_handling(index)
        except SkipRowException:
            raise
        except ResetRequiredException:
            raise

    def main(self, index, basin_code):
        print(f"Download for {basin_code}")
        self.DownloadSetup()  # sort by date and group duplicates before date filtering
        
        row_index = 0
        while row_index < len(self.status_data):

            # Check if all rows are finished
            if (self.status_data['finished'] == 1).all():
                print(f"All rows for {basin_code} are downloaded!")
                #if self.download_type == "excel": # oh is download type not here yet?
                    #combine_excel = CombineResults(basin_code)
                    #combine_excel.combine()
                #else:
                   #pass
                break

            row = self.status_data.iloc[row_index]
            self.finished = row['finished']
            self.over_thousand = row['over_one_thousand']

            if self.finished != 1 and self.over_thousand != 1:
                try:
                    print(f"Proceeding to download basin {basin_code} row {row_index}")
                    time.sleep(1)
                    self.current_row = row
                    self.DownloadProcess(row_index)
                    row_index += 1  # Move to next row only if successful
                except SkipRowException:    
                    print(f"row {row_index} result count exceeds 1000, skipping to next row")
                    self.status_data.at[row_index, 'over_one_thousand'] = 1  # Update status
                    row_index += 1  # Move to next row
                except ResetRequiredException:
                    if self.reset_needed:
                        self.reset()
                        self.reset_needed = False
                        time.sleep(1)
                        print(f"Restarting download process at row {row_index}")
                        # Don't increment row_index, will retry the same row
            else:
                row_index += 1  # Move to next row if finished or over thousand
    

    def reset(self):
        sign_in_button = "//button[@id='SignInRegisterBisNexis']"
        try:
            self._click_from_xpath(sign_in_button)
            print("logging out")
        except ElementClickInterceptedException:
            find_sign_in = self.driver.find_element_by_xpath(sign_in_button)
            self.driver.execute_script("return arguments[0].scrollIntoView(true);", find_sign_in)        
        self.driver.delete_all_cookies()
        print("deleting cookies before logging in again")
        time.sleep(3)
        self.login._init_login()
        self.nlc._search_process()
        time.sleep(5)
        self.DownloadSetup()
#this calls it 
'''

download = Download(
            driver=driver,
            basin_code=basin_code,
            user_name=user_name,
            index=0,  
            login = login,
            nlc = nlc,
            download_type = download_type,
            download_folder = download_folder,
            download_folder_temp = download_folder_temp,
            status_file=status_file,
            finished=False,  
            url=None,  
            timeout=20 )

'''
# and then to run it/check it 

# now this will run the iterrows method
#download.main(index=0, basin_code = basin_code)