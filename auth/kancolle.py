"""针对网页游戏《舰队collection》的认证类。"""

import aiohttp
import asyncio
import json
import re
import time
from urllib.parse import urlparse, parse_qs

from base import config
from auth.exceptions import OOIAuthException


class KancolleAuth:
    """针对网页游戏《舰队collection》的认证类。"""

    # 认证过程中需要的URLs
    urls = {'login': 'https://www.dmm.com/my/-/login/',
            'ajax': 'https://www.dmm.com/my/-/login/ajax-get-token/',
            'auth': 'https://www.dmm.com/my/-/login/auth/',
            'game': 'http://www.dmm.com/netgame/social/-/gadgets/=/app_id=854854/',
            'make_request': 'http://osapi.dmm.com/gadgets/makeRequest',
            'get_world': 'http://203.104.209.7/kcsapi/api_world/get_id/%s/1/%d',
            'get_flash': 'http://%s/kcsapi/api_auth_member/dmmlogin/%s/1/%d',
            'flash': 'http://%s/kcs/mainD2.swf?api_token=%s&amp;api_starttime=%d'}

    # 各镇守府的IP列表
    world_ip_list = (
        "203.104.209.71",
        "203.104.209.87",
        "125.6.184.16",
        "125.6.187.205",
        "125.6.187.229",
        "125.6.187.253",
        "125.6.188.25",
        "203.104.248.135",
        "125.6.189.7",
        "125.6.189.39",
        "125.6.189.71",
        "125.6.189.103",
        "125.6.189.135",
        "125.6.189.167",
        "125.6.189.215",
        "125.6.189.247",
        "203.104.209.23",
        "203.104.209.39",
        "203.104.209.55",
        "203.104.209.102",
    )

    # 伪装成Win7 x64上的IE11
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'

    # 匹配网页中所需信息的正则表达式
    patterns = {'dmm_token': re.compile(r'"DMM_TOKEN", "([\d|\w]+)"'),
                'token': re.compile(r'"token": "([\d|\w]+)"'),
                'reset': re.compile(r'認証エラー'),
                'osapi': re.compile(r'URL\W+:\W+"(.*)",')}

    def __init__(self, login_id, password):
        """ 使用`login_id`和`password`来初始化认证对象。
        `login_id`为登录DMM网站所需的用户名，一般为电子邮件地址，`password`为登录所需的密码。
        仅支持用DMM账号登录，不支持Facebook和Google+账号登录。

        :param login_id: str
        :param password: str
        :return: none
        """

        # 初始化登录变量
        self.login_id = login_id
        self.password = password

        # 初始化aiohttp会话，如果设定了代理服务器，则通过代理服务器发起会话
        if config.proxy:
            self.connector = aiohttp.ProxyConnector(proxy=config.proxy, force_close=False)
        else:
            self.connector = None
        self.session = aiohttp.ClientSession(connector=self.connector)
        self.headers = {'User-Agent': self.user_agent}

        # 初始化登录过程中所需的变量
        self.dmm_token = None
        self.token = None
        self.idKey = None
        self.pwdKey = None
        self.owner = None
        self.osapi_url = None
        self.world_id = None
        self.world_ip = None
        self.api_token = None
        self.api_starttime = None
        self.flash = None

    def __del__(self):
        """析构函数，用于关闭aiohttp的会话。

        :return: none
        """
        self.session.close()

    @asyncio.coroutine
    def _request(self, url, method='GET', data=None, timeout_message='连接失败', timeout=10):
        """使用asyncio.wait_for包装过的会话向远端服务器发起请求。
        `url`为请求的URL地址，`method`为请求的方法， `data`为发起POST请求时的数据，`timeout_message`为请求超时后抛出异常所带的信息，
        `timeout`为超时时间，单位为秒。

        :param url: str
        :param method: str
        :param data: dict
        :param timeout_message: str
        :param timeout: int
        :return: generator
        """
        try:
            response = yield from asyncio.wait_for(self.session.request(method, url, data=data, headers=self.headers),
                                                   timeout)
            return response
        except asyncio.TimeoutError:
            raise OOIAuthException(timeout_message)

    @asyncio.coroutine
    def _get_dmm_tokens(self):
        """解析DMM的登录页面，获取dmm_token和token，返回dmm_token和token的值。

        :return: tuple
        """
        response = yield from self._request(self.urls['login'], method='GET', data=None,
                                            timeout_message='连接DMM登录页失败')
        html = yield from response.text()

        m = self.patterns['dmm_token'].search(html)
        if m:
            self.dmm_token = m.group(1)
        else:
            raise OOIAuthException('获取DMM token失败')

        m = self.patterns['token'].search(html)
        if m:
            self.token = m.group(1)
        else:
            raise OOIAuthException('获取token失败')

        return self.dmm_token, self.token

    @asyncio.coroutine
    def _get_ajax_token(self):
        """根据在DMM登录页获得的dmm_token和token，发起一个AJAX请求，获取第二个token以及idKey和pwdKey。

        :return: tuple
        """
        self.headers.update({'Origin': 'https://www.dmm.com',
                             'Referer': self.urls['login'],
                             'DMM_TOKEN': self.dmm_token,
                             'X-Requested-With': 'XMLHttpRequest'})
        data = {'token': self.token}
        response = yield from self._request(self.urls['ajax'], method='POST', data=data,
                                       timeout_message='DMM登录页AJAX请求失败')
        j = yield from response.json()
        self.token = j['token']
        self.idKey = j['login_id']
        self.pwdKey = j['password']

        return self.token, self.idKey, self.pwdKey

    @asyncio.coroutine
    def _get_osapi_url(self):
        """登录DMM账号，并转到《舰队collection》游戏页面，获取内嵌游戏网页的地址。

        :return: str
        """
        del self.headers['DMM_TOKEN']
        del self.headers['X-Requested-With']
        data = {'login_id': self.login_id,
                'password': self.password,
                'token': self.token,
                self.idKey: self.login_id,
                self.pwdKey: self.password}
        response = yield from self._request(self.urls['auth'], method='POST', data=data,
                                       timeout_message='连接DMM认证网页失败')
        html = yield from response.text()
        m = self.patterns['reset'].search(html)
        if m:
            raise OOIAuthException('DMM强制要求用户修改密码')

        response = yield from self._request(self.urls['game'],
                                       timeout_message='连接舰队collection游戏页面失败')
        html = yield from response.text()
        m = self.patterns['osapi'].search(html)
        if m:
            self.osapi_url = m.group(1)
        else:
            raise OOIAuthException('用户名或密码错误，请重新输入')

        return self.osapi_url

    @asyncio.coroutine
    def _get_world(self):
        """解析游戏内嵌网页地址，从DMM处获得用户所在服务器的ID和IP地址。

        :return: tuple
        """
        qs = parse_qs(urlparse(self.osapi_url).query)
        self.owner = qs['owner'][0]
        self.st = qs['st'][0]
        url = self.urls['get_world'] % (self.owner, int(time.time()*1000))
        self.headers['Referer'] = self.osapi_url
        response = yield from self._request(url, timeout_message='调查提督所在镇守府失败')
        html = yield from response.text()
        svdata = json.loads(html[7:])
        if svdata['api_result'] == 1:
            self.world_id = svdata['api_data']['api_world_id']
            self.world_ip = self.world_ip_list[self.world_id-1]
        else:
            raise OOIAuthException('调查提督所在镇守府时发生错误')

        return self.world_id, self.world_ip, self.st

    @asyncio.coroutine
    def _get_api_token(self):
        """根据用户所在服务器IP和用户自身的ID，从DMM处获得用户的api_token、api_starttim，并生成游戏FLASH的地址

        :return: tuple
        """
        url = self.urls['get_flash'] % (self.world_ip, self.owner, int(time.time()*1000))
        data = {'url': url,
                'httpMethod': 'GET',
                'authz': 'signed',
                'st': self.st,
                'contentType': 'JSON',
                'numEntries': '3',
                'getSummaries': 'false',
                'signOwner': 'true',
                'signViewer': 'true',
                'gadget': 'http://203.104.209.7/gadget.xml',
                'container': 'dmm'}
        response = yield from self._request(self.urls['make_request'], method='POST', data=data,
                                       timeout_message='调查提督进入镇守府的口令失败')
        html = yield from response.text()
        svdata = json.loads(html[27:])
        if svdata[url]['rc'] != 200:
            raise OOIAuthException('调查提督进入镇守府的口令失败')
        svdata = json.loads(svdata[url]['body'][7:])
        if svdata['api_result'] != 1:
            raise OOIAuthException('调查提督进入镇守府的口令时发生错误')
        self.api_token = svdata['api_token']
        self.api_starttime = svdata['api_starttime']
        self.flash = self.urls['flash'] % (self.world_ip, self.api_token, self.api_starttime)

        return self.api_token, self.api_starttime, self.flash

    @asyncio.coroutine
    def get_osapi(self):
        """登录游戏，获取内嵌游戏网页地址并返回

        :return: str
        """
        yield from self._get_dmm_tokens()
        yield from self._get_ajax_token()
        yield from self._get_osapi_url()
        return self.osapi_url

    @asyncio.coroutine
    def get_flash(self):
        """登录游戏，获取游戏FLASH地址并返回

        :return: str
        """
        yield from self.get_osapi()
        yield from self._get_world()
        yield from self._get_api_token()
        return self.flash
