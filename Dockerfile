FROM python:3.12

ADD criminalize.py .
RUN pip install aiohttp aiohttp_cors redis ollama
CMD python ./criminalize.py 
