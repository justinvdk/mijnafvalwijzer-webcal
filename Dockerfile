FROM python:3-alpine

ADD src /app
ADD requirements.txt /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

COPY mijnafvalwijzer-to-ical.py .

ENTRYPOINT [ "python", "./mijnafvalwijzer-to-ical.py" ]
