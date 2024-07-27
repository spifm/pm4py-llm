
# Export filtered log
def exec_prompt(client, llm_config_model, prompt):
    for message in client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=llm_config_model['max_tokens'],
            stream=True,
        ):
            print(message.choices[0].delta.content, end="")
