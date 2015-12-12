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

    async def world_image(self, request):
        """ 显示正确的镇守府图片。
        舰娘游戏中客户端FLASH请求的镇守府图片是根据FLASH本身的URL生成的，需要根据用户所在的镇守府IP为其显示正确的图片。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.HTTPFound
        """
        size = request.match_info['size']
        session = await get_session(request)
        world_ip = session['world_ip']
        if world_ip:
            ip_sections = map(int, world_ip.split('.'))
            world_ip = '_'.join([format(x, '03') for x in ip_sections])
            return aiohttp.web.HTTPFound('/_kcs/resources/image/world/' + world_ip + '_' + size + '.png')
        else:
            return aiohttp.web.HTTPBadRequest()

    async def api(self, request):
        """ 转发客户端和游戏服务器之间的API通信。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response
        """
        action = request.match_info['action']
        session = await get_session(request)
        world_ip = session['world_ip']
        if world_ip:
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
            data = await request.post()
            coro = aiohttp.post(url, data=data, headers=headers, connector=self.connector)
            try:
                response = await asyncio.wait_for(coro, timeout=5)
            except asyncio.TimeoutError:
                return aiohttp.web.HTTPBadRequest()
            body = await response.read()
            return aiohttp.web.Response(body=body, headers={'Content-Type': response.headers['CONTENT-TYPE']})
        else:
            return aiohttp.web.HTTPBadRequest()
