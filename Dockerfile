FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the database if it doesn't exist
RUN python -c "\
from database.models import init_db; \
from pathlib import Path; \
db = Path('database/amed.db'); \
init_db(f'sqlite:///{db}') if not db.exists() else None"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
