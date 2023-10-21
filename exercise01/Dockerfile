FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt schema.sql app.py db.py ./
COPY templates/ ./templates
COPY static/ ./static
RUN pip3 install -r requirements.txt
CMD ["flask", "run", "-h", "::", "-p", "80"]
EXPOSE 80