FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev dos2unix && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN printf '#!/bin/bash\nset -e\n\necho "Creating database tables..."\npython -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all(); print('"'"'Tables created.'"'"')"\n\necho "Seeding database..."\nflask seed\n\necho "Starting gunicorn..."\nexec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app\n' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
