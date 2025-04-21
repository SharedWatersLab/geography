import time
import platform
from selenium.webdriver.common.keys import Keys 

from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download

class newsearch:
    def __init__(self, nlc, download):
        self.nlc=nlc
        self.download=download

    def search(self, start_date, end_date):

        self.nlc.NexisHome()
        self.nlc._init_search()
        self.nlc._search_box()
        time.sleep(10)
        # set date here
        nlc_startdate = "//input[@class='dateFrom' and @aria-label='From']"
        nlc_enddate = "//input[@class='dateTo' and @aria-label='To']"

        system = platform.system().lower()
        if system == "darwin":
            select_all = Keys.COMMAND, "a"
        elif system == "windows":
            select_all = Keys.CONTROL, "a"

        self.download._send_keys_from_xpath(nlc_startdate, select_all)
        self.download._send_keys_from_xpath(nlc_startdate, start_date)

        self.download._send_keys_from_xpath(nlc_enddate, select_all)
        self.download._send_keys_from_xpath(nlc_enddate, end_date)

        #continue
        self.nlc.complete_search()
        time.sleep(5)

#search = newsearch(nlc, download)