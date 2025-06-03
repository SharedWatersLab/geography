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
import re


from classes.LoginClass import Login
from classes.NoLinkClass import NoLinkClass


# class ResetRequiredException(Exception):
#     pass

# class SkipRowException(Exception):
#     pass

# class SingleResultException(Exception):
#     pass

class Download:

    def __init__(self, driver, basin_code, username, login, nlc, download_folder: str, download_folder_temp, finished, url=None, timeout=20):
        """
        REMOVED: download_type parameter (eliminating that concept)
        REMOVED: status_file parameter (eliminating status files)
        """
        self.driver = driver
        self.basin_code = basin_code
        self.username = username
        self.login = login
        self.nlc = nlc
        self.finished = finished 
        self.url = url
        self.timeout = timeout
        self.download_folder = download_folder
        self.download_folder_temp = download_folder_temp

    
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
        # if we need to try with XPath
        #timeline_button = WebDriverWait(self.driver, self.timeout).until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/main/ln-gns-resultslist/div[2]/div/div[1]/div[1]/div[2]/div/aside/button[2]")))
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

    def group_duplicates(self):
        actions_dropdown_xpath = "//button[@id='resultlistactionmenubuttonhc-yk' and text()='Actions']"
        time.sleep(5)
        self._click_from_xpath(actions_dropdown_xpath)
        time.sleep(5)
        moderate_button = "//button[contains(@class, 'action') and @data-action='changeduplicates' and @data-value='moderate']"
        self._click_from_xpath(moderate_button)
        print("group duplicate results by moderate similarity")
        time.sleep(10)

    def handle_popups(self, max_popups=5):

        # Counter to prevent infinite loops
        popups_closed = 0
        
        # A collection of common popup identifiers
        popup_patterns = [
            # Pendo popups with various IDs
            #"//button[contains(@class, '_pendo-close-guide') and contains(@id, 'pendo-close-guide')]", # analytics, from july 2024 not there anymore
            "//button[contains(@class, 'pendo-close-guide')]",
            "//button[contains(@id, 'pendo-close-guide')]",
            "//div[contains(@id, 'pendo-guide-container')]//button[contains(@aria-label, 'Close')]",
            
            # General close buttons for popups/modals
            "//button[@aria-label='Close']",
            "//button[contains(@class, 'close')]",
            "//*[contains(@class, 'modal')]//button[contains(@class, 'close')]",
            "//div[contains(@class, 'popup')]//button",
            "//div[contains(@class, 'modal')]//button",
            
            # Common close icons
            "//*[contains(@class, 'close-icon')]",
            "//i[contains(@class, 'fa-times')]",
            "//span[contains(@class, 'close')]",
            
            # X buttons (common in popups)
            "//button[text()='✕' or text()='×' or text()='X' or text()='x']",
            "//*[text()='✕' or text()='×' or text()='X' or text()='x']"
        ]
        
        while popups_closed < max_popups:
            found_popup = False
            
            # First check if any popups are visible
            for pattern in popup_patterns:
                try:
                    # Find all elements matching the pattern
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    
                    for element in elements:
                        try:
                            if element.is_displayed():
                                # Try scrolling to make sure it's in view
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.5)
                                
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
                                time.sleep(1)  # Short wait after closing a popup
                                break  # Break the inner loop after closing one popup
                        except:
                            continue
                    
                    if found_popup:
                        break  # Break the outer loop to restart from the beginning
                        
                except Exception as e:
                    continue
            
            # If no popup was found and closed, we're done
            if not found_popup:
                break
        
        print(f"Total popups closed: {popups_closed}")
        return popups_closed
    
    def sort_by_date(self):
        sortby_dropdown_css = '#select'
        oldestnewest_option_text = 'Date (oldest-newest)'

        for attempt in range(3):  # Try up to 3 times
            try:
                # Check for and close popup before interacting with dropdown
                self.handle_popups()

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
                self.handle_popups()
                continue
                
            except ElementNotInteractableException:
                print("Element not interactable, attempting to close popup if present")
                self.handle_popups()
                continue
        
        print("Failed to sort by date after multiple attempts")


    def DownloadSetup(self):
        self.group_duplicates()
        self.sort_by_date()

    def get_result_count(self, max_attempts=4):
        """
        Resilient function to get result count that handles:
        - Attribute name variations (with/without spaces)
        - Multiple possible element structures  
        - Timing issues with large result sets
        - Future website changes
        """
        # doubled all timeouts in this method

        for attempt in range(max_attempts): 
            try:
                #time.sleep(2)
                #print(f"Attempt {attempt + 1} to get result count...")
                
                # Wait for page to be fully loaded and stable
                WebDriverWait(self.driver, 40).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Additional wait for any JavaScript to finish (especially important for large result sets)
                time.sleep(2)
                
                # Try to wait for network activity to settle (helps with large result sets)
                try:
                    WebDriverWait(self.driver, 20).until(
                        lambda d: d.execute_script("return jQuery.active == 0") if d.execute_script("return typeof jQuery !== 'undefined'") else True
                    )
                except:
                    pass  # jQuery might not be available
                
                # Focus on the core strategies that matter for the data-actualresultscount attribute
                strategies = [
                    # Strategy 1: Original specific selector with attribute variations
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
                    
                    # Strategy 3: JavaScript-based extraction (most reliable for dynamic content)
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
                            # Use JavaScript to search for the element and attribute
                            js_script = """
                            // Function to wait for the attribute to be populated
                            function waitForResultCount(maxWait = 15000) {
                                return new Promise((resolve) => {
                                    const startTime = Date.now();
                                    
                                    function checkForCount() {
                                        // Try multiple approaches to find the result count
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
                                        
                                        // If not found and we haven't exceeded max wait time, try again
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
                            return self.result_count
                            
                    except Exception as e:
                        print(f"Strategy '{strategy['name']}' failed")
                        continue
                
                if result_count:
                    # Validate the result count makes sense (remove upper bound for large datasets)
                    if result_count > 0:
                        self.result_count = result_count
                        print(f"Final result count: {result_count:,}")  # Format with commas for readability
                        return self.result_count
                    else:
                        print(f"Result count {result_count} is not positive, treating as invalid")
                        result_count = None
                
                if result_count is None:
                    if attempt < max_attempts - 1:
                        if attempt == 0:
                            # First retry: just wait longer (common case)
                            print(f"No result count found on attempt {attempt + 1}, waiting longer and retrying...")
                            time.sleep(15)  # Longer wait for large result sets
                        elif attempt == 1:
                            # Second retry: refresh the page
                            print("Refreshing page to reload result count data...")
                            self.driver.refresh()
                            time.sleep(10)  # Wait for page to reload
                        else:
                            # Final retry: longer wait after refresh
                            print("Final attempt: waiting for backend processing to complete...")
                            time.sleep(20)
                    else:
                        print("Could not retrieve result count after all attempts.")
                        print("The element may exist but the data-actualresultscount attribute is not being populated.")
                        return None
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} to get result count failed")
                if attempt < max_attempts - 1:
                    if attempt == 0:
                        print("First exception, waiting and retrying...")
                        time.sleep(10)
                    else:
                        print("Exception after previous attempts, refreshing page...")
                        self.driver.refresh()
                        time.sleep(10)
                else:
                    print("Max attempts reached due to exceptions.")
                    print("Could not retrieve result count - the data-actualresultscount attribute may not be populating.")
                    return None
        
        return None

    def check_for_download_restriction(self):
        """Monitor for the yellow download restriction banner that appears briefly"""
        try:
            # Create a MutationObserver using JavaScript to watch for the banner
            script = """
            return new Promise((resolve) => {
                const observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        for (const node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Look for any element that might contain error text
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
                
                // Watch the entire document for changes
                observer.observe(document.body, { childList: true, subtree: true });
                
                // Resolve after 5 seconds if nothing is found (shorter for retries)
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

    def wait_for_download(self, download_start_timeout=120, download_complete_timeout=400):
        """Wait for download to complete with better timeout handling"""
        start_time = time.time()
        
        try:
            # First, wait for UI indication that download started
            print("Waiting for download to start...")
            WebDriverWait(self.driver, download_start_timeout).until(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            #print("Download started, processing...")
            elapsed_time = time.time() - start_time # want to check how long it takes when it works
            print(f"Download started after {elapsed_time:.2f} seconds, processing...")
            
        except TimeoutException as e:
            elapsed_time = time.time() - start_time
            print(f"Download did not start after {elapsed_time:.2f} seconds")
            # raise DownloadNeverStartedException(
            #     f"Download failed to start within {download_start_timeout} seconds"
            # )
        
        try:
            # Wait for UI indication that browser finished
            WebDriverWait(self.driver, download_complete_timeout).until_not(
                EC.presence_of_element_located((By.ID, "delivery-popin"))
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            #print(f"Download completed in {elapsed_time:.2f} seconds") #
            # this is kind of a misleading printout, as sometimes UI popup presence changes but download did not complete
            # note: it might be nice to be able to detect what type of UI response appears, to determine whether a download occurred or not
            return True
            
        except TimeoutException as e:
            elapsed_time = time.time() - start_time
            print(f"Download started but didn't complete within {download_complete_timeout} seconds")
            print(f"Total elapsed time: {elapsed_time:.2f} seconds")
            # raise DownloadTimeoutException(
            #     f"Download timed out after {elapsed_time:.2f} seconds (started but didn't finish)"
            # )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"Unexpected error during download: {str(e)}")
            print(f"Failed after {elapsed_time:.2f} seconds")
            raise  # Re-raise the unexpected exception

    def move_file(self, r):

        # Find matching file
        default_filename = [f for f in os.listdir(self.download_folder_temp) if re.match(r"Files \(\d+\)\.ZIP", f)]

        if default_filename:  # If we found any matching files
            print("Download completed!")
            # Use the first matching file
            default_download_path = os.path.join(self.download_folder_temp, default_filename[0])
            geography_download_path = os.path.join(self.download_folder, f"{self.basin_code}_results_{r}.ZIP")

            # Check if file exists and move it
            if os.path.isfile(default_download_path):
                os.rename(default_download_path, geography_download_path)
                print(f"moving file to {geography_download_path}")

        else:
            print(f"file containing range {r} was not downloaded")

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
        username=username,  # Consistent variable naming
        login=login,
        nlc=nlc,
        download_folder=download_folder,
        download_folder_temp=download_folder_temp,
        finished=False,
        url=None,
        timeout=20
    )

'''
