# VLLM GPU Keep-Alive Service

A lightweight service that sends periodic requests to a VLLM server to prevent GPU idle timeouts and keep the model warm. The service sends a minimal completion request (`"hi"` with `max_tokens=1`) at the configured interval. 

## Configuration

Edit `env.example` to configure the service:

```env
VLLM_HOST=localhost
VLLM_PORT=8081
VLLM_MODEL=Qwen/Qwen3-4B-Instruct-2507-FP8
KEEPALIVE_INTERVAL=60
```

## Run
```bash
# copy env.example
cp env.example .env

# build & deploy
docker compose up -d
```

### Standalone

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py
```

## LICENSE
MIT.



