
FROM python:3.13-slim

ENV PYTHONPATH=/src

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
