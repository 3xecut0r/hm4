FROM python:3.10

COPY . /app

WORKDIR /app/

CMD ["python", "main.py"]