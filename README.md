# Reca API

## Introduction

Reca API is a reverse-engineered implementation of Reka AI in OpenAI-compatible API.

## Features

* Reverse-engineered Reka AI Playground API
* OpenAI API compatible
* Can be deployed via Docker Compose or run directly
* Supports proxy connections
* Supports three authorization method

## Available Models
- reka-core
- reka-flash
- reka-edge


## Deploy

### Docker Compose
Clone repo
```bash
git clone git@github.com:HuggingBear/Reca-API.git
cd Reca-API
```
Configure token or user information in `.env` file
```env
REKA_TOKEN=YOUR_REKA_JWT_TOKEN (Without 'Bearer ')
REKA_USER=YOUR_USER_NAME
REKA_PASS=YOUR_SUPER_LONG_PASSWORD
```
Run
```
docker-compose up
```

### Manual Deploy

1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python src/main.py`

## Configuration

### Environment Variables

| Variable | Description |
|---|---|
| PROXY | Proxy address (e.g., "socks5://192.168.0.1:1080") |
| REKA_TOKEN | Access token (JWT token) |
| REKA_USER | Username |
| REKA_PASS | Password |

### Authentication

## Usage
```bash
curl http://127.0.0.1:3031/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "model": "chat",
        "messages": [
          {"role": "user", "content": "Hello, how are you?"}
        ]
      }'
```
Response
```json
{
    "id": "chatcmpl-reka-ai",
    "object": "chat.completion.chunk",
    "created": 1719100000,
    "model": "reka-core",
    "choices": [
        {
            "index": 0,
            "delta": {
                "role": "assistant",
                "content": "  Hello! 😄 I'm Yasa, a helpful AI assistant. I'm doing great today! How are you doing today?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
}
```

You can choose one of the following methods to authenticate:

* Set `REKA_TOKEN` environment variable
* Set `REKA_USER` and `REKA_PASS` environment variables
* Specify `X-Reka-Token` in request header

## Caution

This project is a fork of [jessfin/reka](https://github.com/jessfin/reka). 

It is not affiliated with Reka AI and may violate their Terms of Service. Use with caution.

## License

This project is licensed under the MIT License.