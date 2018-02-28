FROM python:3

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

WORKDIR /src

CMD ["python", "main.py"]
