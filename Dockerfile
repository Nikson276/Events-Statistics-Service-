# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ код (важно для относительных импортов)
COPY . .

# Устанавливаем как пакет (чтобы работал -m ess.xxx)
RUN pip install -e .

# По умолчанию ничего не запускаем — команда задаётся в compose