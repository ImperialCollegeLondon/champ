FROM python:3.10-slim

EXPOSE 8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=nobody:nogroup . /usr/src/app
WORKDIR /usr/src/app

USER nobody:nogroup

RUN mkdir -p /usr/src/app/db
VOLUME /usr/src/app/db
# RUN python manage.py collectstatic --no-input && rm /tmp/portal.log
