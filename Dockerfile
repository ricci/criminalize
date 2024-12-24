FROM python:3.12

ADD criminalize.py .
RUN pip install aiohttp redis ollama
CMD python ./criminalize.py 
