FROM python:3.11-bookworm

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium

CMD ["mkdocs", "serve", "-a", "0.0.0.0:8000"]
