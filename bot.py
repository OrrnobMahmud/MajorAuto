import os
import re
import json
import httpx
import anyio
import random
import asyncio
import argparse
import aiofiles
import aiofiles.os
import python_socks
from glob import glob
import aiofiles.ospath
from pathlib import Path
from urllib.parse import parse_qs
from base64 import urlsafe_b64decode
from datetime import datetime, timezone
from colorama import init as inits, Fore, Style
from models import (
    insert,
    get_by_id,
    Config,
    init,
    update_balance,
    update_token,
    update_useragent,
)
from httpx_socks import AsyncProxyTransport
from fake_useragent import UserAgent

log_file = "http.log"
proxy_file = "proxies.txt"
data_file = "data.txt"
token_file = "tokens.json"
config_file = "config.json"
inits(autoreset=True)
red = Fore.LIGHTRED_EX
blue = Fore.LIGHTBLUE_EX
green = Fore.LIGHTGREEN_EX
yellow = Fore.LIGHTYELLOW_EX
black = Fore.LIGHTBLACK_EX
white = Fore.LIGHTWHITE_EX
reset = Style.RESET_ALL
line = white + "~" * 50


class MajTod:
    def __init__(self, id: int, query: str, proxies: list, cfg=Config):
        marin = lambda data: {key: value[0] for key, value in parse_qs(data).items()}
        parser = marin(query)
        user = parser.get("user")
        self.p = id
        self.cfg = cfg
        self.valid = True
        if user is None:
            self.valid = False
            self.log(f"{red}The data entered has wrong format !")
            return None
        self.user = {}
        uid = re.search(r"\"id\"\:(.*?)\,", user)
        first_name = re.search(r"\"first_name\"\:\"(.*?)\"\,", user)
        if uid:
            self.user["id"] = uid.group(1)
            if first_name:
                self.user["first_name"] = first_name.group(1)
        else:
            self.valid = False
            self.log(f"{red}The data entered has wrong format !")
            return None
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Linux; Android 11; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.79 Mobile Safari/537.36",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en,id-ID;q=0.9,id;q=0.8,en-US;q=0.7",
        }
        self.query = query
        self.proxies = proxies
        if len(self.proxies) > 0:
            proxy = self.get_random_proxy(id, False)
            transport = AsyncProxyTransport.from_url(proxy)
            self.ses = httpx.AsyncClient(transport=transport, timeout=1000)
        else:
            self.ses = httpx.AsyncClient(timeout=1000)

    def log(self, msg):
        now = datetime.now().isoformat().split("T")[1].split(".")[0]
        print(
            f"{black}[{now}]{white}-{blue}[{white}acc {self.p + 1}{blue}]{white} {msg}{reset}"
        )

    async def ipinfo(self):
        ipinfo1_url = "https://ipapi.co/json/"
        ipinfo2_url = "https://ipwho.is/"
        ipinfo3_url = "https://freeipapi.com/api/json"
        try:
            res = await self.ses.get(ipinfo1_url)
            ip = res.json().get("ip")
            country = res.json().get("country")
            if not ip:
                res = await self.ses.get(ipinfo2_url)
                ip = res.json().get("ip")
                country = res.json().get("country_code")
                if not ip:
                    res = await self.ses.get(ipinfo3_url)
                    ip = res.json().get("ipAddress")
                    country = res.json().get("countryCode")
            self.log(f"{green}ip : {white}{ip} {green}country : {white}{country}")
        except json.decoder.JSONDecodeError:
            self.log(f"{green}ip : {white}None {green}country : {white}None")

    def get_random_proxy(self, isself, israndom=False):
        if israndom:
            return random.choice(self.proxies)
        return self.proxies[isself % len(self.proxies)]

    async def http(self, url, headers, data=None):
        while True:
            try:
                await asyncio.sleep(0.5)
                if not await aiofiles.ospath.exists(log_file):
                    async with aiofiles.open(log_file, "w") as w:
                        await w.write("")
                logsize = await aiofiles.ospath.getsize(log_file)
                if logsize / 1024 / 1024 > 1:
                    async with aiofiles.open(log_file, "w") as w:
                        await w.write("")
                if data is None:
                    res = await self.ses.get(url, headers=headers)
                elif data == "":
                    res = await self.ses.post(url, headers=headers)
                else:
                    res = await self.ses.post(url, headers=headers, data=data)
                async with aiofiles.open(log_file, "a", encoding="utf-8") as hw:
                    await hw.write(f"{res.text}\n")
                if "<title>" in res.text:
                    self.log(f"{yellow}failed get json response !")
                    await countdown(3)
                    continue
                if (
                    "Rate limit exceeded." in res.text
                    or "Internal Server Error" in res.text
                ):
                    self.log(f"{yellow}failed get json response !")
                    await countdown(3)
                    continue

                return res
            except (
                httpx.ProxyError,
                python_socks._errors.ProxyTimeoutError,
                python_socks._errors.ProxyError,
                python_socks._errors.ProxyConnectionError,
            ):
                proxy = self.get_random_proxy(0, israndom=True)
                transport = AsyncProxyTransport.from_url(proxy)
                self.ses = httpx.AsyncClient(transport=transport)
                self.log(f"{yellow}proxy error,selecting random proxy !")
                await asyncio.sleep(3)
                continue
            except httpx.NetworkError:
                self.log(f"{yellow}network error !")
                await asyncio.sleep(3)
                continue
            except httpx.TimeoutException:
                self.log(f"{yellow}connection timeout !")
                await asyncio.sleep(3)
                continue
            except (httpx.RemoteProtocolError, anyio.EndOfStream):
                self.log(f"{yellow}connection close without response !")
                await asyncio.sleep(3)
                continue

    def is_expired(self, token):
        if token is None or isinstance(token, bool):
            return True
        header, payload, sign = token.split(".")
        deload = urlsafe_b64decode(payload + "==")
        jeload = json.loads(deload)
        now = (datetime.now().timestamp()) + 300
        if now > jeload.get("exp"):
            return True
        return False

    async def login(self):
        data = {
            "init_data": self.query,
        }
        auth_url = "https://major.glados.app/api/auth/tg/"
        res = await self.http(auth_url, self.headers, json.dumps(data))
        token = res.json().get("access_token")
        if token is None:
            return False
        # return token
        self.headers["authorization"] = f"Bearer {token}"
        await update_token(id=self.user.get("id"), token=token)

    async def start(self):
        if not self.valid:
            return int(datetime.now().timestamp()) + 8 * 3600
        if len(self.proxies) > 0:
            await self.ipinfo()
        if not await aiofiles.ospath.exists(token_file):
            async with aiofiles.open(token_file, "w") as w:
                await w.write(json.dumps({}))

        uid = self.user.get("id")
        first_name = self.user.get("first_name")
        res = await get_by_id(uid)
        if res is None:
            await insert(uid, first_name)
            res = await get_by_id(uid)
        self.log(f"{green}login as {white}{first_name}")
        token = res.get("token")
        useragent = res.get("useragent")
        if not useragent:
            useragent = UserAgent().random
            await update_useragent(uid, useragent)
        self.headers["user-agent"] = useragent
        self.headers["authorization"] = f"Bearer {token}"
        if self.is_expired(token):
            token = await self.login()
            if token is False:
                return int(datetime.now().timestamp()) + 8 * 3600
        streak_url = "https://major.bot/api/user-visits/streak/"
        visit_url = "https://major.bot/api/user-visits/visit/"
        res = await self.http(streak_url, self.headers)
        streak = res.json().get("streak")
        self.log(f"{green}streak : {white}{streak}")
        await self.http(visit_url, self.headers, "")
        await self.getme()
        if self.cfg.auto_task:
            await self.solve_task()
        min_countdown = await self.playgame()
        result = await self.getme()
        return min_countdown

    async def solve_task(self):
        urls = [
            "https://major.bot/api/tasks/?is_daily=true",
            "https://major.bot/api/tasks/?is_daily=false",
        ]
        for url in urls:
            solve_url = "https://major.bot/api/tasks/"
            res = await self.http(url, self.headers)
            for i in res.json():
                id = i.get("id")
                title = i.get("title")
                solve_data = {"task_id": id}
                res = await self.http(solve_url, self.headers, json.dumps(solve_data))
                detail = res.json().get("detail")
                is_complete = res.json().get("is_completed")
                if detail is not None:
                    if detail == "Task is already completed":
                        self.log(f"{yellow}already completed task {white}{title}")
                        continue
                if is_complete:
                    self.log(f"{green}successfully completed task {white}{title}")
                    await countdown(3)
                    continue
                self.log(f"{red}failed to complete task {white}{title}")

    async def getme(self):
        uid = self.user.get("id")
        first_name = self.user.get("first_name")
        url = "https://major.bot/api/users/" + str(uid) + "/"
        res = await self.http(url, self.headers)
        balance = res.json().get("rating")
        await update_balance(uid, balance)
        self.log(f"{green}balance : {white}{balance}")

    async def playgame(self):
        roulette_url = "https://major.glados.app/api/roulette/"
        bonus_url = "https://major.glados.app/api/bonuses/coins/"
        swipe_coin_url = "https://major.glados.app/api/swipe_coin/"
        puzzle_url = "https://major.bot/api/durov/"
        puzzle_answer_url = "https://akasakaid.github.io/major/durov.json"
        timestamps = []
        for i in range(2):
            res = await self.http(puzzle_url, self.headers)
            detail = res.json().get("detail")
            if detail is not None:
                next_timestamp = int(detail.get("blocked_until"))
                timestamps.append(next_timestamp)
                next_isoformat = (
                    datetime.fromtimestamp(next_timestamp).isoformat(" ").split(".")[0]
                )
                self.log(
                    f"{yellow}next time to play puzzel game : {white}{next_isoformat}"
                )
            else:
                _headers = {"User-Agent": "Marin Kitagawa"}
                res = await self.http(puzzle_answer_url, _headers)
                tday = datetime.now(tz=timezone.utc).isoformat().split("T")[0]
                answer = res.json().get(tday)
                if answer is None:
                    self.log(
                        f"{yellow}The puzzle answers for today have not been updated yet."
                    )
                else:
                    res = await self.http(puzzle_url, self.headers, json.dumps(answer))
                    correct = res.json().get("correct", "")
                    if len(correct) == 4:
                        self.log(f"{green}get reward from puzzle game : {white}5000")
                    else:
                        self.log(
                            f"{red}failed get reward from puzzle game, maybe asnwer is wrong"
                        )
            res = await self.http(roulette_url, self.headers)
            detail = res.json().get("detail")
            if detail is not None:
                next_timestamp = int(detail.get("blocked_until"))
                timestamps.append(next_timestamp)
                next_isoformat = (
                    datetime.fromtimestamp(next_timestamp).isoformat(" ").split(".")[0]
                )
                self.log(
                    f"{yellow}next time to play roulette game : {white}{next_isoformat}"
                )
            else:
                res = await self.http(roulette_url, self.headers, "")
                reward = res.json().get("rating_award")
                self.log(f"{green}get reward from roulette : {white}{reward}")
            res = await self.http(bonus_url, self.headers)
            detail = res.json().get("detail")
            if detail is not None:
                next_timestamp = int(detail.get("blocked_until"))
                timestamps.append(next_timestamp)
                next_isoformat = (
                    datetime.fromtimestamp(next_timestamp).isoformat(" ").split(".")[0]
                )
                self.log(
                    f"{yellow}next time to play hold coin game : {white}{next_isoformat}"
                )
            else:
                coin = random.randint(900, 915)
                bonus_data = {"coins": coin}
                res = await self.http(bonus_url, self.headers, json.dumps(bonus_data))
                success = res.json().get("success")
                if success:
                    self.log(f"{green}get reward from hold coin game : {white}{coin}")
                else:
                    self.log(f"{red}failed to get reward from hold coin game !")
            res = await self.http(swipe_coin_url, self.headers)
            detail = res.json().get("detail")
            if detail is not None:
                next_timestamp = int(detail.get("blocked_until"))
                timestamps.append(next_timestamp)
                next_isoformat = (
                    datetime.fromtimestamp(next_timestamp).isoformat(" ").split(".")[0]
                )
                self.log(
                    f"{yellow}next time to play swap game : {white}{next_isoformat}"
                )
            else:
                coin = random.randint(2900, 3000)
                swipe_data = {"coins": coin}
                res = await self.http(
                    swipe_coin_url, self.headers, json.dumps(swipe_data)
                )
                success = res.json().get("success")
                if success:
                    self.log(f"{green}get reward from swap game : {white}{coin}")
                else:
                    self.log(f"{red}failed get reward from swap game !")
            if len(timestamps) >= 3:
                break
        return min(timestamps)


async def countdown(t):
    for i in range(t, 0, -1):
        minute, seconds = divmod(i, 60)
        hour, minute = divmod(minute, 60)
        seconds = str(seconds).zfill(2)
        minute = str(minute).zfill(2)
        hour = str(hour).zfill(2)
        print(f"waiting for {hour}:{minute}:{seconds} ", flush=True, end="\r")
        await asyncio.sleep(1)


async def get_data():
    async with aiofiles.open(data_file) as w:
        read = await w.read()
        datas = [i for i in read.splitlines() if len(i) > 10]
    async with aiofiles.open(proxy_file) as w:
        read = await w.read()
        proxies = [i for i in read.splitlines() if len(i) > 5]
    return datas, proxies


async def bound(sem, data):
    async with sem:
        return await MajTod(*data).start()


async def main():
    global data_file, proxy_file
    temp_worker = os.cpu_count() / 2
    arg = argparse.ArgumentParser()
    arg.add_argument("--marin", action="store_true")
    arg.add_argument(
        "--data", "-D", default="data.txt", help="File containing account data"
    )
    arg.add_argument(
        "--proxy",
        "-P",
        default="proxies.txt",
        help="A file containing a list of proxies",
    )
    arg.add_argument("--action", "-A", help="Argument to select the menu directly")
    arg.add_argument("--worker", "-W", type=int, help="Worker")
    args = arg.parse_args()
    proxy_file = args.proxy
    data_file = args.data
    opt = args.action
    worker = args.worker
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
    if not await aiofiles.ospath.exists(proxy_file):
        async with aiofiles.open(proxy_file, "a") as w:
            pass
    if not await aiofiles.ospath.exists(data_file):
        async with aiofiles.open(data_file, "a") as w:
            pass
    if not await aiofiles.ospath.exists(config_file):
        async with aiofiles.open(config_file, "w") as w:
            await w.write(json.dumps({"auto_task": True}))
    while True:
        if not args.marin:
            os.system("cls" if os.name == "nt" else "clear")
        if not worker:
            worker = int(os.cpu_count() / 2)
            if worker < 1:
                worker = 1
        sem = asyncio.Semaphore(worker)
        async with aiofiles.open(config_file, "r") as r:
            read = await r.read()
            config = json.loads(read)
            cfg = Config(auto_task=config.get("auto_task", True))
        datas, proxies = await get_data()
        menu = f"""
{green}data file :{white} {data_file}
{green}proxy file :{white} {proxy_file}
{green}total data : {white}{len(datas)}
{green}total proxy : {white}{len(proxies)}

    {green}1{white}. set on/off auto task ({(green + "active" if cfg.auto_task else red + "non-active")}{reset})
    {green}2{white}. start bot {green}(multi proses)
    {green}3{white}. start bot {green}(single proses)
        """
        print(banner)
        print(menu)
        if not opt:
            opt = input(f"{green}input number : {white}") or None
            print(line)
            if not opt:
                print(f"{yellow}please input correct number !")
                input(f"{blue}press enter to continue !")
                continue
        if opt == "1":
            async with aiofiles.open(config_file, "w") as w:
                config["auto_task"] = False if cfg.auto_task else True
                await w.write(json.dumps(config, indent=4))
            print(f"{green}success update auto_task config !")
            input(f"{blue}press enter to continue !")
            opt = None
            continue
        elif opt == "2":
            await init()
            if len(datas) <= 0:
                print(f"{red}fill your data in {data_file} first !")
                exit()
            while True:
                datas, proxies = await get_data()
                tasks = [
                    asyncio.create_task(bound(sem, (no, data, proxies, cfg)))
                    for no, data in enumerate(datas)
                ]
                results = await asyncio.gather(*tasks)
                _now = int(datetime.now().timestamp())
                await countdown(min(results) - _now)
        elif opt == "3":
            await init()
            if len(datas) <= 0:
                print(f"{red}fill your data in {data_file} first !")
                exit()
            while True:
                datas, proxies = await get_data()
                countdowns = []
                for no, data in enumerate(datas):
                    result = await MajTod(no, data, proxies, cfg).start()
                    countdowns.append(result)
                now = int(datetime.now().timestamp())
                await countdown(min(countdowns) - now)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        exit()
