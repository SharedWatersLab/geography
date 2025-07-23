from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.DownloadClass import Download, DownloadFailedException
from geography.classes.SearchClass import Search

import os
import shutil
import time
import re
from tqdm import tqdm
import datetime
from pathlib import Path

start_date = '06/30/2008'
end_date = '04/30/2025'

_password_cache = None

def get_user(basin_code, uname):
    # Use standard paths that work for any user
    base_path = os.path.expanduser("~")
    geography_folder = "./"
    download_folder_temp = os.path.join(base_path, "Downloads")
    download_folder = os.path.join(geography_folder, "data", "downloads", basin_code)
    #download_folder = os.path.join(base_path, "Box", basin_code) # testing if we can download to Box drive from base path directly

    paths = {
        "base_path": base_path,
        "user_name": uname,
        "geography_folder": geography_folder,
        "download_folder_temp": download_folder_temp,
        "download_folder": download_folder,
    }
    
    return paths, uname

def logout_clearcookies(download):
    sign_in_button = "//button[@id='SignInRegisterBisNexis']"
    try:
        download._click_from_xpath(sign_in_button)
        print("logging out")
    except Exception as e:
        #download.handle_popups() # maybe try this, sometimes the problem is the download dialog
        find_sign_in = download.driver.find_element_by_xpath(sign_in_button)
        download.driver.execute_script("return arguments[0].scrollIntoView(true);", find_sign_in)        
    download.driver.delete_all_cookies()
    print("deleting cookies")

def reset(download, login, search):
    logout_clearcookies(download)
    time.sleep(3)
    login._init_login()
    search.search_process(start_date, end_date)
    time.sleep(5)
    download.DownloadSetup()

# def move_failed_downloads(download_folder, basin_code):
#     if os.path.exists(download_folder) and os.listdir(download_folder):
#         timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#         #give the new folder a name
#         failed_folder = f"{basin_code}_failed_{timestamp}"
        
#         try:
#             # rename download folder (to "move" its contents to failed folder)
#             os.rename(download_folder, failed_folder)
#             print(f"Moved failed downloads to: {failed_folder}")
            
#             # need to recreate an empty download_folder 
#             os.makedirs(download_folder)

#             # now move failed folder into the new empty download folder lol
#             new_failed_folder_path = os.path.join(download_folder, failed_folder)
#             os.rename(failed_folder, new_failed_folder_path)
            
#         except Exception as e:
#             print(f"Error moving folder: {e}")
#     else:
#         print(f"Download folder {download_folder} doesn't exist or is empty, nothing to move")

def full_process(basin_code, username, paths):
    """
    Main download process function.
    
    Args:
        basin_code (str): The basin code for the geographic area
        username (str): Username from streamlit input
        paths (dict): Dictionary containing file paths
    """
    print("~" * 27)
    print(f"Starting download for {basin_code}!")
    print("~" * 27)

    download_folder = paths["download_folder"]
    download_folder_temp = paths["download_folder_temp"]
    
    # Create download folder if it doesn't exist
    if os.path.exists(download_folder):
        print(f"{basin_code} folder already exists")
    else:
        os.makedirs(download_folder, exist_ok=True) 
        print(f"created folder {basin_code}")
    
    # Password management
    global _password_cache

    if _password_cache is None:
        pm = PasswordManager()
        if not pm.password:
            print("No password found, please enter your password")
            password = pm.get_password()
            print("Password saved successfully")
        else:
            password = pm.password
        _password_cache = password
    else:
        password = _password_cache
        print("Using cached password")
    
    # WebDriver setup
    manager = WebDriverManager()
    driver = manager.start_driver()

    # Login - using consistent username variable
    login = Login(user_name=username, password=password, driver_manager=manager, url=None)
    login._init_login()

    # Search process
    search = Search(driver, basin_code, username, paths["geography_folder"])
    search.search_process(start_date, end_date)  # Note: These variables need to be set at the top of utils, passed as parameters


    # Download setup - streamlined parameters
    download = Download(
        driver=driver,
        basin_code=basin_code,
        username=username,
        login=login,
        search=search,
        download_folder=download_folder,
        download_folder_temp=download_folder_temp,
        finished=False,
        url=None,
        timeout=20
    )
    

    time.sleep(5)
    download.DownloadSetup()

    # Main download process
    before = time.time()

    if download.get_result_count() > 150000 and not getattr(search, 'already_switched_to_riparian', False):
        search.switch_to_riparian()
        search.already_switched_to_riparian = True  # Prevent re-switching
        search.search_process(start_date, end_date)
        download.DownloadSetup()

    consecutive_failures = 0
    failure_threshold = 5 # higher consecutive error threshold

    running=True
    #while True: #
    while running:

        ranges_to_download = download.get_ranges()
    
        # Check if we're done
        if not ranges_to_download:
            print(f"All ranges for basin {basin_code} downloaded!")
            logout_clearcookies(download)
            driver.close()
            running = False
            break
        
        print(f"Attempting to download {len(ranges_to_download)} ranges")

        if consecutive_failures == failure_threshold: # for now change what happens when it fails. do not switch search method.
            # print(f"Too many consecutive failures ({consecutive_failures}), switching search method...")
            print(f"{basin_code} downloads failed {failure_threshold} times in a row, please try another basin")
            logout_clearcookies(download)
            driver.close() # now it will just stop
            #in_progress_download_folder = f"{download_folder}_failed_in_progress"
            #os.rename(download_folder, in_progress_download_folder) # add a label to indicate downloads are not complete for this basin
            running=False

        for i, r in enumerate(tqdm(ranges_to_download)):
            try:
                if i > 0: # if it's not the first loop
                    reset(download, login, search) # reset, which includes login, search, and setup

                # if i == len(ranges_to_download) - 1:  # if it's the last loop
                #     print("Re-checking ranges before final download...")
                #     updated_ranges = download.get_ranges()
                #     if updated_ranges and r != updated_ranges[-1]:
                #         print(f"Last range updated from {r} to {updated_ranges[-1]}")
                #         r = updated_ranges[-1]  # Use the updated last range
                
                download.check_clear_downloads(r)
                download.download_dialog(r)
                print(f"preparing to download range {r}")

                download.wait_for_download()
                download.move_file(r)

                after = time.time()
                elapsed = after - before

                consecutive_failures = 0 # reset on success
                print("Time elapsed since process began (minutes): ", elapsed/60)

            except DownloadFailedException:
                consecutive_failures += 1
                print(f"Download failed for range {r} after {consecutive_failures} consecutive failure(s)")
                break
                #continue
            
            except Exception as e:
                #print(f"Error occurred with range {r}: {e}")
                continue  # Try next range
        
            
    # finally:
    #     ranges_to_download = RangesDownload.get_ranges(download, download_folder) # run this again when loop is complete

    #     # get_ranges() will return not_downloaded_ranges as a list
    #     if not ranges_to_download:
    #         print("all ranges for basin downloaded")
    #     else:
    #         print("ranges remaining:")
    #         print(ranges_to_download)