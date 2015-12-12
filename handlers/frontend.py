"""OOI3的前端部分，用于显示各种页面。
包含了登录表单、登录后的跳转、不同的游戏运行模式和注销页面。
"""

import aiohttp.web
import aiohttp_jinja2
from aiohttp_session import get_session

from auth.kancolle import KancolleAuth, OOIAuthException


class FrontEndHandler:
    """OOI3前端请求处理类。"""

    @aiohttp_jinja2.template('form.html')
    async def form(self, request):
        """展示登录表单。

        :param request: aiohttp.web.Request
        :return: dict
        """
        session = await get_session(request)
        if 'mode' in session:
            mode = session['mode']
        else:
            session['mode'] = 1
            mode = 1

        return {'mode': mode}

    async def login(self, request):
        """接受登录表单提交的数据，登录后跳转或登录失败后展示错误信息。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.HTTPFound or aiohttp.web.Response
        """
        post = await request.post()
        session = await get_session(request)

        login_id = post.get('login_id', None)
        password = post.get('password', None)
        mode = int(post.get('mode', 1))

        session['mode'] = mode

        if login_id and password:

            kancolle = KancolleAuth(login_id, password)
            try:
                await kancolle.get_flash()
                session['api_token'] = kancolle.api_token
                session['api_starttime'] = kancolle.api_starttime
                session['world_ip'] = kancolle.world_ip
                if mode == 2:
                    return aiohttp.web.HTTPFound('/kcv')
                elif mode == 3:
                    return aiohttp.web.HTTPFound('/poi')
                else:
                    return aiohttp.web.HTTPFound('/kancolle')

            except OOIAuthException as e:
                context = {'errmsg': e.message, 'mode': mode}
                return aiohttp_jinja2.render_template('form.html', request, context)
        else:

            context = {'errmsg': '请输入完整的登录ID和密码', 'mode': mode}
            return aiohttp_jinja2.render_template('form.html', request, context)

    async def normal(self, request):
        """适配浏览器中进行游戏的页面，该页面会检查会话中是否有api_token、api_starttime和world_ip三个参数，缺少其中任意一个都不能
        进行游戏，跳转回登录页面。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPFound
        """
        session = await get_session(request)
        token = session.get('api_token', None)
        starttime = session.get('api_starttime', None)
        world_ip = session.get('world_ip', None)
        if token and starttime and world_ip:
            context = {'scheme': request.scheme,
                       'host': request.host,
                       'token': token,
                       'starttime': starttime,
                       'world_ip': world_ip}
            return aiohttp_jinja2.render_template('normal.html', request, context)
        else:
            del session['api_token']
            del session['api_starttime']
            del session['world_ip']
            return aiohttp.web.HTTPFound('/')

    async def kcv(self, request):
        """适配KanColleViewer或者74EO中进行游戏的页面，提供一个iframe，在iframe中载入游戏FLASH。该页面会检查会话中是否有api_token、api_starttime和world_ip三个参数，缺少其中任意一个都不能
        进行游戏，跳转回登录页面。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPFound
        """
        session = await get_session(request)
        token = session.get('api_token', None)
        starttime = session.get('api_starttime', None)
        world_ip = session.get('world_ip', None)
        if token and starttime and world_ip:
            return aiohttp_jinja2.render_template('kcv.html', request, context={})
        else:
            del session['api_token']
            del session['api_starttime']
            del session['world_ip']
            return aiohttp.web.HTTPFound('/')

    async def flash(self, request):
        """适配KanColleViewer或者74EO中进行游戏的页面，展示，该页面会检查会话中是否有api_token、api_starttime和world_ip三个参数，缺少其中任意一个都不能
        进行游戏，跳转回登录页面。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPFound
        """
        session = await get_session(request)
        token = session.get('api_token', None)
        starttime = session.get('api_starttime', None)
        world_ip = session.get('world_ip', None)
        if token and starttime and world_ip:
            context = {'scheme': request.scheme,
                       'host': request.host,
                       'token': token,
                       'starttime': starttime,
                       'world_ip': world_ip}
            return aiohttp_jinja2.render_template('flash.html', request, context)
        else:
            del session['api_token']
            del session['api_starttime']
            del session['world_ip']
            return aiohttp.web.HTTPFound('/')

    async def poi(self, request):
        """适配poi中进行游戏的页面，显示FLASH。该页面会检查会话中是否有api_token、api_starttime和world_ip三个参数，缺少其中任意一个都不能
        进行游戏，跳转回登录页面。

        :param request: aiohttp.web.Request
        :return: aiohttp.web.Response or aiohttp.web.HTTPFound
        """
        session = await get_session(request)
        token = session.get('api_token', None)
        starttime = session.get('api_starttime', None)
        world_ip = session.get('world_ip', None)
        if token and starttime and world_ip:
            context = {'scheme': request.scheme,
                       'host': request.host,
                       'token': token,
                       'starttime': starttime,
                       'world_ip': world_ip}
            return aiohttp_jinja2.render_template('poi.html', request, context)
        else:
            del session['api_token']
            del session['api_starttime']
            del session['world_ip']
            return aiohttp.web.HTTPFound('/')

    async def logout(self, request):
        """ 注销已登录的用户。
        清除所有的session，返回首页。

        :return: aiohttp.web.HTTPFound
        """
        session = await get_session(request)
        if 'api_token' in session:
            del session['api_token']
        if 'api_starttime' in session:
            del session['api_starttime']
        if 'world_ip' in session:
            del session['world_ip']
        return aiohttp.web.HTTPFound('/')
