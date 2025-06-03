from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download
from geography.classes.SearchClass import newsearch
from geography import RangesDownload
import os
import time
import re
from tqdm import tqdm

start_date = '06/30/2008'
end_date = '04/30/2025'

def get_user(basin_code, uname):
    # Use standard paths that work for any user
    base_path = os.path.expanduser("~")
    geography_folder = "./"
    download_folder_temp = os.path.join(base_path, "Downloads")
    download_folder = os.path.join(geography_folder, "data", "downloads", basin_code)
    
    paths = {
        "base_path": base_path,
        "user_name": uname,
        "geography_folder": geography_folder,
        "download_folder_temp": download_folder_temp,
        "download_folder": download_folder,
    }
    
    return paths, uname

def full_process(basin_code, username, paths):
    """
    Main download process function.
    
    Args:
        basin_code (str): The basin code for the geographic area
        username (str): Username from streamlit input
        paths (dict): Dictionary containing file paths
    """
    
    download_folder = paths["download_folder"]
    download_folder_temp = paths["download_folder_temp"]
    
    # Create download folder if it doesn't exist
    if os.path.exists(download_folder):
        print(f"{basin_code} folder already exists")
    else:
        os.makedirs(download_folder, exist_ok=True) 
        print(f"created folder {basin_code}")

    # REMOVED: All status file related code (commented out sections)
    # REMOVED: All download_type references since we're eliminating that concept
    
    # Password management
    pm = PasswordManager()
    if not pm.password:
        print("No password found, please enter your password")
        password = pm.get_password()
        print("Password saved successfully")
    
    # WebDriver setup
    manager = WebDriverManager()
    driver = manager.start_driver()

    # Login - using consistent username variable
    login = Login(user_name=username, password=password, driver_manager=manager, url=None)
    login._init_login()

    # NoLinkClass - pass geography_folder from paths
    nlc = NoLinkClass(driver, basin_code, username, paths["geography_folder"])

    # Download setup - streamlined parameters
    download = Download(
        driver=driver,
        basin_code=basin_code,
        username=username, 
        login=login,
        nlc=nlc,
        download_folder=download_folder,
        download_folder_temp=download_folder_temp,
        finished=False,
        url=None,
        timeout=20
    )
    
    # Search process
    search = newsearch(nlc, download)
    search.search(start_date, end_date)  # Note: These variables need to be passed as parameters

    time.sleep(5)
    download.DownloadSetup()

    # Download ranges setup
    dialog_box = RangesDownload.dialog(download, username, basin_code, download_folder, download_folder_temp)
    ranges_to_download = RangesDownload.get_ranges(download, download_folder) 

    # Main download process
    before = time.time()

    while True:
        # Get ranges that still need downloading
        ranges_to_download = RangesDownload.get_ranges(download, download_folder)
        
        if not ranges_to_download:
            print("all ranges for basin downloaded")
            break
        
        print(f"Attempting to download {len(ranges_to_download)} ranges")
    

        try:
            for i, r in enumerate(tqdm(ranges_to_download)):
                #
                if i == len(ranges_to_download) - 1:  # Last range
                    print("Re-checking ranges before final download...")
                    updated_ranges = RangesDownload.get_ranges(download, download_folder)
                    if updated_ranges and r != updated_ranges[-1]:
                        print(f"Last range updated from {r} to {updated_ranges[-1]}")
                        r = updated_ranges[-1]  # Use the updated last range
                
                if i > 0: # if it's not the first loop
                    download.reset() # reset, which includes login, search, and setup

                dialog_box.check_clear_downloads(r)
                dialog_box.download_dialog(r)
                print(f"preparing to download range {r}")

                download.wait_for_download()
                download.move_file(r)
                
                # # Find matching file
                # default_filename = [f for f in os.listdir(download_folder_temp) if re.match(r"Files \(\d+\)\.ZIP", f)]

                # if default_filename:  # If we found any matching files
                #     # Use the first matching file
                #     default_download_path = os.path.join(download_folder_temp, default_filename[0])
                #     geography_download_path = os.path.join(download_folder, f"{basin_code}_results_{r}.ZIP")

                #     # Check if file exists and move it
                #     if os.path.isfile(default_download_path):
                #         os.rename(default_download_path, geography_download_path)
                #         print(f"moving file to {geography_download_path}")

                after = time.time()
                elapsed = after - before
                print("Time elapsed since process began (minutes): ", elapsed/60)

        except Exception as e:
            print(f"Error occurred: {e}")
            
            
    # finally:
    #     ranges_to_download = RangesDownload.get_ranges(download, download_folder) # run this again when loop is complete

    #     # get_ranges() will return not_downloaded_ranges as a list
    #     if not ranges_to_download:
    #         print("all ranges for basin downloaded")
    #     else:
    #         print("ranges remaining:")
    #         print(ranges_to_download)