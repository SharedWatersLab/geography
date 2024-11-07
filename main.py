from utils import get_user, full_process

basin = input("Enter basin code: ")
uname = input("Enter username: ")
dload_type = input("Enter download type (either excel or pdf): ")

if __name__ == "__main__":
    paths, current_user = get_user(basin, uname, dload_type)
    full_process(current_user)