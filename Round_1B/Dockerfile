FROM python:3.9-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./models /app/models
COPY . .

ENV PATH="/opt/venv/bin:$PATH"

# Run the main script for the 1B task
CMD ["python", "main.py"]
