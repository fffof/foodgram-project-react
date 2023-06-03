FROM python:3.7-slim 
 
WORKDIR /app 
 
COPY requirements.txt . 
 
RUN pip3 install -r /app/requirements.txt --no-cache-dir 
RUN pip3 install python-dotenv
 
COPY . . 
 
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ] 
