#Example Mac Path: "/Users/dvas22/Desktop/David/www/geography/"
#Example PC Path: "C:/Users/Melissa/Documents/EventsAutomation/geography/examples/excelHandling/excel/basinData.csv"

class UserClass:
    def __init__(self, basin_code, currentUser, download_type):
        self.currentUser = currentUser
        self.download_type = download_type
        self.basin = basin_code
        
    def getName(self):
        print(f'starting {self.download_type} process for {self.currentUser}')  

    def getPath(self, download_type):
        download_type_path = "/" + download_type + "/" 

        if self.currentUser.lower() == "example": 
            #TO DO: Set these three to match your computer
            base_path_prefix = "/Users/change_me/"
            geography_folder = base_path_prefix + "Desktop/change_me/geography/"
            download_folder_temp = base_path_prefix + "This should point to where Chrome downloads files by default"

            #These will set by default
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path  + self.basin + ".csv"

            paths = {
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "david":
            base_path_prefix = "/Users/dvas22/"
            geography_folder = base_path_prefix + "Desktop/David/www/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path + self.basin + ".csv"

            paths = {
                "user_name": "davey",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths
        
        elif self.currentUser.lower() == "david2":
            #/Users/david/Desktop/David/www/geography/status/excel
            #/Users/dvas22/Desktop/David/www/geography/status/excel/aral.csv
            base_path_prefix = "/Users/david/"
            geography_folder = base_path_prefix + "Desktop/David/www/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path + self.basin + ".csv"

            paths = {
                "user_name": "davey",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "selena":
            base_path_prefix = "/Users/selenawallace/" #and then we need everyone to just have a base path
            geography_folder = base_path_prefix + "Documents/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path + self.basin + ".csv"

            paths = {
                "user_name": "swalla05",
                "base_path": base_path_prefix,
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths
        
        elif self.currentUser.lower() == "selena2":
            base_path_prefix = "/Users/alexdorr/"
            geography_folder = base_path_prefix + "Documents/Events_automation/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path + self.basin + ".csv"

            paths = {
                "user_name": "swalla05",
                "base_path": base_path_prefix,
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths
         
        elif self.currentUser.lower() == "melissa":
            #C://Users/Melissa/Downloads
            #C:\Users\Melissa\Downloads
            base_path_prefix = "C://Users/Melissa"
            geography_folder = base_path_prefix + "/Documents/EventsAutomation/geography/"
            download_folder_temp = base_path_prefix + "/Downloads/"
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path + self.basin + ".csv"

            paths = {
                "user_name": "mmccra01",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "rachel": 
            #TO DO: Set these three to match your computer
            base_path_prefix = "/Users/rachelskinner/"
            geography_folder = base_path_prefix + "Downloads/Events_Data/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"

            #These will set by default
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path  + self.basin + ".csv"

            paths = {
                "user_name": "rskinn02",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "sukriti": 
            #TO DO: Set these three to match your computer
            base_path_prefix = "/Users/sukritimahipal/"
            geography_folder = base_path_prefix + "Downloads/Events_automation/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"

            #These will set by default
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path  + self.basin + ".csv"

            paths = {
                "user_name": "smahip01",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "raunaq": 
            #TO DO: Set these three to match your computer
            base_path_prefix = "/Users/raunaqchandrashekar/"
            geography_folder = base_path_prefix + "Downloads/Events_Automation/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"

            #These will set by default
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path  + self.basin + ".csv"

            paths = {
                "user_name": "rchand03",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        elif self.currentUser.lower() == "molly": 
            #TO DO: Set these three to match your computer
            base_path_prefix = "/Users/mollyburger/"
            geography_folder = base_path_prefix + "Documents/Events/Events_automation/geography/"
            download_folder_temp = base_path_prefix + "Downloads/"

            #These will set by default
            download_folder = geography_folder + "data/downloads/" + self.basin + download_type_path
            status_file = geography_folder + "data/status" + download_type_path  + self.basin + ".csv"

            paths = {
                "user_name": "mburge04",
                "geography_folder": geography_folder,
                "download_folder_temp": download_folder_temp,
                "download_folder": download_folder,
                "status_file": status_file,
            }

            return paths

        else: 
            print("user not found")



