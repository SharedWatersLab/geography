from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

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
import re

from classes.LoginClass import Login
from classes.SearchClass import Search


class DownloadFailedException(Exception):
    def __init__(self, message="Download persistently failing to complete"):
        self.message = message
        super().__init__(self.message)

class Download:

    def __init__(self, driver, basin_code, username, login, search, download_folder: str, download_folder_temp, finished, url=None, timeout=20):

        self.driver = driver
        self.basin_code = basin_code
        self.username = username
        self.login = login
        self.search = search
        self.finished = finished 
        self.url = url
        self.short_timeout = short_timeout   # Quick UI interactions
        self.long_timeout = long_timeout     # Page loads, result processing
        self.download_folder = download_folder
        self.download_folder_temp = download_folder_temp

    
    def _click_from_xpath(self, xpath, timeout=None):
        """Click element using XPath with appropriate timeout."""
        timeout = timeout or self.short_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
        except TimeoutException:
            raise NoSuchElementException(f"Element with xpath '{xpath}' not found")

    def _send_keys_from_xpath(self, xpath, keys, timeout=None):
        """Send keys to element using XPath."""
        timeout = timeout or self.short_timeout
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath))) 
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        element.send_keys(keys)

    def _click_from_css(self, css_selector, timeout=None):
        """Click element using CSS selector with appropriate timeout."""
        timeout = timeout or self.short_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
            )
            element.click()
        except TimeoutException:
            raise NoSuchElementException(f"Element with selector '{css_selector}' not found")

       
    def _send_keys_from_css(self, css_selector, keys, timeout=None):
        """Send keys to element using CSS selector."""
        timeout = timeout or self.short_timeout
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(keys)

    def open_timeline(self):
        """Open the timeline filter. Uses short timeout since button should appear quickly."""
        timeline_button = '#podfiltersbuttondatestr-news'
        self._click_from_css(timeline_button)
        # Wait for timeline to fully load - reduced from 10s
        time.sleep(3)

    def parse_date(self, date_string):
        """Parse date string in various formats."""
        date_formats = [
            '%m/%d/%y',  # 8/1/08
            '%m/%d/%Y',  # 8/1/2008
            '%Y-%m-%d',  # 2008-08-01
            '%d-%m-%Y',  # 01-08-2008
            '%Y/%m/%d',  # 2008/08/01
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_string, date_format)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date string: {date_string}")

    def group_duplicates(self):
        """Group duplicate results in the search results."""
        actions_dropdown_xpath = "//button[@id='resultlistactionmenubuttonhc-yk' and text()='Actions']"
        
        # Wait for actions dropdown to be ready
        self._click_from_xpath(actions_dropdown_xpath)
        time.sleep(1)  # Brief wait for dropdown to open
        
        moderate_button = "//button[contains(@class, 'action') and @data-action='changeduplicates' and @data-value='moderate']"
        high_button = "//button[contains(@class, 'action') and @data-action='changeduplicates' and @data-value='high']"
        duplicates_button = moderate_button  # Changed August 2025
        
        self._click_from_xpath(duplicates_button)
        print("Group duplicate results")
        
        # Wait for grouping to apply - reduced from 10s
        # Use explicit wait for page to be ready
        WebDriverWait(self.driver, self.long_timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)  # Brief buffer for UI to update

    def handle_popups(self, max_popups=5):
        """
        Handle various popup types that may appear.
        Uses short timeout since popups either appear immediately or not at all.
        """
        popups_closed = 0
        
        # Collection of common popup identifiers
        popup_patterns = [
            # Pendo popups
            "//button[contains(@class, 'pendo-close-guide')]",
            "//button[contains(@id, 'pendo-close-guide')]",
            "//div[contains(@id, 'pendo-guide-container')]//button[contains(@aria-label, 'Close')]",
            
            # General close buttons
            "//button[@aria-label='Close']",
            "//button[contains(@class, 'close')]",
            "//*[contains(@class, 'modal')]//button[contains(@class, 'close')]",
            "//div[contains(@class, 'popup')]//button",
            "//div[contains(@class, 'modal')]//button",
            
            # Close icons
            "//*[contains(@class, 'close-icon')]",
            "//i[contains(@class, 'fa-times')]",
            "//span[contains(@class, 'close')]",
            
            # X buttons
            "//button[text()='✕' or text()='×' or text()='X' or text()='x']",
            "//*[text()='✕' or text()='×' or text()='X' or text()='x']"
        ]
        
        while popups_closed < max_popups:
            found_popup = False
            
            for pattern in popup_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    
                    for element in elements:
                        try:
                            if element.is_displayed():
                                # Scroll into view
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)  # Reduced from 0.5s
                                
                                # Try different click methods
                                try:
                                    element.click()
                                except:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                    except:
                                        try:
                                            ActionChains(self.driver).move_to_element(element).click().perform()
                                        except:
                                            continue
                                
                                print(f"Closed popup using pattern: {pattern}")
                                found_popup = True
                                popups_closed += 1
                                time.sleep(0.5)  # Reduced from 1s
                                break
                        except:
                            continue
                    
                    if found_popup:
                        break
                        
                except Exception as e:
                    continue
            
            if not found_popup:
                break
        
        if popups_closed > 0:
            print(f"Total popups closed: {popups_closed}")
        return popups_closed
    
    def sort_by_date(self):
        """Sort results by date (oldest to newest)."""
        sortby_dropdown_css = '#select'
        oldestnewest_option_text = 'Date (oldest-newest)'

        for attempt in range(3):
            try:
                # Check for and close popup before interacting
                self.handle_popups()

                # Wait for dropdown to be clickable
                dropdown = WebDriverWait(self.driver, self.long_timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sortby_dropdown_css))
                )
                
                # Use Select class to interact with dropdown
                select = Select(dropdown)
                select.select_by_visible_text(oldestnewest_option_text)
                
                print("Selected 'Date (oldest-newest)' option")
                
                # Wait for page to update - reduced from 5s
                WebDriverWait(self.driver, self.long_timeout).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)  # Brief buffer for sort to apply

                return  # Success
                
            except StaleElementReferenceException:
                print("Stale element, retrying...")
                time.sleep(1)  # Reduced from 2s
                continue
                
            except (TimeoutException, NoSuchElementException):
                print(f"Attempt {attempt + 1}: Can't find sort-by dropdown, refreshing the page")
                self.driver.refresh()
                time.sleep(3)  # Reduced from 5s
                continue
                
            except ElementClickInterceptedException:
                print("Popup is in the way, attempting to close it")
                self.handle_popups()
                continue
                
            except ElementNotInteractableException:
                print("Element not interactable, attempting to close popup if present")
                self.handle_popups()
                continue
        
        print("Failed to sort by date after multiple attempts")

    def DownloadSetup(self):
        """Prepare results for download by grouping duplicates and sorting."""
        self.group_duplicates()
        self.sort_by_date()

    def get_result_count(self, max_attempts=4):
        """
        Resilient function to get result count that handles:
        - Attribute name variations (with/without spaces)
        - Multiple possible element structures  
        - Timing issues with large result sets
        - Future website changes
        
        Uses long timeout since this involves waiting for backend processing.
        """
        for attempt in range(max_attempts): 
            try:
                # Wait for page to be fully loaded and stable
                WebDriverWait(self.driver, self.long_timeout * 2).until(  # Extra time for large datasets
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Brief wait for JavaScript to finish - reduced from 2s
                time.sleep(1)
                
                # Try to wait for network activity to settle
                try:
                    WebDriverWait(self.driver, self.long_timeout).until(
                        lambda d: d.execute_script("return jQuery.active == 0") if d.execute_script("return typeof jQuery !== 'undefined'") else True
                    )
                except:
                    pass  # jQuery might not be available
                
                # Strategies to find the result count
                strategies = [
                    # Strategy 1: Original specific selector
                    {
                        "name": "Original CSS selector",
                        "method": "css_with_attributes",
                        "selector": "#sidebar > div.search-controls > div.content-type-container.isBisNexisRedesign > ul > li.active",
                        "attributes": ["data-actualresultscount", " data-actualresultscount", "data-actualresultscount ", " data-actualresultscount "]
                    },
                    
                    # Strategy 2: More generic CSS selector
                    {
                        "name": "Generic li.active selector",
                        "method": "css_with_attributes", 
                        "selector": "li.active",
                        "attributes": ["data-actualresultscount", " data-actualresultscount", "data-actualresultscount ", " data-actualresultscount "]
                    },
                    
                    # Strategy 3: JavaScript-based extraction (most reliable)
                    {
                        "name": "JavaScript extraction",
                        "method": "javascript"
                    }
                ]
                
                result_count = None
                successful_strategy = None
                
                for strategy in strategies:
                    try:
                        if strategy["method"] == "css_with_attributes":
                            elements = self.driver.find_elements(By.CSS_SELECTOR, strategy["selector"])
                            for element in elements:
                                if element.is_displayed():
                                    for attr in strategy["attributes"]:
                                        try:
                                            value = element.get_attribute(attr)
                                            if value and value.strip() and value.strip().isdigit():
                                                result_count = int(value.strip())
                                                successful_strategy = f"{strategy['name']} - attribute: '{attr}'"
                                                break
                                        except:
                                            continue
                                    if result_count:
                                        break
                        
                        elif strategy["method"] == "javascript":
                            js_script = """
                            // Function to wait for the attribute to be populated
                            function waitForResultCount(maxWait = 15000) {
                                return new Promise((resolve) => {
                                    const startTime = Date.now();
                                    
                                    function checkForCount() {
                                        var possibleSelectors = [
                                            '#sidebar > div.search-controls > div.content-type-container.isBisNexisRedesign > ul > li.active',
                                            'li.active',
                                            'li[class*="active"]'
                                        ];
                                        
                                        for (var i = 0; i < possibleSelectors.length; i++) {
                                            var element = document.querySelector(possibleSelectors[i]);
                                            if (element) {
                                                var attrs = ['data-actualresultscount', ' data-actualresultscount', 'data-actualresultscount ', ' data-actualresultscount '];
                                                for (var j = 0; j < attrs.length; j++) {
                                                    var value = element.getAttribute(attrs[j]);
                                                    if (value && value.trim() && !isNaN(parseInt(value.trim()))) {
                                                        resolve({
                                                            value: parseInt(value.trim()), 
                                                            selector: possibleSelectors[i], 
                                                            attribute: attrs[j]
                                                        });
                                                        return;
                                                    }
                                                }
                                            }
                                        }
                                        
                                        if (Date.now() - startTime < maxWait) {
                                            setTimeout(checkForCount, 500);
                                        } else {
                                            resolve(null);
                                        }
                                    }
                                    
                                    checkForCount();
                                });
                            }
                            
                            return waitForResultCount();
                            """
                            
                            js_result = self.driver.execute_script(js_script)
                            if js_result and js_result.get('value'):
                                result_count = js_result['value']
                                successful_strategy = f"{strategy['name']} - {js_result.get('selector')} with attribute '{js_result.get('attribute')}'"
                        
                        if result_count:
                            print(f"Successfully found result count: {result_count} using {successful_strategy}")
                            self.result_count = result_count
                            return result_count
                            
                    except Exception as e:
                        print(f"Strategy '{strategy['name']}' failed")
                        continue
                
                if result_count:
                    # Validate the result count makes sense
                    if result_count > 0:
                        self.result_count = result_count
                        print(f"Final result count: {result_count:,}")
                        return self.result_count
                    else:
                        print(f"Result count {result_count} is not positive, treating as invalid")
                        result_count = None
                
                if result_count is None:
                    if attempt < max_attempts - 1:
                        if attempt == 0:
                            # First retry: just wait longer
                            print(f"No result count found on attempt {attempt + 1}, waiting longer and retrying...")
                            time.sleep(20)  # Reduced from 30s - still long for large datasets
                        elif attempt == 1:
                            # Second retry: refresh the page
                            print("Refreshing page to reload result count data...")
                            self.driver.refresh()
                            time.sleep(20)  # Reduced from 30s
                        else:
                            # Final retry: longer wait after refresh
                            print("Final attempt: waiting for backend processing to complete...")
                            time.sleep(30)  # Reduced from 60s
                    else:
                        print("Could not retrieve result count after all attempts.")
                        print("The element may exist but the data-actualresultscount attribute is not being populated.")
                        return None
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} to get result count failed")
                if attempt < max_attempts - 1:
                    if attempt == 0:
                        print("First exception, waiting and retrying...")
                        time.sleep(5)  # Reduced from 10s
                    else:
                        print("Exception after previous attempts, refreshing page...")
                        self.driver.refresh()
                        time.sleep(5)  # Reduced from 10s
                else:
                    print("Max attempts reached due to exceptions.")
                    print("Could not retrieve result count - the data-actualresultscount attribute may not be populating.")
                    return None
        
        return None

    def get_ranges(self):
        """Get ranges based on result count and download limit."""
        # Get full count from site
        full_count = self.get_result_count() 
        
        # Nexis Uni limit for word full text
        download_limit = 500 

        # Generate list of ranges for download dialog
        ranges = []
        for i in range(1, full_count, download_limit):
            end = min(i + (download_limit - 1), full_count)
            ranges.append(f"{i}-{end}")

        # Match downloaded files to ranges
        downloaded_ranges = [f.split("_")[-1].replace(".ZIP", "") for f in os.listdir(self.download_folder) if f.endswith(".ZIP")]

        # Compare and create list of ranges to download
        not_downloaded_ranges = []
        for r in ranges:
            if r in downloaded_ranges:
                continue
            # For final range, check if any downloaded range has same start number
            if r == ranges[-1]:
                start_num = r.split('-')[0]
                if any(dr.split('-')[0] == start_num for dr in downloaded_ranges):
                    continue
            not_downloaded_ranges.append(r)
        not_downloaded_ranges = sorted(not_downloaded_ranges, key=lambda x: int(x.split('-')[0]))
        return not_downloaded_ranges
    
    def check_for_download_restriction(self):
        """
        Monitor for the yellow download restriction banner that appears briefly.
        Uses short timeout since banner appears immediately if it's going to appear.
        """
        try:
            script = """
            return new Promise((resolve) => {
                const observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        for (const node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                const text = node.textContent.toLowerCase();
                                if (text.includes("can't download") || 
                                    text.includes("cannot download") ||
                                    text.includes("download limit") ||
                                    text.includes("restricted")) {
                                    observer.disconnect();
                                    resolve({found: true, message: text});
                                    return;
                                }
                            }
                        }
                    }
                });
                
                observer.observe(document.body, { childList: true, subtree: true });
                
                // Resolve after 5 seconds if nothing is found
                setTimeout(() => {
                    observer.disconnect();
                    resolve({found: false});
                }, 5000);
            });
            """
            result = self.driver.execute_script(script)
            return result
        except Exception as e:
            print(f"Error checking for download limit banner")
            return {"found": False}

    def download_dialog(self, r):
        """
        Handle the download dialog process.
        Uses short timeout for UI interactions.
        """
        open_download_options = "//button[@data-action='downloadopt' and @aria-label='Download']"
        result_range_field = "//input[@id='SelectedRange']"

        try:
            # Wait for download button - reduced from 10s to 5s
            time.sleep(5)
            self._click_from_xpath(open_download_options)
            time.sleep(1)  # Reduced from 2s

        except (ElementClickInterceptedException, StaleElementReferenceException):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Check if we're in dialog box
                    WebDriverWait(self.driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, result_range_field))
                    )                        
                    break  # Success

                except (NoSuchElementException, TimeoutException):
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Reduced from 2s
                        print(f"Attempt {attempt + 1} failed to open download window, retrying...")
                        time.sleep(5)  # Reduced from 10s
                        self._click_from_xpath(open_download_options)
                        time.sleep(1)  # Reduced from 2s
                    else:
                        print(f"Could not open dialog box, will skip range {r}")
                        raise DownloadFailedException

        # Enter range in dialog box
        range_element = self.driver.find_element(By.XPATH, result_range_field)
        range_element.clear()
        range_element.send_keys(r)

        # Click MS Word option
        MSWord_option = "//input[@type= 'radio' and @id= 'Docx']"
        self._click_from_xpath(MSWord_option)

        # Click separate files option
        separate_files_option = "//input[@type= 'radio' and @id= 'SeparateFiles']"
        self._click_from_xpath(separate_files_option)

        # Click download button
        download_button = "//button[@type='submit' and @class='button primary' and @data-action='download']"
        self._click_from_xpath(download_button)

    def wait_for_download(self, download_start_timeout=120, download_complete_timeout=400):
        """
        Wait for download to complete with better timeout handling.
        These timeouts are appropriate for network operations and should remain relatively long.
        """
        start_time = time.time()
        
        try:
            # Wait for UI indication that download started
            print("Waiting for download to start...")
            WebDriverWait(self.driver, download_start_timeout).until(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            elapsed_time = time.time() - start_time
            print(f"Download started after {elapsed_time:.2f} seconds, processing...")
            
        except TimeoutException as e:
            elapsed_time = time.time() - start_time
            print(f"Download did not start after {elapsed_time:.2f} seconds")
            raise DownloadFailedException
        
        try:
            # Wait for UI indication that browser finished
            WebDriverWait(self.driver, download_complete_timeout).until_not(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            return True
            
        except TimeoutException as e:
            elapsed_time = time.time() - start_time
            print(f"Download started but didn't complete within {download_complete_timeout} seconds")
            print(f"Total elapsed time: {elapsed_time:.2f} seconds")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"Unexpected error during download: {str(e)}")
            print(f"Failed after {elapsed_time:.2f} seconds")
            raise

    def move_file(self, r):
        """Move downloaded file to appropriate location."""
        # Find matching file
        default_filename = [f for f in os.listdir(self.download_folder_temp) if re.match(r"Files \(\d+\)\.ZIP", f)]

        if default_filename:
            print("Download completed!")
            default_download_path = os.path.join(self.download_folder_temp, default_filename[0])
            geography_download_path = os.path.join(self.download_folder, f"{self.basin_code}_results_{r}.ZIP")

            if os.path.isfile(default_download_path):
                os.rename(default_download_path, geography_download_path)
                print(f"Moving file to {geography_download_path}")
        else:
            print(f"File containing range {r} was not downloaded")
            raise DownloadFailedException

    def wait_for_box_sync(self, file_path, max_wait=30):
        """Wait for file to be fully synced to Box Drive."""
        print("Waiting for Box Drive sync...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                time.sleep(2)  # Buffer for sync completion
                print("File synced to Box Drive!")
                return True
            time.sleep(1)
        
        print("Warning: Box sync may not be complete")
        return False

    def check_clear_downloads(self, r):
        """Check for and handle unsorted downloads."""
        default_download_pattern = r"Files \(\d+\)\.ZIP"
        matching_files = [f for f in os.listdir(self.download_folder_temp) if re.match(default_download_pattern, f)]
        
        if matching_files:
            print("There's an unsorted file in downloads")
            self.create_unsorted_folder(r)
            self.move_unsorted(r, matching_files[0])

    def create_unsorted_folder(self, r):
        """Create folder for unsorted downloads."""
        self.unsorted_folder = Path(f"{self.download_folder}/{self.basin_code}_unsorted")
        if not os.path.exists(self.unsorted_folder):
            print(f"Creating unsorted folder {self.unsorted_folder}")
            os.makedirs(self.unsorted_folder)

        print("+" * 48)
        print(f"Check unsorted download found in range {r}")
        print("+" * 48)

    def move_unsorted(self, r, original_filename):
        """Move unsorted files to the unsorted folder."""
        original_path = os.path.join(self.download_folder_temp, original_filename)
        unsorted_filename = f"foundinrange_{r}.ZIP"
        unsorted_moved_path = os.path.join(self.unsorted_folder, unsorted_filename)
        
        os.rename(original_path, unsorted_moved_path)
        print(f"File {unsorted_filename} moved to {self.basin_code} download folder")