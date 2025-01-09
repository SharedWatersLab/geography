from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
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
        #self.current_user = current_user
        #self.geography_folder = f'{self.current_user.geography_folder}geography/' # f"{currentUser.base_path}/geography/geography/search_terms.xlsx"
        self.geography_folder = currentUser.getPath(download_type)["geography_folder"] # assumes where nlc is called userclass has already been defined

        tracking_sheet = pd.read_excel(f'{self.geography_folder}/geography/search_terms.xlsx')
        
        row = tracking_sheet[tracking_sheet['BCODE'] == basin_code.upper()]
        self.search_term = row['Basin_Specific_Terms'].values[0]

        # search keys
        self.box_1_keys = '*water* OR river* OR lake OR dam OR stream OR tributary OR diversion OR irrigation OR pollution OR water quality OR flood! OR drought! OR channel OR canal OR hydroelect! OR reservoir OR groundwater OR aquifer OR drought OR recharge OR "water table" OR "bore hole"'
        self.box_2_keys = 'treaty OR agree! OR negotiat! OR resolution OR commission OR secretariat OR joint management OR basin management OR peace OR accord OR "peace accord" OR settle! OR cooperat! OR collaborat! OR disput! OR conflict! OR disagree! OR sanction! OR war OR troops OR "letter of protest" OR hostility OR "shots fired" OR boycott OR protest! OR appeal OR intent OR reject OR threat! OR force OR coerce OR assault OR fight OR demand OR disapprove OR diploma! OR statement OR memorandum'
        self.box_3_keys = self.search_term
        self.box_4_keys = 'ocean OR navigat! OR nuclear OR "water cannon" OR "light water reactor" OR "mineral water" OR "hold water" OR "cold water" OR "hot water" OR "water canister" OR "water tight" OR " water down" OR "flood of refugees" OR Rivera OR Suez OR Panama OR oil OR drugs OR "three gorges" OR waterski OR watermelon OR dishwater OR waterproof OR "water resistant" OR "water bath" '

    #def get_search_term(self):
    #    print(f"Search Term: {self.search_term}")

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
        self.search_box = '#searchTerms'
        self.search_string = 'hlead(' + self.box_1_keys + ') and hlead(' + self.box_2_keys + ') and hlead(' + self.box_3_keys + ') and not hlead(' + self.box_4_keys + ')'
        self._send_keys_from_css(self.search_box, self.search_string)
        time.sleep(5)

    #click search
    def complete_search(self):
        self.search_button = "//button[@class='btn search' and @data-action='search']"
        self._click_from_xpath(self.search_button)
        time.sleep(10)

        # sometimes, for some reason, it doesn't click the search button
        # check to see if we're on the results page and if not, click again
        self.results_page_substring = '/search/' #'pdsearchterms=hlead' # it changed recently?
        if self.results_page_substring in self.driver.current_url:
            print("clicked search, on results page")
            return
        else: 
            try:
                time.sleep(10)
                self._click_from_xpath(self.search_button)
                print("had to click search button again for some reason") # eventually remove this but I'm curious how often it needs to try again
                time.sleep(3)
            except NoSuchElementException:
                pass
            except StaleElementReferenceException:
                pass
                
        # if the click search issue persists, try encompassing click into a try loop 

    def _search_process(self):
        self.NexisHome()
        self._init_search()
        self._search_box()
        time.sleep(10)
        self.complete_search()
        time.sleep(5)

    
  
# methods below are obsolete due to July 2024 Nexis Uni update

'''
    def _box_1(self):
        self._send_keys_from_css(".searchterm-input-box:nth-child(1)", self.box_1_keys) 
        self._click_from_css(".search-input-row-outline > .dropdown:nth-child(3) > .icon")
        self._click_from_css(".expanded .dropdown-option:nth-child(7) > .option-text")

    def _box_2(self):
        self._send_keys_from_css(".search-input-row:nth-child(2) .searchterm-input-box", self.box_2_keys)
        self._click_from_css(".dropdown:nth-child(5) > .icon")
        self._click_from_css(".expanded .dropdown-option:nth-child(7) > .option-description")

    def _box_3(self):
        self._send_keys_from_css(".search-input-row:nth-child(3) .searchterm-input-box", self.box_3_keys)
        self._click_from_css(".search-input-row:nth-child(3) .dropdown:nth-child(5) > .icon")
        self._click_from_css(".expanded .dropdown-option:nth-child(7) > .option-description")

    def _box_4(self):
        self._click_from_css(".search-input-row:nth-child(4) .dropdown:nth-child(1) > .icon")
        self._click_from_css(".expanded .dropdown-option:nth-child(5) > .option-description")
        self._send_keys_from_css(".search-input-row:nth-child(4) .searchterm-input-box", self.box_4_keys)
        self._click_from_css(".search-input-row:nth-child(4) .dropdown:nth-child(5) > .icon")
        self._click_from_css(".expanded .dropdown-option:nth-child(7) > .option-description")

    #click search
    def complete_search(self):
        search_button_old = ".search" # this is what it used to be
        search_button = '#mainSearch'
        self._click_from_css(search_button)
        
'''  
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
#actually this could all be here if I can figure out how to like...
'''
import pandas as pd # at top of this class
# because maybe search_term doesn't need to be passed in?
    
    def get_search_term(self): #but basin_code would need to be pulled in
        print(f"Search Term: {self.search_term}")

        # this all extra indented because it's underneath NoLinkClass
'''