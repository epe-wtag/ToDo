FROM python:latest
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN apt-get update && \
    apt-get install -y netcat-openbsd
COPY . .
COPY wait-for.sh .
EXPOSE 8000
RUN chmod +x wait-for.sh
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]