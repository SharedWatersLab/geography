from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import time
import pandas as pd

#from classes.UserClass import UserClass

class NoLinkClass:
    def __init__(self, driver: webdriver, basin_code, download_type, currentUser, timeout=20, url=None):
        self.driver = driver
        self.url = url
        self.timeout = timeout
        self.basin_code = basin_code
        self.download_type = download_type
        self.geography_folder = currentUser.getPath(download_type)["geography_folder"] # assumes where nlc is called userclass has already been defined

        tracking_sheet = pd.read_excel(f'{self.geography_folder}/geography/basins_searchterms_tracking.xlsx')
        
        row = tracking_sheet[tracking_sheet['BCODE'] == basin_code.upper()]
        self.search_term = row['Basin_Specific_Terms'].values[0]

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
            self.driver.get("https://advance-lexis-com.ezproxy.library.tufts.edu/bisnexishome?crid=6537b0c7-d00a-4047-8afa-732967dfba6e&pdmfid=1519360&pdisurlapi=true")
            time.sleep(3)

    def _init_search(self):
        if self.url:
            self.driver.get(self.url)
        news_button = 'body > main > div > ln-navigation > navigation > div.global-nav.light.margin-bottom-30 > div.zones.pagewrapper.product-switcher-navigation.pagewrapper-nexis > nexissearchtabmenu > div > tabmenucomponent > div > div > ul > li:nth-child(3) > button'
        self._click_from_css(news_button) # click to search in News
        news_advancedsearch_button = '#wxbhkkk > ul > li:nth-child(1) > button'
        self._click_from_css(news_advancedsearch_button) # click advanced search, PN: NOT WORKING FOR ME
        self.driver.execute_script("window.scrollTo(0,102)")
        print("Initializing search for " + self.basin_code)
        #print(f"Initializing search for {row['Basin_Name']})

    def _search_box(self):
        self.search_box = '#searchTerms' # css
        #self.search_box = "//input[@type='text' and @id='searchTerms']"
        self.search_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and not hlead(' + self.box_4_keys + ')'
        self._send_keys_from_css(self.search_box, self.search_string) # old
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

    def _search_process(self):
        self.NexisHome()
        self._init_search()
        self._search_box()
        time.sleep(10)
        self.complete_search()
        time.sleep(5)

    
#how to instantiate in main 
'''
from classes.NoLinkClass import NoLinkClass
nlc = NoLinkClass(driver, search_term)

nlc._init_search()
nlc._search_box()
nlc.complete_search()
'''


# plop the below in main code to get search term (formerly box 3 keys), 
'''
import pandas as pd
basin_code = 'tigr' # main should already refer to this

df = pd.read_excel('TrackingSheet_basinterms.xlsx') 
# this sheet is in my class folder, need full file path otherwise
# it's the tracking sheet, but needs headers removed, terms in default (or only) tab
row = df[df['BCODE'] == basin_code.upper()]

search_term = row['Basin_Specific_Terms'].values[0] # maybe the column will be renamed
print(search_term) 
'''
