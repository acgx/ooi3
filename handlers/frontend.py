import aiohttp_jinja2
from aiohttp_session import get_session


class FrontEndHandler:

    @aiohttp_jinja2.template('form.html')
    async def form(self, request):
        session = await get_session(request)
        if 'mode' in session:
            mode = session['mode']
        else:
            session['mode'] = 1
            mode = 1

        return {'mode': mode}

    def normal(self):
        pass

    def kcv(self):
        pass

    def poi(self):
        pass

    def logout(self):
        pass
