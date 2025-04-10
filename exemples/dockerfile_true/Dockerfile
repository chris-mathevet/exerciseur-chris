FROM python:alpine3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# Sans OpenFaas
# EXPOSE 8082 
# Avec openFaas
EXPOSE 8080 
CMD exec python ./daemon.py
