
#!/bin/sh

# Start FileFlow in production mode

exec uvicorn api.server:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --limit-concurrency 8 \
    --timeout-keep-alive 5
