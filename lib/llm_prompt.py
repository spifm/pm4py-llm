
# Export filtered log
def exec_prompt(client, llm_config_model, prompt, output_file, debug):
    with open(output_file, 'w') as f:
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=llm_config_model['max_tokens'],
                stream=True,
            ):
                if debug > 0:
                    print(message.choices[0].delta.content, end="")

                f.write(message.choices[0].delta.content)