import argparse
import asyncio
import config
from html.parser import HTMLParser

import aiohttp

import crypto


class UserSession:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self.session = session
        self.username = username
        self.password = password
        self.authHTMLParser = AuthHTMLParser(self.username, self.password)

    async def login(self):
        async with self.session.get(config.AuthURL, params=config.params, headers=config.headers) as response:
            self.authHTMLParser.feed(await response.text())
        self.authHTMLParser.authAttrs['password'] = crypto.encrypt_password(self.password, self.authHTMLParser.pwdDefaultEncryptSalt)
        async with self.session.post(config.AuthURL, params=config.params, headers=config.headers,
                                     data=aiohttp.FormData(self.authHTMLParser.authAttrs), allow_redirects=False) as response:
            return await response.text()


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


async def main(username, password):
    async with aiohttp.ClientSession() as session:
        us = UserSession(session, username, password)
        st = await us.login()
        for cookie in us.session.cookie_jar:
            print(cookie.key)
            print(cookie["domain"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="full username")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.username, args.password))
