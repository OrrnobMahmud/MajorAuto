import sys
import time
import random
import requests
import urllib.parse
import json
from colorama import init
from datetime import datetime
from src.headers import headers
from src.auth import get_token
from src.utils import log, log_line, countdown_timer, _banner, _clear, mrh, hju, kng, pth, bru, htm, reset

init(autoreset=True)

class Major:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config(config_file)

        # Load configuration values
        self.use_proxies = self.config.get('use_proxies', False)
        self.auto_do_task = self.config.get('auto_complete_task', False)
        self.auto_play_game = self.config.get('auto_play_game', False)
        self.account_delay = self.config.get('account_delay', 5)
        self.game_delay = self.config.get('game_delay', 3)
        self.wait_time = self.config.get('wait_time', 3600)
        self.data_file = self.config.get('data_file', 'data.txt')
        self.query_tokens = []  # Store query tokens
        self.proxies = self.load_proxies('proxies.txt')
        
        # Show the configuration menu
        self.show_menu()

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
        except FileNotFoundError:
            return {}

    def load_proxies(self, file_name):
        try:
            with open(file_name, 'r') as f:
                proxy_list = f.read().splitlines()
                proxies = []
                for proxy in proxy_list:
                    if '@' in proxy:
                        host_port = proxy.split('@')[1]
                    else:
                        host_port = proxy
                    host, port = host_port.split(':')
                    proxies.append({
                        'http': f'http://{host}:{port}',
                        'https': f'https://{host}:{port}',
                        'host': host,
                        'port': port
                    })
                return proxies
        except Exception as e:
            log(f"Error loading proxies: {e}")
            return []

    def request(self, method, url, token, proxies=None, json=None):
        try:
            response = requests.request(
                method, url, headers=headers(token=token), proxies=proxies, json=json, timeout=20
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return None

    def show_menu(self):
        """Displays the interactive menu to the user for configuration."""
        _clear()
        _banner()
        while True:
            print(f"\n{bru}--- Configuration Menu ---")
            print(f"1. Use Proxies: {hju}{self.use_proxies}")
            print(f"2. Auto Complete Task: {hju}{self.auto_do_task}")
            print(f"3. Auto Play Game: {hju}{self.auto_play_game}")
            print(f"4. Account Delay: {hju}{self.account_delay} seconds")
            print(f"5. Game Delay: {hju}{self.game_delay} seconds")
            print(f"6. Wait Time Between Cycles: {hju}{self.wait_time} seconds")
            print(f"7. Data File: {hju}{self.data_file}")
            print(f"8. Add Query Tokens for Accounts")
            print(f"9. Save & Run Bot")
            print(f"0. Exit")

            choice = input(f"\n{pth}Select an option: ")

            if choice == '1':
                self.use_proxies = not self.use_proxies
            elif choice == '2':
                self.auto_do_task = not self.auto_do_task
            elif choice == '3':
                self.auto_play_game = not self.auto_play_game
            elif choice == '4':
                self.account_delay = int(input(f"{bru}Enter new account delay (in seconds): "))
            elif choice == '5':
                self.game_delay = int(input(f"{bru}Enter new game delay (in seconds): "))
            elif choice == '6':
                self.wait_time = int(input(f"{bru}Enter new wait time (in seconds): "))
            elif choice == '7':
                self.data_file = input(f"{bru}Enter new data file name: ")
            elif choice == '8':
                self.add_query_tokens()
            elif choice == '9':
                self.save_config()
                self.main()
            elif choice == '0':
                sys.exit()
            else:
                print(f"{kng}Invalid choice! Please try again.")

    def add_query_tokens(self):
        """Allows users to dynamically add query tokens."""
        _clear()
        _banner()
        while True:
            print(f"\n{bru}--- Add Query Tokens ---")
            print(f"Current Tokens: {hju}{', '.join(self.query_tokens) if self.query_tokens else 'None'}")
            token = input(f"{pth}Enter a query token (or type 'done' to finish): ")

            if token.lower() == 'done':
                break
            else:
                self.query_tokens.append(token)
                print(f"{hju}Added token: {token}")

    def save_config(self):
        """Saves the current configuration to the config file."""
        config = {
            "use_proxies": self.use_proxies,
            "auto_complete_task": self.auto_do_task,
            "auto_play_game": self.auto_play_game,
            "account_delay": self.account_delay,
            "game_delay": self.game_delay,
            "wait_time": self.wait_time,
            "data_file": self.data_file
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{hju}Configuration saved successfully!")

    def check_in(self, token, proxies=None):
        """Checks in the user using the token."""
        url = "https://major.bot/api/user-visits/visit/"
        result = self.request("POST", url, token, proxies=proxies)

        if result:
            if result.get("status") in [500, 520]:
                return log(f"{kng}Server Major Down")

            if result.get('is_increased'):
                if result.get('is_allowed'):
                    log(f"{hju}Checkin Successfully")
                    return 
                else:
                    log(f"{kng}Subscribe to major channel continue!")
                    return
            else:
                log(f"{kng}Checkin already claimed")
                return 
        else:
            log(f"{kng}Checkin failed")
            return False

    def main(self):
        """Main loop that runs the bot."""
        while True:
            _clear()
            _banner()
            with open(self.data_file, "r") as f:
                accounts = f.read().splitlines()

            log(hju + f"Number of accounts: {bru}{len(accounts)}")
            log_line()

            for idx, account in enumerate(accounts):
                if self.proxies:
                    proxy = random.choice(self.proxies)
                    host = proxy['host']
                    port = proxy['port']
                else:
                    host, port = "No proxy", ""

                log(hju + f"Account: {bru}{idx + 1}/{len(accounts)}")
                log(hju + f"Using proxy: {pth}{host}:{port}")
                log(htm + "~" * 38)

                try:
                    token = get_token(data=account)
                    query = account

                    if token:
                        tele_id = self.get_tele_id_from_query(query)
                        if tele_id:
                            # Your existing task handling logic here
                            self.check_in(token)
                            if self.auto_do_task:
                                tasks = self.get_task(token, "true") + self.get_task(token, "false")
                                for task in tasks:
                                    if not task.get('is_completed'):
                                        self.do_task(token, task.get("id"))

                        if self.auto_play_game:
                            coins_hold = random.randint(800, 915)
                            self.hold_coin(token, coins_hold)
                            countdown_timer(self.game_delay)
                            coins_swipe = random.randint(1900, 2400)
                            self.swipe_coin(token, coins_swipe)
                            countdown_timer(self.game_delay)
                            self.spin(token)
                            self.solve_puzzle(token)
                            
                        log_line()
                    else:
                        log(mrh + f"Error fetching token, please try again!")
                except Exception as e:
                    log(mrh + f"Error: {kng}{e}")
                countdown_timer(self.account_delay)
            countdown_timer(self.wait_time)

if __name__ == "__main__":
    try:
        major = Major()
        major.main()
    except KeyboardInterrupt:
        sys.exit()
