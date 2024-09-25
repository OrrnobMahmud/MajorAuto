import os
import json
import time
from datetime import datetime
from colorama import *

mrh = Fore.LIGHTRED_EX
pth = Fore.LIGHTWHITE_EX
hju = Fore.LIGHTGREEN_EX
kng = Fore.LIGHTYELLOW_EX
bru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL
htm = Fore.LIGHTBLACK_EX

last_log_message = None

def _banner():
    banner = f"""{Fore.GREEN}
   ___                   _      __  __      _                 _ 
  / _ \ _ _ _ _ _ _  ___| |__  |  \/  |__ _| |_  _ __ _  _ __| |
 | (_) | '_| '_| ' \/ _ \ '_ \ | |\/| / _` | ' \| '  \ || / _` |
  \___/|_| |_| |_||_\___/_.__/ |_|  |_\__,_|_||_|_|_|_\_,_\__,_|
                                                                
    Auto Claim Bot For Blum - Orrnob's Drop Automation
    Author  : Orrnob Mahmud : Thanks to @SDSProjects
    Github  : https://github.com/OrrnobMahmud
    Telegram: https://t.me/verifiedcryptoairdops
        {Style.RESET_ALL}"""

def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def read_config():
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    with open(config_path, 'r') as file:
        try:
            config_content = file.read()
            return json.loads(config_content)
        except json.JSONDecodeError as e:
            return {}
        
def log(message, **kwargs):
    global last_log_message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flush = kwargs.pop('flush', False)
    end = kwargs.pop('end', '\n')
    if message != last_log_message:
        print(f"{htm}[{current_time}] {message}", flush=flush, end=end)
        last_log_message = message

def log_line():
    print(pth + "~" * 60)

def countdown_timer(seconds):
    while seconds:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        h = str(h).zfill(2)
        m = str(m).zfill(2)
        s = str(s).zfill(2)
        print(f"{pth}please wait until {h}:{m}:{s} ", flush=True, end="\r")
        seconds -= 1
        time.sleep(1)
    print(f"{pth}please wait until {h}:{m}:{s} ", flush=True, end="\r")

def _number(number):
    return "{:,.0f}".format(number)
