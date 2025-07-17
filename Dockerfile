FROM python:3.11

WORKDIR /app

RUN apt-get update && \
    apt-get install -y g++ default-jdk && \
    apt-get clean

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN python3 manage.py makemigrations
RUN python3 manage.py migrate

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
