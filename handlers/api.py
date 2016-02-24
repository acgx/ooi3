"""转发客户端FLASH和游戏服务器之间的通信。
接受客户端FLASH发送到OOI3服务器的请求，将其转发给用户所在的游戏服务器，获得响应后再返回给客户端FLASH。
"""

import aiohttp
import aiohttp.web
import asyncio
from aiohttp_session import get_session

from base import config


class APIHandler:
    """ OOI3中用于转发客户端FLASH和游戏服务器间通信的类。"""

    def __init__(self):
        """ 构造函数，根据环境变量初始化代理服务器。

        :return: none
        """
        if config.proxy:
            self.connector = aiohttp.ProxyConnector(proxy=config.proxy, force_close=False)
        else:
            self.connector = None

        # 初始化存放镇守府图片和api_start2内容的变量
        self.api_start2 = None
        self.worlds = {}

    @asyncio.coroutine
    def world_image(self, request):
        """ 显示正确的镇守府图片。
        舰娘游戏中客户端FLASH请求的镇守府图片是根据FLASH本身的URL生成的，需要根据用户所在的镇守府IP为其显示正确的图片。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.HTTPFound or aiohttp.web.HTTPBadRequest
        """
        size = request.match_info['size']
        session = yield from get_session(request)
        world_ip = session['world_ip']
        if world_ip:
            ip_sections = map(int, world_ip.split('.'))
            image_name = '_'.join([format(x, '03') for x in ip_sections]) + '_' + size
            if image_name in self.worlds:
                body = self.worlds[image_name]
            else:
                url = 'http://203.104.209.102/kcs/resources/image/world/' + image_name + '.png'
                coro = aiohttp.get(url, connector=self.connector)
                try:
                    response = yield from asyncio.wait_for(coro, timeout=5)
                except asyncio.TimeoutError:
                    return aiohttp.web.HTTPBadRequest()
                body = yield from response.read()
                self.worlds[image_name] = body
            return aiohttp.web.Response(body=body, headers={'Content-Type': 'image/png', 'Cache-Control': 'no-cache'})
        else:
            return aiohttp.web.HTTPBadRequest()

    @asyncio.coroutine
    def api(self, request):
        """ 转发客户端和游戏服务器之间的API通信。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPBadRequest
        """
        action = request.match_info['action']
        session = yield from get_session(request)
        world_ip = session['world_ip']
        if world_ip:
            if action == 'api_start2' and self.api_start2 is not None:
                return aiohttp.web.Response(body=self.api_start2,
                                            headers=aiohttp.MultiDict({'Content-Type': 'text/plain'}))
            else:
                referrer = request.headers.get('REFERER')
                referrer = referrer.replace(request.host, world_ip)
                referrer = referrer.replace('https://', 'http://')
                url = 'http://' + world_ip + '/kcsapi/' + action
                headers = aiohttp.MultiDict({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
                    'Origin': 'http://' + world_ip + '/',
                    'Referer': referrer,
                    'X-Requested-With': 'ShockwaveFlash/18.0.0.232'
                })
                data = yield from request.post()
                coro = aiohttp.post(url, data=data, headers=headers, connector=self.connector)
                try:
                    response = yield from asyncio.wait_for(coro, timeout=5)
                except asyncio.TimeoutError:
                    return aiohttp.web.HTTPBadRequest()
                body = yield from response.read()
                if action == 'api_start2' and len(body) > 100000:
                    self.api_start2 = body
                return aiohttp.web.Response(body=body, headers=aiohttp.MultiDict({'Content-Type': 'text/plain'}))
        else:
            return aiohttp.web.HTTPBadRequest()
