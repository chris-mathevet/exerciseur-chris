FROM python:alpine3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5678
CMD exec python ./daemon.py
