import pm4py

# Analyze abstract Petri Net model
def analyze_petri_net(client, llm_config, net, im, fm, file_name, debug):
    print("\n\n-------------------\nPetri net analysis\n-------------------\n\n")
    petri_net_description = pm4py.llm.abstract_petri_net(net, im, fm)
    prompt = f"{llm_config['context']}\n\nHere is the Petri Net model:\n\n{petri_net_description}"
    exec_prompt(client, llm_config['petri_net'], prompt, file_name, debug)

# Analyze abstract Directly-Follows Graph model
def analyze_dfg(client, llm_config, filtered_log, file_name, debug):
    print("\n\n-------------\nDFG analysis\n------------\n\n")
    dfg_description = pm4py.llm.abstract_dfg(filtered_log)
    prompt = f"{llm_config['context']}\n\nHere is the DFG model:\n\n{dfg_description}"
    exec_prompt(client, llm_config['dfg'], prompt, file_name, debug)

# Analyze abstract Temporal Profile
def analyze_temporal_profile(client, llm_config, temporal_profile, file_name, debug):
    print("\n\n---------------------\nTemporal profile analysis\n---------------------\n\n")
    temporal_profile_description = pm4py.llm.abstract_temporal_profile(temporal_profile, include_header=True)
    prompt = f"{llm_config['context']}\n\nHere is the Temporal Profile:\n\n{temporal_profile_description}"
    exec_prompt(client, llm_config['temporal_profile'], prompt, file_name, debug)

# Export filtered log
def exec_prompt(client, llm_config_model, prompt, output_file, debug):
    with open(output_file, 'a') as f:
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=llm_config_model['max_tokens'],
                stream=True,
            ):
                if debug > 0:
                    print(message.choices[0].delta.content, end="")

                f.write(message.choices[0].delta.content)
        f.write("\n\n")