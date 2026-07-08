FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

# RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /app

ENV NOMI_BACKEND_PORT=8000

CMD ["python", "-u", "-m", "control_panel.backend.main"]