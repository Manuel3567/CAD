FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt app.py gcp.py ./
COPY templates/ ./templates
COPY static/ ./static
RUN pip3 install -r requirements.txt
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "80"]
EXPOSE 80