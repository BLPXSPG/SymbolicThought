from openai import AzureOpenAI
from time import sleep
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed


def _get_azure_client(config):
    missing = []
    if not config.azure_openai_api_key:
        missing.append("AZURE_OPENAI_API_KEY")
    if not config.azure_openai_api_version:
        missing.append("AZURE_OPENAI_API_VERSION")
    if not config.azure_openai_endpoint:
        missing.append("AZURE_OPENAI_ENDPOINT")
    if missing:
        raise ValueError(f"Missing Azure OpenAI configuration: {', '.join(missing)}")

    return AzureOpenAI(
        api_key=config.azure_openai_api_key,
        api_version=config.azure_openai_api_version,
        azure_endpoint=config.azure_openai_endpoint,
    )


def _get_client_and_model(config):
    if not config.azure_openai_chat_deployment:
        raise ValueError("Missing Azure OpenAI configuration: AZURE_OPENAI_CHAT_DEPLOYMENT")
    return _get_azure_client(config), config.azure_openai_chat_deployment


def _get_embedding_client_and_model(config):
    if not config.azure_openai_embedding_deployment:
        raise ValueError("Missing Azure OpenAI configuration: AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    return _get_azure_client(config), config.azure_openai_embedding_deployment


def multiple_generate(cfg, sys, prompt, generate_type="string", multiple=5):
    gen_fn = gen_response_string if generate_type == "string" else gen_response_json

    with ThreadPoolExecutor(max_workers=multiple) as executor:
        futures = [executor.submit(gen_fn, sys, prompt, cfg) for _ in range(multiple)]
        return [f.result() for f in futures]


def gen_embedding(prompt: str, config, retry_flag=True):
    try:
        client, model = _get_embedding_client_and_model(config)
        embedding = client.embeddings.create(input=[prompt], model=model).data[0].embedding
        embedding = np.array(embedding).reshape(1, -1)
        return embedding
    except Exception as e:
        print("Error:", e)
        sleep(2)
        if retry_flag:
            return gen_embedding(prompt, config, retry_flag=False)
        else:
            print("Failed after retry.")
            return None


def gen_embeddings_batch(prompts: list, config, retry_flag=True):
    if not prompts:
        return []
    try:
        client, model = _get_embedding_client_and_model(config)
        response = client.embeddings.create(input=prompts, model=model)
        results = [None] * len(prompts)
        for item in response.data:
            emb = np.array(item.embedding).reshape(1, -1)
            results[item.index] = emb
        return results
    except Exception as e:
        print("Error in batch embedding:", e)
        sleep(2)
        if retry_flag:
            return gen_embeddings_batch(prompts, config, retry_flag=False)
        else:
            print("Failed after retry, falling back to sequential.")
            return [gen_embedding(p, config) for p in prompts]


def gen_response_json(sys: str, prompt: str, config, retry_flag=True):
    try:
        client, model = _get_client_and_model(config)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": prompt},
            ],
            n=1
        )
        response = completion.choices[0].message.content
        response_cleaned = response.replace('`', '').replace('json', '').replace('\n', '').replace('    ', ' ').replace('  ', ' ')
        start_index = response_cleaned.find("{")
        end_index = response_cleaned.rfind("}")
        data = json.loads(response_cleaned[start_index:end_index+1])
        return data
    except Exception as e:
        print("Error:", e)
        sleep(2)
        if retry_flag:
            return gen_response_json(sys, prompt, config, retry_flag=False)
        else:
            print("Failed after retry.")
            return {}


def gen_response_string(sys: str, prompt: str, config, retry_flag=True):
    try:
        client, model = _get_client_and_model(config)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": prompt},
            ],
            n=1
        )
        return completion.choices[0].message.content
    except Exception as e:
        print("Error:", e)
        sleep(2)
        if retry_flag:
            return gen_response_string(sys, prompt, config, retry_flag=False)
        else:
            print("Failed after retry.")
            return {}
