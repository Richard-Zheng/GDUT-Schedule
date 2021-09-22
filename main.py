import argparse
import asyncio
import re
from datetime import datetime, date, time, timedelta
from pathlib import Path

import aiohttp
import requests
import config
import json
from html.parser import HTMLParser
from icalendar import Calendar, Event

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

    async def get_all_schedule(self, school_year: int, term: int):
        first_monday = date.fromisoformat(await self.get_first_monday_date(school_year, term))
        async with self.session.post(
                'https://jxfw.gdut.edu.cn/xsgrkbcx!xsAllKbList.action',
                params={
                    'xnxqdm': f'{str(school_year)}0{str(term)}',  # 学年学期
                },
                cookies=self.cookies
        ) as response:
            resp = await response.text()
            schedules = json.loads(re.findall(r'var kbxx = (\[.*?\]);', resp)[0])
            c = Calendar()
            for course in schedules:
                jcArr = course['jcdm2'].split(",")
                begin_time = time.fromisoformat(config.jc_to_time[int(jcArr[0])][0] + '+08:00')
                end_time = time.fromisoformat(config.jc_to_time[int(jcArr[-1])][1] + '+08:00')
                continuous_schedules = zcs_to_start_and_num_of_times(course['zcs'])
                for week_num_and_duaration in continuous_schedules:
                    e = Event()
                    e.add('SUMMARY', course['kcmc'])
                    begin_date = first_monday + timedelta(weeks=week_num_and_duaration[0]-1, days=int(course['xq'])-1)
                    e.add('dtstart', datetime.combine(begin_date, begin_time))
                    e.add('dtend', datetime.combine(begin_date, end_time))
                    e.add('rrule', {'freq': 'WEEKLY', 'count': week_num_and_duaration[1]})
                    e['LOCATION'] = course['jxcdmcs']
                    c.add_component(e)

            term_ics_path = Path(data_dir, f'user_{self.username}_{school_year}0{term}_schedule.ics')
            with term_ics_path.open(mode='wb') as f:
                f.write(c.to_ical())

    async def get_week_schedule(self, school_year: int, term: int, week: int):
        async with self.session.post(
                config.GetStudentCoursesDateURL,
                params={
                    'xnxqdm': f'{str(school_year)}0{str(term)}',  # 学年学期
                    'zc': str(week)  # 周次
                },
                cookies=self.cookies
        ) as response:
            return json.loads(await response.text())

    async def get_first_monday_date(self, school_year: int, term: int):
        s = await self.get_week_schedule(school_year, term, 1)
        for day in s[1]:
            if day['xqmc'] == '1':
                return day['rq']

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


def zcs_to_start_and_num_of_times(zcs):
    zc = list(map(int, zcs.split(',')))
    zc.sort()
    out = []
    s_i = 0
    for i, val in enumerate(zc):
        if zc[s_i] + i - s_i != val:
            out.append([zc[s_i], i - s_i])
            s_i = i
    out.append([zc[s_i], len(zc) - s_i])
    return out

async def main(args):
    async with aiohttp.ClientSession() as session:
        us = UserSession(session, args.username, args.password)
        await us.get_all_schedule(2021, 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="full username")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
