
from auth import make_admin

username = input("Enter your existing username: ").strip()

if make_admin(username):
    print(f"Success! {username} is now an Admin.")
else:
    print("Username not found. Check your username and try again.")
