FROM python:3
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
WORKDIR /srv/app
COPY . .
EXPOSE 5000
CMD python run.py
