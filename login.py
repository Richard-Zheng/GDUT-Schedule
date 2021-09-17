import argparse
import asyncio
from pathlib import Path

import aiohttp
import requests
import config
import json
from html.parser import HTMLParser
from ics import Calendar, Event

import crypto

data_dir = Path('data')
data_dir.mkdir(parents=True, exist_ok=True)

class AuthHTMLParser(HTMLParser):
    def __init__(self, username, password):
        super().__init__()
        self.pwdDefaultEncryptSalt = ''
        self.authAttrs = {'username': username, 'password': password}

    def handle_starttag(self, tag, attrs):
        if tag == 'input' and attrs[1][0] == 'name' and attrs[2][0] == 'value':
            self.authAttrs[attrs[1][1]] = attrs[2][1]
        elif tag == 'input' and attrs[1][1] == 'pwdDefaultEncryptSalt':
            self.pwdDefaultEncryptSalt = attrs[2][1]

    def feed(self, data):
        super().feed(data)
        self.authAttrs['password'] = crypto.encrypt_password(self.authAttrs['password'], self.pwdDefaultEncryptSalt)


class UserSession:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self.session = session
        self.username = username
        self.password = password
        self.authHTML = AuthHTMLParser(username, password)
        response = requests.get(
            'https://authserver.gdut.edu.cn/authserver/login?service=http%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin',
            headers=config.headers)
        self.cookies = response.cookies
        self.authHTML.feed(response.text)
        self.login()

    def login(self):
        response = requests.post(
            'https://authserver.gdut.edu.cn/authserver/login?service=http%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin',
            data=self.authHTML.authAttrs,
            cookies=self.cookies,
            headers=config.headers,
        )
        self.cookies = response.history[2].cookies

    async def get_week_schedule(self, school_year: int, term: int, week: int):
        async with self.session.post(
            config.GetStudentCoursesDateURL,
            params={
                'xnxqdm': f'{str(school_year)}0{str(term)}', # 学年学期
                'zc': str(week) # 周次
            },
            cookies=self.cookies
        ) as response:
            return json.loads(await response.text())

    async def get_term_schedule(self, school_year: int, term: int):
        term_data_path = Path(data_dir, f'user_{self.username}_{school_year}0{term}_schedule.txt')
        if term_data_path.exists():
            with term_data_path.open(mode='r') as f:
                return json.load(f)
        task = []
        for week in range(1, 20):
            task.append(self.get_week_schedule(school_year, term, week))
        all_schedule_in_a_term = await asyncio.gather(*task)
        with term_data_path.open(mode='w') as f:
            json.dump(all_schedule_in_a_term, f)
        return all_schedule_in_a_term

    async def get_term_ics(self, school_year: int, term: int):
        term_ics_path = Path(data_dir, f'user_{self.username}_{school_year}0{term}_schedule.ics')
        term_schedule = await self.get_term_schedule(school_year, term)
        c = Calendar()
        for week_schedule in term_schedule:
            day_to_date = {}
            for day in week_schedule[1]:
                day_to_date[day['xqmc']] = day['rq']

            for course in week_schedule[0]:
                e = Event()
                e.name = course['kcmc']
                jcArr = course['jcdm2'].split(",")
                e.begin = day_to_date[course['xq']] + ' ' + config.jc_to_time[int(jcArr[0])][0] + '+08:00'
                e.end = day_to_date[course['xq']] + ' ' + config.jc_to_time[int(jcArr[-1])][1] + '+08:00'
                e.location = course['jxcdmc']
                c.events.add(e)
        with term_ics_path.open(mode='w') as f:
            f.write(str(c))


async def main(args):
    async with aiohttp.ClientSession() as session:
        us = UserSession(session, args.username, args.password)
        await us.get_term_ics(2021, 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="full username")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
