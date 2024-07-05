import time

def create_reply_json_chunk(model_name, content, input_tokens, generated_tokens, finish_reason):
    return {
        "id": "chatcmpl-reka-ai",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": generated_tokens,
            "total_tokens": input_tokens + generated_tokens
        }
    }
    
    
def create_reply_json(model_name, content, input_tokens, generated_tokens, finish_reason):
    return {
        "id": "chatcmpl-reka-ai",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "usage": {
            "prompt_tokens": 13,
            "completion_tokens": 7,
            "total_tokens": 20
        },
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": finish_reason
            }
        ],
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": generated_tokens,
            "total_tokens": input_tokens + generated_tokens
        }
    }
    