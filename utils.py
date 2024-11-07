from geography.classes.UserClass import UserClass
from geography.classes.LoginClass import PasswordManager, WebDriverManager, Login
from geography.classes.NoLinkClass import NoLinkClass
from geography.classes.DownloadClass import Download
import os

def get_user(basin, uname, dload_type):
    basin_code = basin
    master_user = uname
    download_type = dload_type

    currentUser = UserClass(basin_code, master_user, download_type)
    paths = currentUser.getPath(download_type)
    return paths, currentUser

def full_process(current_user):
    if os.path.exists(current_user.download_folder):
        print(f"{current_user.basin}/{current_user.download_type} folder already exists")
    else:
        os.makedirs(current_user.download_folder, exist_ok=True)
        print(f"created folder {current_user.basin}/{current_user.download_type}")
    
    pm = PasswordManager()
    if not pm.password:
        print("No password found, please enter your password")
        password = pm.get_password()
        print("Password saved successfully")
    
    manager = WebDriverManager()
    driver = manager.start_driver()

    login = Login(user_name=current_user.currentUser, password=password, driver_manager=manager, url=None)
    login._init_login()

    nlc = NoLinkClass(driver, current_user.basin, current_user.download_type, current_user)
    nlc._search_process()

    download = Download(
        driver=driver,
        basin_code=current_user.basin,
        user_name=current_user.download_folder,
        index=0,
        login=login,
        nlc=nlc,
        download_folder=current_user.download_folder,
        download_folder_temp=current_user.download_folder_temp,
        status_file=current_user.status_file,
        finished=False,
        url=None,
        timeout=20
    )
    download.main(index=0, basin_code=current_user.basin)