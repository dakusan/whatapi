from ConfigParser import RawConfigParser
import requests
import time

headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'whatapi [isaaczafuta]'
    }

class LoginException(Exception):
    pass


class RequestException(Exception):
    pass


class WhatAPI:
    def __init__(self, config_file=None, username=None, password=None, cookies=None):
        self.session = requests.Session()
        self.session.headers = headers
        self.authkey = None
        self.passkey = None
        if config_file:
            config = RawConfigParser()
            config.read(config_file)
            self.username = config.get('login', 'username')
            self.password = config.get('login', 'password')
        else:
            self.username = username
            self.password = password
        if cookies:
            self.session.cookies = cookies
            try:
                self._auth()
            except RequestException:
                self._login()
        else:
            self._login()

    def _auth(self):
        '''Gets auth key from server'''
        accountinfo = self.request("index")
        self.authkey = accountinfo["response"]["authkey"]
        self.passkey = accountinfo["response"]["passkey"]

    def _login(self):
        '''Logs in user'''
        loginpage = 'https://ssl.what.cd/login.php'
        data = {'username': self.username,
                'password': self.password,
                'keeplogged': 1,
                'login': 'Login'
        }
        r = self.session.post(loginpage, data=data, allow_redirects=False)
        if r.status_code != 302:
            raise LoginException
        self._auth()

    def get_torrent(self, torrent_id):
        '''Downloads the torrent at torrent_id using the authkey and passkey'''
        torrentpage = 'https://ssl.what.cd/torrents.php'
        params = {'action': 'download', 'id': torrent_id}
        if self.authkey:
            params['authkey'] = self.authkey
            params['torrent_pass'] = self.passkey
        r = self.session.get(torrentpage, params=params, allow_redirects=False)
        time.sleep(2)
        if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
            return r.content
        return None

    def logout(self):
        '''Logs out user'''
        logoutpage = 'https://ssl.what.cd/logout.php'
        params = {'auth': self.authkey}
        self.session.get(logoutpage, params=params, allow_redirects=False)

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        ajaxpage = 'https://ssl.what.cd/ajax.php'
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)

        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        time.sleep(2)
        try:
            json_response = r.json()
            if "status" in json_response and json_response["status"] == "success":
                return json_response
            if "error" in json_response:
                raise RequestException(json_response["error"])
            if "status" in json_response:
                raise RequestException(json_response["status"])
            import pprint
            raise RequestException(pprint.pformat(json_response))
        except ValueError:
            raise RequestException
