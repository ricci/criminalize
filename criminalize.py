#!/usr/bin/env python3

import asyncio
import hashlib
import json
import logging
import os

from aiohttp import web
import aiohttp_cors
from ollama import AsyncClient
import redis

OLLAMAHOST = os.environ['OLLAMA_HOST']
VALKEYHOST = os.environ['VALKEY_HOST']
VALKEYPORT = os.environ['VALKEY_PORT']

logger = logging.getLogger(__name__)

valkey = redis.asyncio.client.Redis(host=VALKEYHOST, port=VALKEYPORT, db=0, decode_responses=True)
ollamaClient = AsyncClient(host=OLLAMAHOST)

async def handleHttp(request):
    text = "Status: Healthy"
    return web.Response(text=text)

async def handleHttpCriminalize(request):

    if request.content_type != "application/json" or not request.can_read_body:
        logging.info("Bad content type: {}".format(request.content_type))
        raise web.HTTPBadRequest

    try:
        request_json = await request.json()
    except:
        logging.info("Can't read JSON")
        raise web.HTTPBadRequest

    hashval = hashlib.sha256(repr(request_json).encode()).hexdigest()

    try:
        resp = await valkey.get(hashval)
        if resp:
            return web.Response(body=json.dumps({'response': resp}))
    except redis.ConnectionError:
        # Oh well, no caching right now
        pass

    model = ""
    if request_json["type"] == "title":
        model = "toottitle"
    elif request_json["type"] == "venue":
        model = "tootvenue"
    elif request_json["type"] == "bio":
        model = "stodgify"
    else:
        logging.info("Bad request type: {}".format(request_json["type"]))
        raise web.HTTPBadRequest

    message = {'role': 'user', 'content': request_json["message"][:5000]}

    try:
        ollamaResponse = await ollamaClient.chat(model=model, messages=[message])
        title = ollamaResponse["message"]["content"]
        title.strip('\"')

        try:
            asyncio.create_task(valkey.set(hashval, title))
        except:
            pass

        return web.Response(body=json.dumps({'response': title }))
    except:
        raise web.HTTPInternalServerError

app = web.Application()

cors = aiohttp_cors.setup(app)
app.add_routes([web.get('/', handleHttp),
                web.put('/criminalize', handleHttpCriminalize)])

# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})

# Configure CORS on all routes.
for route in list(app.router.routes()):
    cors.add(route)


if __name__ == '__main__':
    if 'DEBUG' in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    web.run_app(app)
