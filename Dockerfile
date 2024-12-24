FROM python:3.12

RUN pip install aiohttp aiohttp_cors redis ollama
ADD criminalize.py .
CMD python ./criminalize.py 
