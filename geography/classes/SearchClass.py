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

class Search:
    def __init__(self, driver: webdriver, basin_code, username, geography_folder, 
                 short_timeout=5, long_timeout=15, url=None):
        """
        Initialize Search object with configurable timeouts.
        
        Args:
            short_timeout: For quick UI interactions (buttons, fields) - default 5s
            long_timeout: For page loads, search results - default 15s
        """
        self.driver = driver
        self.url = url
        self.short_timeout = short_timeout   # Quick UI interactions
        self.long_timeout = long_timeout     # Page loads, search completion
        self.basin_code = basin_code
        self.username = username
        self.geography_folder = geography_folder

        # this can manually be set to True if we want to try with narrower search terms/fewer results
        self.use_riparian = False # range count >500 will "flip this switch" to proceed with riparian country search
        self.riparian_txt = os.path.join(self.geography_folder, "data", "downloads", self.basin_code, "riparian_names_used.txt")

        # Load tracking sheet
        tracking_sheet = pd.read_excel(f'{self.geography_folder}geography/basins_searchterms_tracking.xlsx')
        
        self.row = tracking_sheet[tracking_sheet['BCODE'] == basin_code.upper()]
        self.search_term = self.row['Basin_Specific_Terms'].values[0]

        # search keys
        self.box_1_keys = 'water* OR river* OR lake* OR dam* OR stream OR streams OR tributar* OR irrigat* OR flood* OR drought* OR canal* OR hydroelect* OR reservoir* OR groundwater* OR aquifer* OR riparian* OR pond* OR wadi* OR creek* OR oas*s OR spring*'
        self.box_2_keys = 'treaty OR treaties OR agree* OR negotiat* OR mediat* OR resolv* OR facilitat* OR resolution OR commission* OR council* OR dialog* OR meet* OR discuss* OR secretariat* OR manag* OR peace* OR accord OR settle* OR cooperat* OR collaborat* OR diplomacy OR diplomat* OR statement OR "memo" OR "memos" OR memorand* OR convers* OR convene* OR convention* OR declar* OR allocat*OR share*OR sharing OR apportion* OR distribut* OR ration* OR administ* OR trade* OR trading OR communicat* OR notif* OR trust* OR distrust* OR mistrust*OR support* OR relations* OR consult* OR alliance* OR ally OR allies OR compensat* OR disput* OR conflict* OR disagree* OR sanction* OR war* OR troop* OR skirmish OR hostil* OR attack* OR violen* OR boycott* OR protest* OR clash* OR appeal* OR intent* OR reject* OR threat* OR forc* OR coerc* OR assault* OR fight OR demand* OR disapprov*  OR bomb* OR terror* OR assail* OR insurg* OR counterinsurg* OR destr* OR agitat* OR aggrav* OR veto* OR ban* OR exclud* OR prohibit* OR withdraw* OR suspect* OR combat* OR milit* OR refus* OR deteriorat* OR spurn* OR invad* OR invasion* OR blockad* OR debat* OR refugee* OR migrant* OR violat*'
        self.box_3_keys = self.search_term
        self.box_4_keys = 'ocean* OR "bilge water" OR "flood of refugees" OR waterproof OR "water resistant" OR streaming OR streame*'

    def _click_from_css(self, css_selector, timeout=None):
        """Click element using CSS selector with appropriate timeout."""
        timeout = timeout or self.short_timeout  # Use short timeout by default for clicks
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.click()
    
    def _send_keys_from_css(self, css_selector, keys, timeout=None):
        """Send keys to element using CSS selector."""
        timeout = timeout or self.short_timeout
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(keys)

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
    
    def NexisHome(self):
        """Navigate to Nexis Uni home page if needed."""
        try:
            # Use short timeout for safety button - it either appears quickly or not at all
            ignore_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#proceed-button.secondary-button.small-link"))
            )
            ignore_button.click()
            print("Safety page, clicked to ignore")
            # Minimal wait for click to register
            time.sleep(1)
        except TimeoutException:
            pass

        self.nexis_home_substring = 'bisnexishome'
        if self.nexis_home_substring in self.driver.current_url:
            print('Already on Nexis Uni home page')
            pass
        else:
            print("Navigate to Nexis Uni home page")
            self.driver.get("https://login.libdata.lib.ua.edu/login?qurl=http%3a%2f%2fwww.nexisuni.com")
            # Use long timeout for page load
            WebDriverWait(self.driver, self.long_timeout).until(
                lambda d: self.nexis_home_substring in d.current_url
            )

    def _init_search(self):
        """Initialize the search interface."""
        if self.url:
            self.driver.get(self.url)
            # Wait for page load with long timeout
            time.sleep(2)  # Brief wait for JS to initialize
        
        # Click News button - should appear quickly
        news_button = '#nexissearchbutton > tabmenucomponent > div > div > ul > li:nth-child(3) > button'
        self._click_from_css(news_button)
        
        # Click advanced search button
        news_advancedsearch_button = '#wxbhkkk > ul > li:nth-child(1) > button'
        self._click_from_css(news_advancedsearch_button)
        
        # Scroll into view - no wait needed
        self.driver.execute_script("window.scrollTo(0,102)")
        print(f"Initializing search for {self.basin_code}")

    def riparian_search(self):
        """Generate search string with riparian country terms."""
        riparian_country_terms = self.row['Riparian_country_term'].values[0]
        box_5_keys = riparian_country_terms
        string_with_country_names = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and hlead(' + box_5_keys + ') and not hlead(' + self.box_4_keys + ')'

        if len(string_with_country_names) < 5000:
            print("Search string is within limit")
            return string_with_country_names
        else:
            excess_chars = len(string_with_country_names) - 5000
            remove_from_box3 = len(self.box_3_keys) - excess_chars
            box3_truncated = self.box_3_keys[:remove_from_box3]
            last_or_pos = box3_truncated.rfind(" OR ")
            new_box_3_keys = self.box_3_keys[:last_or_pos]
            truncated_riparian_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + new_box_3_keys + ') and hlead(' + box_5_keys + ') and not hlead(' + self.box_4_keys + ')'
            return truncated_riparian_string

    def default_search(self):
        """Generate default search string without riparian terms."""
        default_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and not hlead(' + self.box_4_keys + ')'
        return default_string
    
    def _search_box(self):
        """Fill in the search box with search terms."""
        self.search_box = '#searchTerms'
        
        if self.use_riparian:
            search_string = self.riparian_search()
            print("Adding riparian country terms to search terms")
        else:
            search_string = self.default_search()
            print("Using default search terms")
        
        self._send_keys_from_css(self.search_box, search_string)
        
        # Brief wait for text to populate (sometimes JS needs a moment)
        time.sleep(1)

    def complete_search(self, max_attempts=3):
        """
        Click search button and verify results page loads.
        Uses long timeout since this involves page navigation.
        """
        self.search_button_lower = "//button[@class='btn search' and @data-action='search']"
        self.search_button_upper = "//button[@data-action='search' and @id='mainSearch' and @aria-label='Search']"
        search_buttons_css = ["button.btn.search[data-action='search']", "#mainSearch"]
        
        # Define result indicators once
        result_indicators = [
            "//li[contains(@class, 'active') and @data-actualresultscount]",
            "//button[@data-id='urb:hlct:16']",
            "//div[contains(@class, 'results-list')]"
        ]
        
        for attempt in range(max_attempts):
            try:
                # First check if we're already on the results page
                for indicator in result_indicators:
                    try:
                        if self.driver.find_element(By.XPATH, indicator).is_displayed():
                            print("Already on results page, search was successful")
                            return True
                    except:
                        continue
                
                # Try clicking the search button
                clicked = False
                
                # Try XPath methods first
                for xpath in [self.search_button_lower, self.search_button_upper]:
                    try:
                        button = WebDriverWait(self.driver, self.short_timeout).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        # Scroll to button
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        
                        # Try multiple click methods
                        try:
                            button.click()
                            clicked = True
                            print(f"Clicked search button (standard click, xpath)")
                            break
                        except:
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                clicked = True
                                print(f"Clicked search button (JS click, xpath)")
                                break
                            except:
                                try:
                                    ActionChains(self.driver).move_to_element(button).click().perform()
                                    clicked = True
                                    print(f"Clicked search button (ActionChains, xpath)")
                                    break
                                except:
                                    continue
                    except:
                        continue
                    
                # If XPath failed, try CSS methods
                if not clicked:
                    for css in search_buttons_css:
                        try:
                            button = WebDriverWait(self.driver, self.short_timeout).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, css))
                            )
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            
                            try:
                                button.click()
                                clicked = True
                                print(f"Clicked search button (standard click, CSS)")
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    clicked = True
                                    print(f"Clicked search button (JS click, CSS)")
                                    break
                                except:
                                    try:
                                        ActionChains(self.driver).move_to_element(button).click().perform()
                                        clicked = True
                                        print(f"Clicked search button (ActionChains, CSS)")
                                        break
                                    except:
                                        continue
                        except:
                            continue
                
                # Last resort: find by text
                if not clicked:
                    try:
                        search_buttons = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'Search') or contains(@aria-label, 'Search')]")
                        for button in search_buttons:
                            if button.is_displayed():
                                self.driver.execute_script("arguments[0].click();", button)
                                clicked = True
                                print("Clicked search button (text content search)")
                                break
                    except:
                        pass
                
                # Wait for results page to load - use LONG timeout since this is page navigation
                # Try to detect when page has loaded rather than blind waiting
                try:
                    for indicator in result_indicators:
                        try:
                            WebDriverWait(self.driver, self.long_timeout).until(
                                EC.presence_of_element_located((By.XPATH, indicator))
                            )
                            print("Successfully verified we're on results page")
                            return True
                        except:
                            continue
                    
                    # If we got here, we didn't find the results page
                    if attempt < max_attempts - 1:
                        print(f"Search attempt {attempt+1} failed. Retrying...")
                        # Check for error page
                        if "error" in self.driver.title.lower() or "problem" in self.driver.title.lower():
                            self.driver.refresh()
                            time.sleep(2)  # Brief wait after refresh
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
                    time.sleep(1)  # Brief wait before retry
                else:
                    print("All search attempts failed.")
                    return False
        
        return False

    def switch_to_riparian(self):
        """Flips the switch permanently to use riparian search."""
        print("Switching to riparian search mode...")
        self.use_riparian = True
        # Create riparian tracking file
        if not os.path.exists(self.riparian_txt):
            os.makedirs(os.path.dirname(self.riparian_txt), exist_ok=True)
            with open(self.riparian_txt, 'w') as f:
                f.write("Riparian search terms used\n")
    
    def search_process(self, start_date, end_date):
        """Execute the complete search process with date filters."""
        self.NexisHome()
        self._init_search()
        self._search_box()
        
        # Set date fields
        startdate_field = "//input[@class='dateFrom' and @aria-label='From']"
        enddate_field = "//input[@class='dateTo' and @aria-label='To']"

        # Determine OS for keyboard shortcuts
        system = platform.system().lower()
        if system == "darwin":
            select_all = Keys.COMMAND, "a"
        elif system == "windows":
            select_all = Keys.CONTROL, "a"

        # Fill in dates - these are quick field operations
        self._send_keys_from_xpath(startdate_field, select_all)
        self._send_keys_from_xpath(startdate_field, start_date)

        self._send_keys_from_xpath(enddate_field, select_all)
        self._send_keys_from_xpath(enddate_field, end_date)

        # Complete the search - this uses long timeout internally
        return self.complete_search()