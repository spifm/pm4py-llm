import requests
from lib.Config import Config
from openai import OpenAI
from openai.types.responses import ResponseOutputMessage, ResponseOutputText
from huggingface_hub import InferenceClient


def get_config():
    return Config().get()

# Analyze abstract Petri Net model
def analyze_petri_net(abstract_model, file_name):
    config = get_config()
    llm_context = "\n".join(config["llm"]["context"])

    print("\n\n-------------------\nPetri net analysis\n-------------------\n\n")
    prompt = f"{llm_context}\n\n{config["llm"]["petri_net"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(config['llm']['petri_net'], prompt, file_name)

# Analyze abstract Directly-Follows Graph model
def analyze_dfg(abstract_model, file_name):
    config = get_config()
    print("\n\n-------------\nDFG analysis\n------------\n\n")
    prompt = f"{config["llm"]['context']}\n\n{config["llm"]["dfg"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(config['llm']['dfg'], prompt, file_name)

# Analyze abstract Temporal Profile
def analyze_temporal_profile(abstract_model, file_name):
    config = get_config()
    print("\n\n---------------------\nTemporal profile analysis\n---------------------\n\n")
    prompt = f"{config["llm"]['context']}\n\n{config["llm"]["temporal_profile"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(config["llm"]['temporal_profile'], prompt, file_name)

# Execute prompt for different LLM providers
def exec_prompt(llm_model_config, prompt, output_file):

    config = get_config()

    if config["llm"]['llm_provider'] == 'ollama':
        exec_prompt_for_ollama(prompt, output_file)
    elif config["llm"]['llm_provider'] == 'huggingface':
        exec_prompt_for_huggingface(llm_model_config, prompt, output_file)
    elif config["llm"]['llm_provider'] == 'openai':
        exec_prompt_for_openai(prompt, output_file)
    else:
        print("Model type not supported")

def exec_prompt_for_ollama(prompt, output_file):

    config = get_config()

    ollama_config = config["llm"]['ollama']
    url = f"{ollama_config['api_url']}{ollama_config['api_endpoint']}"

    payload = {
        "model": ollama_config['model_name'],
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": False
    }

    if config["debug"] > 0:
        print(f"URL: {url}")
        print(f"prompt: {prompt}")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error in Ollama request: {e}")
        return None

    if config["debug"] > 0:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    result = response.json()["message"]["content"]
    if config["debug"] > 0:
        print(f"Response content result: {result}")

    with open(output_file, 'a') as f:
        f.write(result + "\n\n")

    return result

def exec_prompt_for_openai(prompt, output_file):

    config = get_config()
    openai_config = config["llm"]['openai']
    client = OpenAI(api_key=openai_config["openai_api_key"])

    try:
        if openai_config['reasoning']:
            response = client.responses.create(
                model=openai_config['model_name'],
                input=prompt,
                reasoning={
                    "effort": "medium"
                }
            )
        else:
            response = client.responses.create(
                model=openai_config['model_name'],
                input=prompt
            )

    except Exception as e:
        print(f"Error during OpenAI request: {e}")
        return None

    if config["debug"] > 0:
        print(f"OpenAI response: {response}")

    # Search for the output that is a message
    message_output = next(
        o for o in response.output 
        if isinstance(o, ResponseOutputMessage) or getattr(o, "type", "") == "message"
    )

    # Extract text chunks
    text_chunks = []
    for c in message_output.content:
        if isinstance(c, ResponseOutputText) or hasattr(c, "text"):
            text_chunks.append(c.text)

    result = "\n".join(text_chunks)

    with open(output_file, 'a') as f:
        f.write(result + "\n\n")
    
    return result

def exec_prompt_for_huggingface(llm_model_config, prompt, output_file):

    config = get_config()

    if config["llm"]['huggingface']['model_type'] == 'text-generation-inference':
        exec_prompt_for_huggingface_text_generation_inference(llm_model_config, prompt, output_file)
    elif config["llm"]['huggingface']['model_type'] == 'vllm':
        exec_prompt_for_huggingface_vllm(llm_model_config, prompt, output_file)
    else:
        print("Huggingface model type not supported")

def exec_prompt_for_huggingface_text_generation_inference(llm_model_config, prompt, output_file):

    config = get_config()

    client = InferenceClient(
        config["llm"]['huggingface']['model_name'],
        token=config["llm"]['huggingface']['hugging_face_api_key'],
    )

    with open(output_file, 'a') as f:
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=llm_model_config['max_tokens'],
                stream=True,
            ):
                if config['debug'] > 0:
                    print(message.choices[0].delta.content, end="")

                f.write(message.choices[0].delta.content)
        f.write("\n\n")


def exec_prompt_for_huggingface_vllm(llm_model_config, prompt, output_file):
    # TODO: Implement VLLM
    pass