FROM python:3.8.3-buster

WORKDIR /usr/src/app

COPY . .

EXPOSE 8000

RUN pip install pipenv

RUN pipenv lock -r >> requirements.txt

RUN pip install -r requirements.txt

RUN apt-get update

RUN apt-get install docker.io -y

RUN docker --version

# RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -

# RUN apt-get install -y nodejs

CMD python app.py