#!/usr/bin/env python3 

from aiohttp import web
import json
from ollama import AsyncClient
import redis
import hashlib

OLLAMAHOST = "10.0.0.71:11434"
VALKEYHOST= "10.1.0.46"
VALKEYPORT = 6380

valkey = redis.Redis(host=VALKEYHOST, port=VALKEYPORT, db=0, decode_responses=True)

async def handleHttp(request):
    text = "Status: Healthy"
    return web.Response(text=text)

async def handleHttpCriminalize(request):
    print("got a request")
    ollamaClient = AsyncClient(host=OLLAMAHOST)

    if request.content_type != "application/json" or not request.can_read_body:
        pass # XXX ERROR

    request_json = await request.json()
    # XXX ERROR

    hashval = hashlib.sha256(repr(request_json).encode()).hexdigest()
    resp = valkey.get(hashval)
    if resp:
        return web.Response(body=json.dumps({'response': resp}))
    else:
        model = "";
        if request_json["type"] == "title":
            model = "toottitle"
        elif request_json["type"] == "venue":
            model = "tootvenue"
        else:
            pass # XXX ERROR

        message = {'role': 'user', 'content': request_json["message"]}

        print("asking ollama (model {})".format(model))
        ollamaResponse = await ollamaClient.chat(model=model, messages=[message])
        # XXX ERROR
        print("returning response")

        title = ollamaResponse["message"]["content"]
        title.strip('\"')
        valkey.set(hashval,title)

        return web.Response(body=json.dumps({'response': title }))

app = web.Application()
#logging.basicConfig(level=logging.DEBUG)
app.add_routes([web.get('/', handleHttp),
                web.put('/criminalize', handleHttpCriminalize)])

if __name__ == '__main__':
    web.run_app(app)
