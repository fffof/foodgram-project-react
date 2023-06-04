FROM python:3.7-slim 
 
WORKDIR /app 
 
COPY requirements.txt . 
 
RUN pip3 install -r /app/requirements.txt --no-cache-dir 
RUN pip3 install python-dotenv
 
COPY . . 
CMD ["python", "manage.py","makemigrations"]
CMD ["python", "manage.py","migrate"]
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ] 
