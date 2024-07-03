
import os
import json
import time
import requests
import asyncio
import re
import logging
from aiohttp import web

from utils import get_logging_level, is_jwt_token_expired
from reka import get_access_token, parse_conversation_data

logging.basicConfig(level=get_logging_level())
logger = logging.getLogger(__name__)


# Read settings from environment variable
env_proxy = os.environ.get('PROXY', None)

# Username and password were used to create a new token, but are not required
# if the token was set in an environment variable or passed via the request header
env_reka_user = os.environ.get('REKA_USER', None)
env_reka_pass = os.environ.get('REKA_PASS', None)
env_reka_access_token = os.environ.get('REKA_TOKEN', None)

# Lock that prevent server from accepting requests when trying to get a new token
create_token_event = asyncio.Event()
create_token_event.set()

# Cache JWT token for the application's lifetime
# TODO: Save it to a persistent storage that survives restarts
memory_reka_access_token = None


async def handle_chat_request(request, access_token=None):
    body = await request.json()
    logger.debug(f"Received chat request with body: {body}")

    messages = body.get("messages", [])
    stream = body.get("stream", True)
    model_name = body.get("model", "reka-core")

    # Convert request data to Reka Playground API format
    conversation_history = parse_conversation_data(messages)

    logger.debug(f"Conversation history: {conversation_history}")

    chat_data = {
        "conversation_history": conversation_history,
        "stream": stream,
        "use_search_engine": False,
        "use_code_interpreter": False,
        "model_name": model_name,
        "random_seed": int(time.time())
    }

    url = "https://chat.reka.ai/api/chat"
    # Try reading auth token from header, then environment variable, then fallback to empty string
    token = f"Bearer {access_token or memory_reka_access_token or env_reka_access_token or ''}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': token
    }
    logger.debug(f"Sending request to Reka AI with headers: {headers}")

    try:
        proxies = {}
        if env_proxy:
            proxies['https'] = env_proxy

        response = requests.post(url, headers=headers, data=json.dumps(chat_data), stream=True)
        logger.debug(f"Response from Reka AI: {response.status_code}, {response.headers}")
    except Exception as e:
        logger.error(f"Unexpected error while requesting to Reka AI: {e}")
        return web.Response(status=500, body="Unexpected upstream error")

    if response.status_code == 429:
        logger.error("Rate limited by Reka AI")
        return web.Response(status=429, body="Rate limited by Reka AI")
    elif not response.ok:
        logger.error(f"Unexpected response from Reka AI: {response.status_code} - {response.text}")
        return web.Response(status=500, body="Unexpected response from upstream server")

    response_stream = web.StreamResponse()
    response_stream.headers['Content-Type'] = 'text/event-stream'
    response_stream.headers['Access-Control-Allow-Origin'] = '*'
    response_stream.headers['Access-Control-Allow-Methods'] = '*'
    response_stream.headers['Access-Control-Allow-Headers'] = '*'
    
    await response_stream.prepare(request)
    writer = response_stream
    # Reka Playground API will send chat completions from the first letter in every new stream message,
    # so we need to keep track of the cursor location of the last message to avoid giving duplicate
    # characters to the client.
    previous_message_index = 0
    finished = False
    
    
    for line in response.iter_lines():
        if finished:
            return
        
        logger.debug(f"Received response line: {line}")

        # It might not be a stream response if the answer is too short?
        if line and (line.startswith(b'data:') or line.startswith(b'{')):
            decoded_line = line.decode('utf-8')
            data_content = decoded_line[5:].strip() if decoded_line.startswith('data:') else decoded_line
            data_json = None

            try:
                data_json = json.loads(data_content)
            except Exception as e:
                logger.error(f"Unable to decode response message: {data_content}")
                return web.Response(status=500, body="Unable to decode upstream response")
            
            # Filter model response and convert to OpenAI style data structure
            if data_json['type'] == 'model':
                full_text = data_json['text']
                full_text_length = len(full_text)
                # I don't know why there are <sep in the end of chat response, truncate it
                sep_matches = re.search(r'\n <s?e?p?$', full_text)
                text_ends_location = full_text_length if not sep_matches else sep_matches.start()
                
                
                new_json = {
                    "id": "chatcmpl-reka-ai",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": full_text[previous_message_index:text_ends_location]
                            },
                            "finish_reason": "stop" if "finish_reason" in data_json else None,
                        }
                    ],
                    "usage": {
                        "prompt_tokens": data_json['metadata']['input_tokens'],
                        "completion_tokens": data_json['metadata']['generated_tokens'],
                        "total_tokens": data_json['metadata']['input_tokens'] + data_json['metadata']['generated_tokens']
                    },
                }
                
                previous_message_index = len(full_text)

                event_data = f"data: {json.dumps(new_json, ensure_ascii=False)}\n\n"
                await writer.write(event_data.encode('utf-8'))
                logger.debug(f"Wrote event data: {event_data}")
                
                if "finish_reason" in data_json:
                    await writer.write("data: [DONE]\n\n".encode('utf-8'))
                    await writer.write_eof()
                    finished = True
                    logger.debug("Wrote [DONE]")
            # It doesn't seem useful
        elif line.startswith(b'event: message'):
            pass
        elif not line:
            pass
        else:
            logger.info(f"Unknown data line in Reka AI response: {line}")
            pass

    return writer


async def update_access_token():
    """
    Updates the access token used for Reka AI chat requests.

    Attempts to obtain a new one using the username and password read from
    environment variables.

    Raises:
        ValueError: If no username and password was provided.
    """
    global memory_reka_access_token

    if not env_reka_user or not env_reka_pass:
        raise ValueError("No access token was provided, nor a username and password.")

    create_token_event.clear()
    proxies = {}
    if env_proxy:
        proxies = {"https": env_proxy}
    memory_reka_access_token = get_access_token(env_reka_user, env_reka_pass, proxies)
    create_token_event.set()


async def on_cors_request(request):
    return web.Response(status=200, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*'
    })


async def on_chat_completions_request(request):
    logger.info(f"Serving request from {request.remote}")
    # Wait if there is a ongoing request to get a new token
    await create_token_event.wait()
    header_token = request.headers.get('X-Reka-Token', '')
    access_token = header_token or memory_reka_access_token or env_reka_access_token

    # Get new token if no token was provided or cached or it was expired
    if not access_token:
        logger.warning("No access token provided, attempting to get a new one")
        await update_access_token()
    elif is_jwt_token_expired(access_token):
        logger.warning("Access token has expired, attempting to get a new one")
        await update_access_token()

    return await handle_chat_request(request)

async def on_get_models_request(request):
    available_models = [
        "reka-core",
        "reka-flash",
        "reka-edge"
    ]
    
    model_profiles = []
    
    for model in available_models:
        model_data = {
            "id": model,
            "object": "model",
            "created": 1719999999,
            "owned_by": "reka-ai"
        }
        model_profiles.append(model_data)
    
    return web.json_response({
        "object": "list",
        "data": model_profiles
    })


app = web.Application()
app.router.add_route("OPTIONS", "/{tail:.*}", on_cors_request)  # catch all OPTIONS requests
app.router.add_route("POST", "/v1/chat/completions", on_chat_completions_request)
app.router.add_route("GET", "/v1/models", on_get_models_request)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3031)
