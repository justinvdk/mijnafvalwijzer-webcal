FROM python:3-alpine

ADD src /app
ADD requirements.txt /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

ENV HTTP_HOST 0.0.0.0
ENV HTTP_PORT 9090

EXPOSE $HTTP_PORT

ENTRYPOINT ["python", "app.py"]
