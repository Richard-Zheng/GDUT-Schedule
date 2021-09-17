import argparse
import requests
import config
from html.parser import HTMLParser

import crypto


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
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.authHTML = AuthHTMLParser(username, password)
        response = requests.get(
            'https://authserver.gdut.edu.cn/authserver/login?service=http%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin',
            headers=config.headers)
        self.cookies = response.cookies
        self.authHTML.feed(response.text)

    def login(self):
        response = requests.post(
            'https://authserver.gdut.edu.cn/authserver/login?service=http%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin',
            data=self.authHTML.authAttrs,
            cookies=self.cookies,
            headers=config.headers,
        )
        self.cookies = response.cookies


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="full username")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()

    us = UserSession(args.username, args.password)
    us.login()
