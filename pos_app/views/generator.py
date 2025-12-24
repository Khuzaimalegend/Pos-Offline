import requests
from bs4 import BeautifulSoup
import re

# Function to fetch data from a given URL
def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# Function to parse and extract email-password pairs from hacker forums
def extract_credentials_from_forum(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    credentials = []

    # Example pattern to match email-password pairs; adjust as needed
    pattern = re.compile(r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b).*?(\b[A-Za-z0-9!@#$%^&*()_+\-=$$$${};":\\|,.<>\/?]*\b)', re.DOTALL)

    for match in pattern.finditer(soup.get_text()):
        email, password = match.groups()
        credentials.append((email, password))

    return credentials

# Function to check if an email and password match a data breach
def check_data_breach(email, password, breach_data):
    for breach in breach_data:
        if email in breach['emails'] and password in breach['passwords']:
            return True
    return False

# Function to scan data breaches for Minecraft accounts
def scan_data_breaches_for_minecraft_accounts():
    # List of data breach sources (example URLs)
    breach_sources = [
        'https://www.bleepingcomputer.com/forums/t/563860/minecraft-hacked-more-than-1800-minecraft-account-credentials-leaked/',
        'https://www.reddit.com/r/hypixel/comments/1kurojj/minecraft_account_hacked/',
        'https://www.reddit.com/r/Minecraft/comments/1lgzaw3/microsoft_confirmed_im_the_rightful_owner_of_my/',
        'https://www.reddit.com/r/Minecraft/comments/1o016a6/minecraft_account_hacked/',
        'https://www.reddit.com/r/LinusTechTips/comments/1ieo3dx/microsoft_lets_hackers_steal_accounts_permanently/',
        'https://www.reddit.com/r/Minecraft/comments/1lfns7x/minecraft_account_hacked_heres_how_i_got_it_back/',
        'https://www.reddit.com/r/Minecraft/comments/1707bep/minecraft_account_got_hacked_and_stolen/',
        'https://www.reddit.com/r/onions/comments/1jop12d/where_can_i_find_the_data_breach_forum/',
        'https://www.reddit.com/r/Minecraft/comments/1nfk3s1/my_friends_minecraft_account_got_hacked_and_perma/',
        'https://www.reddit.com/r/MinecraftLeaks/comments/1jc3681/minecraft_live_2025_content_major_leaks/',
        'https://www.reddit.com/r/hacking/comments/1lg9thn/is_there_a_new_breachforums_domain/',
        'https://www.reddit.com/r/Minecraft/comments/1izggo8/minecraft_account_got_hacked/',
        'https://www.reddit.com/r/hacking/comments/1k3uo6x/breachforums/',
        'https://www.reddit.com/r/MinecraftLeaks/comments/1iy5rwx/potential_new_insider_account/',
        'https://www.reddit.com/r/Minecraft/comments/1jza46z/has_anyone_ever_successfully_recovered_a_hacked/'
    ]

    all_breach_data = []

    for source in breach_sources:
        html_content = fetch_data(source)
        if html_content:
            credentials = extract_credentials_from_forum(html_content)
            all_breach_data.extend(credentials)

    # Example list of Minecraft accounts (email, password) to check
    minecraft_accounts = [
        ('example1@minecraft.com', 'password1'),
        ('example2@minecraft.com', 'password2'),
        # Add more accounts as needed
    ]

    found_accounts = []

    for email, password in minecraft_accounts:
        if check_data_breach(email, password, all_breach_data):
            found_accounts.append((email, password))

    return found_accounts

# Example usage
if __name__ == "__main__":
    found_accounts = scan_data_breaches_for_minecraft_accounts()
    if found_accounts:
        print("Found Minecraft accounts in data breaches:")
        for email, password in found_accounts:
            print(f"Email: {email}, Password: {password}")
    else:
        print("No Minecraft accounts found in data breaches.")