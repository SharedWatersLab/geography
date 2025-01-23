from geography.classes.UserClass import UserClass
from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download
from geography.classes.SearchClass import newsearch
from geography import RangesDownload
import os
import time
import re

start_date = '06/30/2008'
end_date = '06/30/2024'

def get_user(basin_code, uname, dload_type):
    basin_code = basin_code
    master_user = uname
    download_type = dload_type

    currentUser = UserClass(basin_code, master_user, download_type)
    paths = currentUser.getPath(download_type)
    return paths, currentUser

def full_process(current_user, paths):

    base_path = paths['base_path']
    user_name = paths["user_name"]
    geography_folder = paths["geography_folder"]
    download_folder_temp = paths["download_folder_temp"]
    download_folder = paths["download_folder"]
    status_file = paths["status_file"]

    if os.path.exists(download_folder):
        print(f"{current_user.basin_code}/{current_user.download_type} folder already exists")
    else:
        os.makedirs(download_folder, exist_ok=True) # this isn't exactly right is it? - Yes, I added exists_ok=True to avoid errors if the folder already exists
        print(f"created folder {current_user.basin_code}/{current_user.download_type}")

    generic_status_path = f"{geography_folder}data/status/pdf/new_status.csv" # this is a blank df
    # this file will need to be in the repository until we've updated download class to not use status_file
    if os.path.exists(status_file): # though in the future we'll want to just not call in status_file
        pass
    else:
        status_file = generic_status_path # if it doesn't exist, just use the blank one...

    if os.path.exists(current_user.download_folder):
        print(f"{current_user.basin_code}/{current_user.download_type} folder already exists")
    else:
        os.makedirs(current_user.download_folder, exist_ok=True)
        print(f"created folder {current_user.basin_code}/{current_user.download_type}")
    
    pm = PasswordManager()
    if not pm.password:
        print("No password found, please enter your password")
        password = pm.get_password()
        print("Password saved successfully")
    
    manager = WebDriverManager()
    driver = manager.start_driver()

    login = Login(user_name=current_user.currentUser, password=password, driver_manager=manager, url=None)
    login._init_login()

    nlc = NoLinkClass(driver, current_user.basin_code, current_user.download_type, current_user)

    download = Download(
        driver=driver,
        basin_code=current_user.basin_code,
        user_name=current_user.download_folder,
        index=0,
        login=login,
        nlc=nlc,
        download_type='pdf',
        download_folder=current_user.download_folder,
        download_folder_temp=current_user.download_folder_temp,
        status_file=current_user.status_file,
        finished=False,
        url=None,
        timeout=20
    )
    # download.main(index=0, basin_code=current_user.basin_code)
    
    search = newsearch(nlc, download)
    search.search(start_date, end_date)

    time.sleep(5)
    download.DownloadSetup()

    dialog_box = RangesDownload.dialog(download, current_user)
    ranges_to_download = RangesDownload.get_ranges(download, current_user.download_folder) 

    # and this is the process
    try:
        for r in ranges_to_download:
            dialog_box.check_clear_downloads(r)
            dialog_box.download_dialog(r)
            print(f"preparing to download range {r}")

            download.wait_for_download()
            
            # Find matching file
            default_filename = [f for f in os.listdir(current_user.download_folder_temp) if re.match(r"Files \(\d+\)\.ZIP", f)]

            if default_filename:  # If we found any matching files
                # Use the first matching file
                default_download_path = os.path.join(current_user.download_folder_temp, default_filename[0])
                geography_download_path = f"{current_user.download_folder}{current_user.basin_code}_results_{r}.ZIP"

                # Check if file exists and move it
                if os.path.isfile(default_download_path):
                    os.rename(default_download_path, geography_download_path)
                    print(f"moving file to {geography_download_path}")

            download.reset()
    finally:
        ranges_to_download = RangesDownload.get_ranges(download, current_user.download_folder) # run this again when loop is complete

        # get_ranges() will return not_downloaded_ranges as a list

        if not ranges_to_download:
            print("all ranges for basin downloaded")

        else:
            print("ranges remaining:")
            print(ranges_to_download)