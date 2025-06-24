from utils import get_user, full_process

# basin = input("Enter basin code: ")
# uname = input("Enter username: ")
# dload_type = input("Enter download type (either excel or pdf): ")

# if __name__ == "__main__":
#     paths, current_user = get_user(basin, uname, dload_type)
#     full_process(current_user)

def main():
    uname = input("Enter username: ")
    with open("basins.txt", "r") as f:
        basins = [b.strip() for b in f.readlines()]
    print(", ".join(basins))

    selected_basin = input("Choose basin: ")
    if uname: 
        paths, username = get_user(basin, uname)
        full_process(basin, username, paths)
    else:
        print("Please enter a username")

if __name__ == "__main__":
    main()
