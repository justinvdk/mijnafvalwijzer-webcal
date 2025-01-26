FROM python:3-alpine

WORKDIR /app

ADD requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

ADD src /app
ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=9090

EXPOSE $HTTP_PORT

ENTRYPOINT ["python", "app.py"]
