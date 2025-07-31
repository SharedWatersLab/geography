import time
import platform
import pandas as pd
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.keys import Keys 

#from geography.classes.DownloadClass import Download

class Search:
    def __init__(self, driver: webdriver, basin_code, username, geography_folder, timeout=20, url=None):
        self.driver = driver
        self.url = url
        self.timeout = timeout
        self.basin_code = basin_code
        self.username = username  # Consistent naming
        self.geography_folder = geography_folder  # Now passed directly from paths

        # this can manually be set to True if we want to try with narrower search terms/fewer results
        self.use_riparian = False # range count >500 will "flip this switch" to proceed with riparian country search
        
        # Load tracking sheet - note the path might need adjustment
        tracking_sheet = pd.read_excel(f'{self.geography_folder}geography/basins_searchterms_tracking.xlsx')
        
        self.row = tracking_sheet[tracking_sheet['BCODE'] == basin_code.upper()]
        self.search_term = self.row['Basin_Specific_Terms'].values[0]

        # search keys
        self.box_1_keys = 'water* OR river* OR lake* OR dam* OR stream OR streams OR tributar* OR irrigat* OR flood* OR drought* OR canal* OR hydroelect* OR reservoir* OR groundwater* OR aquifer* OR riparian* OR pond* OR wadi* OR creek* OR oas*s OR spring*'
        self.box_2_keys = 'treaty OR treaties OR agree* OR negotiat* OR mediat* OR resolv* OR facilitat* OR resolution OR commission* OR council* OR dialog* OR meet* OR discuss* OR secretariat* OR manag* OR peace* OR accord OR settle* OR cooperat* OR collaborat* OR diplomacy OR diplomat* OR statement OR "memo" OR "memos" OR memorand* OR convers* OR convene* OR convention* OR declar* OR allocat*OR share*OR sharing OR apportion* OR distribut* OR ration* OR administ* OR trade* OR trading OR communicat* OR notif* OR trust* OR distrust* OR mistrust*OR support* OR relations* OR consult* OR alliance* OR ally OR allies OR compensat* OR disput* OR conflict* OR disagree* OR sanction* OR war* OR troop* OR skirmish OR hostil* OR attack* OR violen* OR boycott* OR protest* OR clash* OR appeal* OR intent* OR reject* OR threat* OR forc* OR coerc* OR assault* OR fight OR demand* OR disapprov*  OR bomb* OR terror* OR assail* OR insurg* OR counterinsurg* OR destr* OR agitat* OR aggrav* OR veto* OR ban* OR exclud* OR prohibit* OR withdraw* OR suspect* OR combat* OR milit* OR refus* OR deteriorat* OR spurn* OR invad* OR invasion* OR blockad* OR debat* OR refugee* OR migrant* OR violat*'
        self.box_3_keys = self.search_term
        self.box_4_keys = 'ocean* OR "bilge water" OR "flood of refugees" OR waterproof OR “water resistant” OR streaming OR streame*'

    def _click_from_css(self, css_selector):
        element = WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.click()
    
    def _send_keys_from_css(self, css_selector, keys):
        element = WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(keys)

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
    
    def NexisHome(self):
        self.nexis_home_substring = 'bisnexishome'
        if self.nexis_home_substring in self.driver.current_url:
            print('already on Nexis Uni home page')
            pass
        else:
            print("Navigate to Nexis Uni home page")
            self.driver.get("https://login.libdata.lib.ua.edu/login?qurl=http%3a%2f%2fwww.nexisuni.com")
            time.sleep(3)

    def _init_search(self):
        if self.url:
            self.driver.get(self.url)
        #news_button = 'body > main > div > ln-navigation > navigation > div.global-nav.light.margin-bottom-30 > div.zones.pagewrapper.product-switcher-navigation.pagewrapper-nexis > nexissearchtabmenu > div > tabmenucomponent > div > div > ul > li:nth-child(3) > button'
        news_button = '#nexissearchbutton > tabmenucomponent > div > div > ul > li:nth-child(3) > button' # new selector for UA search
        self._click_from_css(news_button) # click to search in News
        news_advancedsearch_button = '#wxbhkkk > ul > li:nth-child(1) > button'
        self._click_from_css(news_advancedsearch_button) # click advanced search, PN: NOT WORKING FOR ME
        self.driver.execute_script("window.scrollTo(0,102)")
        print("Initializing search for " + self.basin_code)
        #print(f"Initializing search for {row['Basin_Name']})

    def riparian_search(self):
        riparian_country_terms = self.row['Riparian_country_term'].values[0]
        box_5_keys = riparian_country_terms
        string_with_country_names = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and hlead(' + box_5_keys + ') and not hlead(' + self.box_4_keys + ')'

        if len(string_with_country_names) < 5000: # to see if it fits our search limit
            print("search string is within limit")
            return string_with_country_names
        else:
            excess_chars = len(string_with_country_names) - 5000 # how much longer is the string than the Nexis Uni limit?
            remove_from_box3 = len(self.box_3_keys) - excess_chars # how long does this make basin-specific limit?
            #print(f"string is {len(string_with_country_names)} characters, need to create a shorter string")
            box3_truncated = self.box_3_keys[:remove_from_box3] # trims basin-specific terms to exactly the limit
            last_or_pos = box3_truncated.rfind(" OR ") # finds the nearest 'or'
            # update the variable
            new_box_3_keys = self.box_3_keys[:last_or_pos] # truncates from there so the final term is a complete one
            truncated_riparian_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + new_box_3_keys + ') and hlead(' + box_5_keys + ') and not hlead(' + self.box_4_keys + ')'
            #print(f"new search string is {len(truncated_riparian_string)} characters")
            return truncated_riparian_string

    def default_search(self):
        default_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and not hlead(' + self.box_4_keys + ')'
        return default_string
    
    def _search_box(self):
        self.search_box = '#searchTerms' # css
        #self.search_box = "//input[@type='text' and @id='searchTerms']"
        
        if self.use_riparian: # if that "switch" in init has been flipped due to persistent download failure exception
            search_string = self.riparian_search()
            print("adding riparian country terms to search terms")
        else:
            search_string = self.default_search()
            print("using default search terms")
        
        self._send_keys_from_css(self.search_box, search_string)
        #self._send_keys_from_xpath(self.search_box, self.search_string)
        
        time.sleep(5)

    #click search
    def complete_search(self, max_attempts=3):
        self.search_button_lower = "//button[@class='btn search' and @data-action='search']"
        self.search_button_upper = "//button[@data-action='search' and @id='mainSearch' and @aria-label='Search']"
        search_buttons_css = ["button.btn.search[data-action='search']", "#mainSearch"]
        
        for attempt in range(max_attempts):
            try:
                # First check if we're already on the results page (if a previous click worked but didn't register in code)
                try:
                    # Check for elements that only appear on results page
                    result_indicators = [
                        "//li[contains(@class, 'active') and @data-actualresultscount]",
                        "//button[@data-id='urb:hlct:16']",
                        "//div[contains(@class, 'results-list')]"
                    ]
                    
                    for indicator in result_indicators:
                        try:
                            if self.driver.find_element(By.XPATH, indicator).is_displayed():
                                print("Already on results page, search was successful")
                                return True
                        except:
                            continue
                except:
                    pass
                
                # Try clicking with different methods
                clicked = False
                
                # Try XPath methods first
                try:
                    # Try to make sure the button is in view
                    for xpath in [self.search_button_lower, self.search_button_upper]:
                        try:
                            button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xpath))
                            )
                            # Scroll to the button
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)  # Give a moment for the page to settle
                            
                            # Try multiple click methods
                            try:
                                button.click()
                                clicked = True
                                print(f"Clicked search button using standard click with xpath: {xpath}")
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    clicked = True
                                    print(f"Clicked search button using JS click with xpath: {xpath}")
                                    break
                                except:
                                    try:
                                        ActionChains(self.driver).move_to_element(button).click().perform()
                                        clicked = True
                                        print(f"Clicked search button using ActionChains with xpath: {xpath}")
                                        break
                                    except:
                                        continue
                        except:
                            continue
                except:
                    pass
                    
                # If XPath methods failed, try CSS methods
                if not clicked:
                    for css in search_buttons_css:
                        try:
                            button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                            )
                            # Scroll to the button
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            
                            try:
                                button.click()
                                clicked = True
                                print(f"Clicked search button using standard click with CSS: {css}")
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    clicked = True
                                    print(f"Clicked search button using JS click with CSS: {css}")
                                    break
                                except:
                                    try:
                                        ActionChains(self.driver).move_to_element(button).click().perform()
                                        clicked = True
                                        print(f"Clicked search button using ActionChains with CSS: {css}")
                                        break
                                    except:
                                        continue
                        except:
                            continue
                
                # If no click worked, try a last resort
                if not clicked:
                    try:
                        # Try to find any search button by text content
                        search_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Search') or contains(@aria-label, 'Search')]")
                        for button in search_buttons:
                            if button.is_displayed():
                                self.driver.execute_script("arguments[0].click();", button)
                                clicked = True
                                print("Clicked search button using text content search")
                                break
                    except:
                        pass
                
                # Wait for results page to load
                time.sleep(5)
                
                # Verify we're on the results page
                try:
                    # Try to find an element that should be on the results page
                    for indicator in result_indicators:
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, indicator))
                            )
                            print("Successfully verified we're on results page")
                            return True
                        except:
                            continue
                    
                    # If we got here, we likely didn't reach the results page
                    if attempt < max_attempts - 1:
                        print(f"Search attempt {attempt+1} failed. Search button may have been clicked but results page not loaded. Retrying...")
                        # Try refreshing if on an error page
                        if "error" in self.driver.title.lower() or "problem" in self.driver.title.lower():
                            self.driver.refresh()
                            time.sleep(5)
                    else:
                        print("All search attempts failed. Could not reach results page.")
                        return False
                        
                except Exception as e:
                    print(f"Error verifying results page: {str(e)}")
                    if attempt < max_attempts - 1:
                        print(f"Retrying search (attempt {attempt+2}/{max_attempts})...")
                    else:
                        print("All search attempts failed.")
                        return False
                        
            except Exception as e:
                print(f"Search attempt {attempt+1} failed with error: {str(e)}")
                if attempt < max_attempts - 1:
                    print(f"Retrying search (attempt {attempt+2}/{max_attempts})...")
                    time.sleep(2)
                else:
                    print("All search attempts failed.")
                    return False
        
        return False

    def switch_to_riparian(self):
        """Flips the switch permanently"""
        print("Switching to riparian search mode...")
        self.use_riparian = True
        # and then create a .txt file that's called 'riparian' and add it to the downloads/bcode folder, which we'll track in main sheet at completion
        riparian_txt = os.path.join(self.geography_folder, "data", "downloads", self.basin_code, "riparian_names_used.txt")
        if not os.path.exists(riparian_txt):
            os.makedirs(riparian_txt)
    
    def search_process(self, start_date, end_date):

        self.NexisHome()
        self._init_search()
        self._search_box()
        time.sleep(10)
        # set date here
        startdate_field = "//input[@class='dateFrom' and @aria-label='From']"
        enddate_field = "//input[@class='dateTo' and @aria-label='To']"

        system = platform.system().lower()
        if system == "darwin":
            select_all = Keys.COMMAND, "a"
        elif system == "windows":
            select_all = Keys.CONTROL, "a"

        self._send_keys_from_xpath(startdate_field, select_all)
        self._send_keys_from_xpath(startdate_field, start_date)

        self._send_keys_from_xpath(enddate_field, select_all)
        self._send_keys_from_xpath(enddate_field, end_date)

        #continue
        self.complete_search()
        time.sleep(5)

#search = newsearch(nlc, download)