FROM ubuntu:24.04

# Install system dependencies and upgrade packages to fix vulnerabilities
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3.12 \
    python3.12-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python /usr/bin/python3.12 \
    && update-alternatives --set python3 /usr/bin/python3.12


# Add non-root user
RUN useradd -m user \
    && mkdir -p /app && chown -R user:user /app

USER user

ENV PATH="/home/user/.local/bin:${PATH}"
ENV PIP_USER=1
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# Copy requirements and install Python dependencies
COPY --chown=user:user requirements /app/requirements
RUN python -m pip install --timeout 180 -r /app/requirements/main.txt \
    && rm -rf /app/requirements

# Copy application code
COPY --chown=user:user eva /app/eva

# Create necessary directories
RUN mkdir -p /app/documents /app/chroma_db /app/logs /app/huggingface

# Expose port
EXPOSE 8000
ENV PORT=8000
# Run the application
CMD ["python", "-m", "eva.main"]
