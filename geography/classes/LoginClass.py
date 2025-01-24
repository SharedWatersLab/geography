from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

from chromedriver_py import binary_path  

import os
import sys
import pandas as pd
import time
import getpass
from pathlib import Path

# I don't know if I need this????
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# and should it be in like all the classes?

from driverTest import SetupDriver  # noqa: E402
# setup = SetupDriver()
# setup.setup_webdriver()
# service = setup.service

#service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome() # (service=service)


class PasswordManager:
    def __init__(self):
        # initialize the password attribute to None
        self.password = None

    def get_password(self):
        # Check if the password is already set
        if self.password is None:
            # Prompt for the password and store it
            self.password = getpass.getpass()
        # Return the stored password
        return self.password

'''
# Create an instance of PasswordManager
pm = PasswordManager()
if pm.password is None:
    password = pm.get_password()
    print("Password set!")
else: pass
'''
#is this right? will it ask again?

#ideally if the section starting line 41 is good we don't need all this
'''
options = ChromeOptions()
options.page_load_strategy = 'normal'
options.add_argument("--start-maximized")

#options.add_argument("user-data-dir=Users/<username>/Library/Application Support/Google/Chrome/Default")
#prefs = {'download.default_directory' : '/Users/dvas22/Desktop/David/www/geography/downloads'}
options.add_argument("user-data-dir=/tmp/storedLoginInformation1")

prefs = {'download.prompt_for_download' : False}
options.add_experimental_option('prefs', prefs)
'''

class WebDriverManager:
    def __init__(self):
        self.driver = None
        self.options = ChromeOptions()
        self.setup_options()
        self.driver_path = Path("./chromedriver") / ("chromedriver.exe" if sys.platform == "win32" else "chromedriver")
        # self.paths = paths

        # if os.getcwd() != self.paths['base_path'] + "geography":
        #     service_path = "..\chromedriver\chromedriver" if sys.platform.startswith("win") else "../chromedriver/chromedriver"
        # else:
        service_path = ".\chromedriver\chromedriver.exe" if sys.platform.startswith("win") else "./chromedriver/chromedriver"

        # service_path = r".\chromedriver\chromedriver" if sys.platform.startswith("win") else "./chromedriver/chromedriver"
        # print(service_path)
        self.service = Service(service_path)
    
    def setup_options(self):
        self.options = webdriver.ChromeOptions()
        self.options.page_load_strategy = 'normal'
        self.options.add_argument("--start-maximized")
        self.options.add_argument("user-data-dir=/tmp/storedLoginInformation")       
        prefs = {'download.prompt_for_download': False}
        self.options.add_experimental_option('prefs', prefs)

    # def setup_service(self):
    #     os_type = setup.get_operating_system()
    #     print(f"Detected operating system: {os_type}")

    #     chrome_version = setup.get_chrome_version()
    #     if chrome_version:
    #         print(f"Detected Chrome version: {chrome_version}")
    #         chromedriver_version = setup.get_matching_chromedriver_version(chrome_version)
    #         if chromedriver_version:
    #             print(f"Matching ChromeDriver version: {chromedriver_version}")
    #             if setup.download_chromedriver(chromedriver_version, os_type):
    #                 #move_chromedriver(os_type)
    #                 print("downloaded")
    #         else:
    #             print("Failed to find a matching ChromeDriver version. Please ensure you have the latest version of Chrome installed.")
    #     else:
    #         print("Could not detect Chrome version. Please ensure Chrome is installed and you have the latest version.")
        #self.service = Service(ChromeDriverManager().install())
        #self.service = Service('/usr/local/bin/chromedriver')
     
        # should these two replace line 61?
        #self.temp_foldername = "storedLoginInformation" + str(self.number)
        #self.options.add_argument(self.temp_foldername)
        # at some point I need to refer to reset() method right?
        # or somehow instantiate it at the end of main script
        # something like
        #Login._init_login()
      
    
    def start_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

class Login:
    def __init__(self, user_name, password, driver_manager= WebDriverManager, timeout=20, url=None):
        self.driver_manager = driver_manager
        self.driver = driver_manager.start_driver() 
        self.user_name = user_name
        self.password = password
        self.url = url
        self.timeout = timeout

    def _click_from_css(self, css_selector):
        element = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        element.click()
    
    def _send_keys_from_css(self, css_selector, keys):
        element = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(keys)

    def _is_element_present_css(self, css_selector):
        try:
            self.driver.find_element_by_css_selector(css_selector)
            return True
        except NoSuchElementException:
            return False
    
    def reset(self):
        self.number += 1 # self.number = self.number + 1
        self.temp_foldername = "storedLoginInformation" + str(self.number)
        # and then somewhere else the following ???

    def login_page(self):
        #wait = WebDriverWait(self.driver, 5)
        
        TuftsLogin_selector = ".btn-shib > .login"
        OpenAthens_selector = '#lachooser-container > div:nth-child(2) > div > div:nth-child(1) > div:nth-child(1) > div'
        
        try:
            # First check which elements are present
            openathens_elements = self.driver.find_elements(By.CSS_SELECTOR, OpenAthens_selector)
            tufts_elements = self.driver.find_elements(By.CSS_SELECTOR, TuftsLogin_selector)
            
            if openathens_elements:
                time.sleep(3)
                self._click_from_css(OpenAthens_selector)
                print("clicking through new OpenAthens page to get to login home")
            elif tufts_elements:
                print("On Tufts login page")
            
            time.sleep(3)
            print("entering login information")
            self._send_keys_from_css("#username", self.user_name)
            self._send_keys_from_css("#password", self.password)
            self._click_from_css("#login > button")
            print("Entered Tufts username and password")
            time.sleep(3)
            
            return True
            
        except TimeoutException:
            print("Neither login page variant detected")
            return False
    
                # print("need to go back through library login")
                # library_link = "https://tufts.primo.exlibrisgroup.com/discovery/search?query=any,contains,nexis%20uni&tab=Everything&search_scope=MyInst_and_CI&vid=01TUN_INST:01TUN&lang=en&offset=0"
                # self.driver.get(library_link)

                # # these next two lines get to nexis uni from Tufts library
                # available_online_css = "#alma991017244849703851availabilityLine0 > span"
                # self._click_from_css(available_online_css) #click "Available Online"
                # # then retry login process again (btn-shib login, user, pass...)
                # # but in testing, it opened in a new tab (which, yeah, it was gonna do)
                # # but the original tab continued the process just fine... 
                # # so maybe it just needs to navigate away from nexis uni?
                # self._click_from_css(".btn-shib > .login")

    def _init_login(self):
        
        loggedin_home = "https://login.ezproxy.library.tufts.edu/login?auth=tufts&url=http://www.nexisuni.com"
        self.driver.get(self.url or loggedin_home)
        time.sleep(5)
        
        try:
            tuftsloggedin_element = "co-branding-display-name" # class name
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, tuftsloggedin_element)))
            print("User is already logged in.")
        except TimeoutException:
            print("User is not logged in. Proceeding with login...")
            try:
                self.login_page()
            
            #in case update chrome page comes up
                try:
                    update_chrome_substring = "https://api-58712eef.duosecurity.com/frame/frameless/v4/auth?sid=frameless-"
                    if update_chrome_substring in self.driver.current_url:
                        self._click_from_css("body > div > div > div > div.display-flex.flex-direction-column.flex-value-one.size-padding-left-large.size-padding-right-large > div > button")
                        print("skipped update chrome page")
                    else:
                        pass

                except NoSuchElementException:
                    print("update chrome page not prompted")
                    pass

                duo_page_substring = "https://api-58712eef.duosecurity.com/frame/v4/auth/prompt?sid=frameless-"
                if duo_page_substring in self.driver.current_url:
                    print("DUO authentication prompted")
                    self.handle_duo_2fa()
                    time.sleep(2)

                    if self.handle_duo_2fa():
                        print("DUO authentication successful")
                    else:
                        print("DUO authentication failed")
                        return False  # Exit the method if DUO fails
                else:
                    print("DUO authentication not prompted")
                    pass

                time.sleep(5)
                # then this clicks reload if we're not brought to the home page
                self.handle_reload_error()
                time.sleep(5)

            except TimeoutException:
                #print("logged in automatically for some reason")
                pass

    def handle_duo_2fa(self):
        duo_page_substring = "https://api-58712eef.duosecurity.com/frame/v4/auth/prompt?sid=frameless-"
        max_attempts = 2
        attempt = 0

        while attempt < max_attempts:
            try:
                if duo_page_substring in self.driver.current_url:
                    print('DUO push code on screen OR wait for call')
                    time.sleep(10)  # Reduced initial wait time

                    try:
                        self._click_from_css("#trust-browser-button")
                        print("DUO push entered, skipping trust browser page")
                        time.sleep(2)
                    except: NoSuchElementException
                    
                    if duo_page_substring not in self.driver.current_url:
                        print("DUO authentication completed")
                        return True
                    
                    else:
                    
                        if duo_page_substring in self.driver.current_url:
                            other_options_selector = "#auth-view-wrapper > div:nth-child(2) > div.row.display-flex.other-options-link.align-flex-justify-content-center.size-margin-bottom-large.size-margin-top-small"
                            print("waited for push, now calling")
                            self._click_from_css(other_options_selector)
                                
                            DUO_phone_call = 'body > div > div > div.card.card--white-label.uses-white-label-border-color.display-flex.flex-direction-column > div > div.all-auth-methods.display-flex.flex-value-one > ul > li:nth-child(2) > a > span.method-select-chevron > svg'
                            self._click_from_css(DUO_phone_call)
                            print('DUO calling')
                            time.sleep(20)

                            try:
                                self._click_from_css("#trust-browser-button")
                                print("skipping trust browser page")
                            except: NoSuchElementException
                            
                            if duo_page_substring not in self.driver.current_url:
                                print("DUO authentication completed")
                                return True
                    '''
                # # Handle trust browser page
                # if self._is_element_present_css("#trust-browser-button"):
                #     self._click_from_css("#trust-browser-button")
                #     print("Skipped trust browser page")
'''
                    
                # Check if we're still on the DUO page after waiting
                if duo_page_substring not in self.driver.current_url:
                    print("DUO authentication successful")
                    break

                else:
                    pass   
                
            except NoSuchElementException:
                print(f"An element was not found during attempt {attempt + 1}")
            
            attempt += 1
        
        if attempt == max_attempts:
            print("Failed to complete DUO authentication after maximum attempts")
            return False

        return True
    
    def handle_reload_error(self, timeout=10):
        try:
            # Wait for the element to be clickable
            reload_error = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "reload-button"))
            )
            # If the element is found and clickable, click it
            reload_error.click()
            print("Reload button found and clicked")
            return True
        except TimeoutException:
            print("login successful")
            return False
        
# '''
#         #DUO to try to automate
#         # in case we're allowed to use an IT bypass code
#         #bypass_code = 123456789 # replace with the bypass code
#         time.sleep(3)
#         try:
#             duo_page_substring = "https://api-58712eef.duosecurity.com/frame/v4/auth/prompt?sid=frameless-"
#             if duo_page_substring in self.driver.current_url:
#                 print('DUO push code on screen OR wait for call')
#                 time.sleep(20)
#             else: pass
        
#             if duo_page_substring in self.driver.current_url:
#                 other_options_selector = "#auth-view-wrapper > div:nth-child(2) > div.row.display-flex.other-options-link.align-flex-justify-content-center.size-margin-bottom-large.size-margin-top-small"
#                 self._click_from_css(other_options_selector)
#                 DUO_phone_call = 'body > div > div > div.card.card--white-label.uses-white-label-border-color.display-flex.flex-direction-column > div > div.all-auth-methods.display-flex.flex-value-one > ul > li:nth-child(2) > a > span.method-select-chevron > svg'
#                 self._click_from_css(DUO_phone_call)
#                 print('DUO calling')
#                 time.sleep(20)
#             else: 
#                 self._click_from_css("#trust-browser-button")
#                 print("skipped trust browser page")

#         #if DUO fails (sometimes won't call phone), try again
#         #if duo_page_substring in self.driver.current_url:
#             #time.sleep(2)
#             # can do other options again and find selector for code again
#             # and another time.sleep()

#         except NoSuchElementException:
#             print("duo not prompted")
#             pass

#         #in case trust browser page comes up
#         time.sleep(3)
#         try:
#             if duo_page_substring in self.driver.current_url :
#                 self._click_from_css("#trust-browser-button")
#                 print("skipped trust browser page")
                
#             else:
#                 pass

#         except NoSuchElementException:
#             print("trust browser page not prompted")
#             pass
#             '''


# plop into main
# '''
# '''
# from classes.LoginClass import WebDriverManager, Login, PasswordManager

# if __name__ == "__main__":  
    
#     # will ask for and set password
#     pm = PasswordManager()
#     if pm.password is None:
#         password = pm.get_password()
#         print("Password set!")
#     else: pass
    
#     # will open chrome
#     manager = WebDriverManager()
#     driver = manager.start_driver()
#     options = manager.setup_options()

#     # will log in (tufts)
#     login = Login(user_name=user_name, password=password, driver_manager=manager, url=None)
#     login._init_login()

# '''

