FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# 👇 Добавь это, чтобы wait-for-it.sh был исполняемым
RUN chmod +x /app/wait-for-it.sh