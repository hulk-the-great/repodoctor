# Optional custom sandbox image for RepoDoctor.
# Build with:
#   docker build -t repodoctor-python-sandbox -f .repodoctor/Dockerfile .
# Then run RepoDoctor with:
#   --test-runner docker --docker-image repodoctor-python-sandbox

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m pip install --no-cache-dir pytest

WORKDIR /workspace
