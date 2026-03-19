FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# PORT is injected by the host (Render, HuggingFace, Railway, etc.).
# Default to 8501 for local Docker use.
# The entrypoint reads $PORT at runtime so no rebuild is needed
# when the platform assigns a different port.
ENV PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE ${PORT}

# Use shell form so $PORT is expanded at container start time
CMD streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port=${PORT} \
    --server.headless=true
