import requests

from .base import basetap
from datetime import datetime, timedelta, timezone

DEFAULT_HEADER = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://tg-tap-miniapp.laborx.io',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://tg-tap-miniapp.laborx.io/',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

class timefarm(basetap):
    def __init__(self, proxy = None, headers = DEFAULT_HEADER):
        super().__init__()
        self.proxy = proxy
        self.headers = headers
        self.stopped = False
        self.wait_time = 5
        self.name = self.__class__.__name__

    def login(self):
        url = "https://tg-bot-tap.laborx.io/api/v1/auth/validate-init"

        try:
            response = requests.post(url, headers=self.headers, data=self.init_data_raw)
            data = response.json()
            if "token" in data:
                self.auth = f"Bearer {data['token']}"
                self.update_header("Authorization", self.auth)
                self.bprint("Login success")
                self.tap(fromlogin=True)
                self.get_info()

                return True

            self.bprint("Login failed")
        except Exception as e:
            self.bprint(e)

    def get_info(self):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/info"
        try:    
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                self.print_balance(float(data['balance']))
                self.get_next_waiting_time(data['activeFarmingStartedAt'], data['farmingDurationInSec'])
                if self.wait_time > 0:
                    self.print_waiting_time()

                return True
        except Exception as e:
            self.bprint(e)

    def get_next_waiting_time(self, last_farm_at, farm_duration_sec):
        last_claimed_dt = datetime.strptime(last_farm_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        next_claimed_dt = last_claimed_dt + timedelta(seconds=float(farm_duration_sec))
        current_time = datetime.now(timezone.utc)
        # Calculate the waiting time in seconds
        waiting_time_seconds = (next_claimed_dt - current_time).total_seconds()
        # Ensure the waiting time is not negative
        self.wait_time = max(0, waiting_time_seconds)

    def print_waiting_time(self):
        hours, remainder = divmod(self.wait_time, 3600)
        minutes, _ = divmod(remainder, 60)
        self.bprint(f"Waiting time: {int(hours)} hours and {int(minutes)} minutes")

    def startFarm(self):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/start"
        try:
            response = requests.post(url, headers=self.headers, proxies=self.proxy)
            data = response.json()

        except Exception as e:
            self.wait_time = 10
            self.bprint(e)    

    def tap(self, fromlogin = False):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/finish"
        try:
            response = requests.post(url, headers=self.headers, proxies=self.proxy)
            data = response.json()
            if "balance" in data:
                self.startFarm()
                self.get_info()

            if fromlogin:
                self.bprint(f"Error {data['error']['message']}, stop looping since code is failed")
                self.stopped = True
            else:
                self.bprint(f"Error: {data['error']['message']}, try re-login")
                self.login()
        
        except Exception as e:
            self.bprint(e)

    def run(self):
        while self.stopped == False:
            self.tap()
            self.wait()
        return
