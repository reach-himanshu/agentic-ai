FROM python:3.11

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .
RUN python -m spacy download en_core_web_lg

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
