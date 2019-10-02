import requests
import os
import codecs
import sys


class Auth():

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0",
    }

    def __init__(self,
            auth_file="{}/.config/bboardd/uob_login.txt".format(os.environ.get("HOME")
                if os.environ.get("HOME") is not None else ""),
            headers=DEFAULT_HEADERS):
        self.session = requests.Session()
        self.headers = headers
        self.auth_file  = auth_file


    def login(self):
        lt, e = self._get_lt()
        self._login_sso(lt, e)
        self._login_bb()

    def get_session(self):
        return self.session

    def get_headers(self):
        return self.headers



    def _get_lt(self):
        url = "https://sso.bris.ac.uk/sso/login"
        r = self.session.get(url, headers=self.headers)

        cookie_found = False
        for cookie in self.session.cookies:
            if cookie.name == "JSESSIONID":
                cookie_found = True
                break
        if not cookie_found:
            print("Couldn't load login page (maybe the desgin has changed)",
                file=sys.stderr)
            sys.exit(-1)

        lt = ""
        e = ""
        for line in r.text.split("\n"):
            if "name=\"lt\"" in line:
                i1 = line.find("value=\"") + len("value=\"")
                i2 = line.find("\"", i1)
                lt = line[i1:i2]
            if "name=\"execution\"" in line:
                i1 = line.find("value=\"") + len("value=\"")
                i2 = line.find("\"", i1)
                e = line[i1:i2]
        if lt == "" or e == "":
            print("Couldn't find lt input (maybe the desgin has changed)",
                file=sys.stderr)
            sys.exit(-1)
        return lt, e


    def _login_sso(self, lt, e):
        with open(self.auth_file, "r") as f:
            auth = f.read().split("\n")
            if len(auth) < 2:
                print("Could not read Credentials from logfile", file=sys.stderr)
                sys.exit(-1)
            user = auth[0]
            pw = codecs.encode(auth[1], "rot_13")

        values = {
            "lt": lt,
            "execution": e,
            "_eventId": "submit",
            "username": user,
            "password": pw,
            "submit": "",
        }
        url = "https://sso.bris.ac.uk/sso/login;jsessionid=" + self.session.cookies.get(
            "JSESSIONID")

        h = self.headers.copy()
        h['Referer'] = "https://sso.bris.ac.uk/sso/login"

        r = self.session.post(url, data=values, headers=h)
        if "signed in" not in r.text:
            print("Couldn't login", file=sys.stderr)
            sys.exit(-1)


    def _login_bb(self):
        url = "https://www.ole.bris.ac.uk/webapps/bb-auth-provider-cas-bb_bb60/execute/casLogin?cmd=login&authProviderId=_122_1&redirectUrl=https%3A%2F%2Fwww.ole.bris.ac.uk"
        r = self.session.get(url)
