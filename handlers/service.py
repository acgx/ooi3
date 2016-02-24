"""OOI3的API服务。
只接受POST请求，包括login_id和password两个参数，返回用户的内嵌游戏网页地址或游戏FLASH地址。请求缺少参数时返回400错误。
"""

import asyncio
import aiohttp
import aiohttp.web
import json

from auth.exceptions import OOIAuthException
from auth.kancolle import KancolleAuth


class ServiceHandler:
    """OOI3的API服务请求处理类。"""

    @asyncio.coroutine
    def get_osapi(self, request):
        """获取用户的内嵌游戏网页地址，返回一个JSON格式的字典。
        结果中`status`键值为1时获取成功，`osapi_url`键值为内嵌网页地址；`status`为0时获取失败，`message`键值提供了错误信息。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPBadRequest
        """
        data = yield from request.post()
        login_id = data.get('login_id', None)
        password = data.get('password', None)
        if login_id and password:
            headers = aiohttp.MultiDict({'Content-Type': 'application/json'})
            kancolle = KancolleAuth(login_id, password)
            try:
                osapi_url = yield from kancolle.get_osapi()
                result = {'status': 1,
                          'osapi_url': osapi_url}
            except OOIAuthException as e:
                result = {'status': 0,
                          'message': e.message}
            return aiohttp.web.Response(body=json.dumps(result).encode(), headers=headers)
        else:
            return aiohttp.web.HTTPBadRequest()

    @asyncio.coroutine
    def get_flash(self, request):
        """获取用户的游戏FLASH地址，返回一个JSON格式的字典。
        结果中`status`键值为1时获取成功，`flash_url`键值为游戏FLASH地址；`status`为0时获取失败，`message`键值提供了错误信息。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPBadRequest
        """
        data = yield from request.post()
        login_id = data.get('login_id', None)
        password = data.get('password', None)
        if login_id and password:
            headers = aiohttp.MultiDict({'Content-Type': 'application/json'})
            kancolle = KancolleAuth(login_id, password)
            try:
                flash_url = yield from kancolle.get_flash()
                result = {'status': 1,
                          'flash_url': flash_url}
            except OOIAuthException as e:
                result = {'status': 0,
                          'message': e.message}
            return aiohttp.web.Response(body=json.dumps(result).encode(), headers=headers)
        else:
            return aiohttp.web.HTTPBadRequest()
