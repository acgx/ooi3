"""OOI3: Online Objects Integration version 3.0"""

import argparse
import asyncio
from aiohttp import web

from handlers.service import ServiceHandler

parser = argparse.ArgumentParser(description='Online Objects Integration version 3.0')
parser.add_argument('-H', '--host', default='127.0.0.1',
                    help='The host of OOI server')
parser.add_argument('-p', '--port', type=int, default=9999,
                    help='The port of OOI server')


def main():
    """OOI运行主函数。

    :return: none
    """

    # 解析命令行参数
    args = parser.parse_args()
    host = args.host
    port = args.port

    # 初始化事件循环
    loop = asyncio.get_event_loop()

    # 初始化请求处理器
    service = ServiceHandler()

    # 初始化应用
    app = web.Application(loop=loop)

    # 给应用添加路由
    app.router.add_route('POST', '/service/osapi', service.get_osapi)
    app.router.add_route('POST', '/service/flash', service.get_flash)
    app_handlers = app.make_handler()

    # 启动OOI服务器
    server = loop.run_until_complete(loop.create_server(app_handlers, host, port))
    print('OOI serving on http://%s:%d' % server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app_handlers.finish_connections(1.0))
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()

if __name__ == '__main__':
    main()
