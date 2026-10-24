import asyncio
import re
from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand
from websockets.asyncio.server import ServerConnection, serve

from mediaworkers.ws_urls import urlpatterns

class UrlCollector:
    urlpatterns = []
    def __init__(self):
        if self.urlpatterns:
            return

        conf_package_str, conf_module_str = settings.ROOT_WSURLCONF.split('.')
        conf_module = import_module(settings.ROOT_WSURLCONF)
        for row in conf_module.urlpatterns:
            if isinstance(row, str):
                parts = row.split('.')
                module = import_module(row)
                self.urlpatterns.extend(getattr(module, 'urlpatterns'))
            else:
                self.urlpatterns.append(row)


# TODO: использовать джанговый распознаватель путей
# TODO: вынести в отдельную библиотеку
async def handler(websocket: ServerConnection):
    for url in UrlCollector().urlpatterns:
        if len(url) == 2:
            url.append(re.compile(url[0]))

        matched_object = url[2].match(websocket.request.path)
        if matched_object:
            await url[1](websocket, **(matched_object.groupdict()))
            return

    await websocket.close()


async def main(port):
    async with serve(handler, "", port, server_header='service server'):
        await asyncio.get_running_loop().create_future()  # run forever


class Command(BaseCommand):
    help = 'Run the websocket server'

    def handle(self, *args, **options):
        port = options['addrport'] or 8001
        asyncio.run(main(port))

    def add_arguments(self, parser):
        parser.add_argument(
            'addrport', nargs='?', help='Optional port number'
        )
