#!/usr/bin/env python3 

import asyncio
from aiohttp import web
import json
from ollama import AsyncClient
import redis
import hashlib

OLLAMAHOST = "10.0.0.71:11434"
VALKEYHOST= "10.1.0.46"
VALKEYPORT = 6380

valkey = redis.asyncio.client.Redis(host=VALKEYHOST, port=VALKEYPORT, db=0, decode_responses=True)
ollamaClient = AsyncClient(host=OLLAMAHOST)

async def handleHttp(request):
    text = "Status: Healthy"
    return web.Response(text=text)

async def handleHttpCriminalize(request):

    if request.content_type != "application/json" or not request.can_read_body:
        raise web.HTTPBadRequest

    try:
        request_json = await request.json()
    except:
        raise web.HTTPBadRequest

    hashval = hashlib.sha256(repr(request_json).encode()).hexdigest()

    try:
        resp = await valkey.get(hashval)
        if resp:
            return web.Response(body=json.dumps({'response': resp}))
    except redis.ConnectionError:
        # Oh well, no caching right now
        pass

    model = "";
    if request_json["type"] == "title":
        model = "toottitle"
    elif request_json["type"] == "venue":
        model = "tootvenue"
    else:
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
app.add_routes([web.get('/', handleHttp),
                web.put('/criminalize', handleHttpCriminalize)])

if __name__ == '__main__':
    web.run_app(app)
