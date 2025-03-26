import pm4py
import lib.config_loader as config_loader
import torch
from huggingface_hub import InferenceClient
from vllm import LLM, SamplingParams

config = config_loader.load_config()
debug = config['debug']
llm_config = config["llm"]
llm_context = "\n".join(llm_config["context"])

client = InferenceClient(
    llm_config['model_name'],
    token=llm_config['hugging_face_api_key'],
)

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

def exec_prompt(llm_model_config, prompt, output_file):
    if llm_config['model_type'] == 'text-generation-inference':
        exec_prompt_for_text_generation_inference(llm_model_config, prompt, output_file)
    elif llm_config['model_type'] == 'vllm':
        exec_prompt_for_vllm(llm_model_config, prompt, output_file)
    else:
        print("Model type not supported")


def exec_prompt_for_text_generation_inference(llm_model_config, prompt, output_file):
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


def exec_prompt_for_vllm(llm_model_config, prompt, output_file):
    device = "cuda" if torch.cuda.is_available() else "cpu"  # Detects GPU or uses CPU

    if debug > 0:
        print(torch.cuda.is_available())
        print(torch.cuda.device_count())
        print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")
        print(f"Using device: {device}")
    
    model = LLM(model=llm_config['model_name'], device=device, dtype="float16" if device == "cuda" else "float32", max_model_len=4096) # Use float16 to optimize memory usage if using a GPU
    
    params = SamplingParams(
        max_tokens=llm_model_config['max_tokens'],
        temperature=0.3,
        top_p=0.3,
    )
    
    with open(output_file, 'a') as f:
        try:
            output = model.generate(prompt, sampling_params=params)
            
            if output:
                f.write(output[0].outputs[0].text)
                if debug > 0:
                    f.write(output[0].outputs[0].text)
                
            f.write("\n\n")
        except Exception as e:
            print(f"Error in model execution: {e}")
