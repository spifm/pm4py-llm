import lib.config_loader as config_loader
import requests
from huggingface_hub import InferenceClient


config = config_loader.load_config()
debug = config['debug']
llm_config = config["llm"]
llm_context = "\n".join(llm_config["context"])

# Analyze abstract Petri Net model
def analyze_petri_net(abstract_model, file_name):
    print("\n\n-------------------\nPetri net analysis\n-------------------\n\n")
    prompt = f"{llm_context}\n\n{llm_config["petri_net"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(config['llm']['petri_net'], prompt, file_name)

# Analyze abstract Directly-Follows Graph model
def analyze_dfg(abstract_model, file_name):
    print("\n\n-------------\nDFG analysis\n------------\n\n")
    prompt = f"{llm_config['context']}\n\n{llm_config["dfg"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(config['llm']['dfg'], prompt, file_name)

# Analyze abstract Temporal Profile
def analyze_temporal_profile(abstract_model, file_name):
    print("\n\n---------------------\nTemporal profile analysis\n---------------------\n\n")
    prompt = f"{llm_config['context']}\n\n{llm_config["temporal_profile"]["prompt"]}\n\n{abstract_model}"
    exec_prompt(llm_config['temporal_profile'], prompt, file_name)

# Execute prompt for different LLM providers
def exec_prompt(llm_model_config, prompt, output_file):
    if llm_config['llm_provider'] == 'ollama':
        exec_prompt_for_ollama(prompt, output_file)
    elif llm_config['llm_provider'] == 'huggingface':
        exec_prompt_for_huggingface(llm_model_config, prompt, output_file)
    else:
        print("Model type not supported")

def exec_prompt_for_ollama(prompt, output_file):
    ollama_config = llm_config['ollama']
    url = f"{ollama_config['api_url']}{ollama_config['api_endpoint']}"

    payload = {
        "model": ollama_config['model_name'],
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": False
    }

    if debug > 0:
        print(f"URL: {url}")
        print(f"prompt: {prompt}")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error in Ollama request: {e}")
        return None

    if debug > 0:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    result = response.json()["message"]["content"]
    if debug > 0:
        print(f"Response content result: {result}")

    with open(output_file, 'a') as f:
        f.write(result + "\n\n")

    return result

def exec_prompt_for_huggingface(llm_model_config, prompt, output_file):
    if llm_config['huggingface']['model_type'] == 'text-generation-inference':
        exec_prompt_for_huggingface_text_generation_inference(llm_model_config, prompt, output_file)
    elif llm_config['huggingface']['model_type'] == 'vllm':
        exec_prompt_for_huggingface_vllm(llm_model_config, prompt, output_file)
    else:
        print("Huggingface model type not supported")

def exec_prompt_for_huggingface_text_generation_inference(llm_model_config, prompt, output_file):

    client = InferenceClient(
        llm_config['huggingface']['model_name'],
        token=llm_config['huggingface']['hugging_face_api_key'],
    )

    with open(output_file, 'a') as f:
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=llm_model_config['max_tokens'],
                stream=True,
            ):
                if debug > 0:
                    print(message.choices[0].delta.content, end="")

                f.write(message.choices[0].delta.content)
        f.write("\n\n")


def exec_prompt_for_huggingface_vllm(llm_model_config, prompt, output_file):
    # TODO: Implement VLLM
    pass