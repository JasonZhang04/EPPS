import asyncio
import tinker
from tinker import types
import sys
import os

# Set encoding to UTF-8 for Windows terminals to avoid UnicodeEncodeError with emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Fix for Windows Git Bash/Anaconda pathing causing FileNotFoundError in Tinker's httpx client
import os
ssl_cert_file = os.environ.get("SSL_CERT_FILE")
if ssl_cert_file and not os.path.exists(ssl_cert_file):
    del os.environ["SSL_CERT_FILE"]

async def run_chat():
    api_key = os.environ.get("TINKER_API_KEY")
    if not api_key:
        print("Error: TINKER_API_KEY environment variable is not set.")
        return

    try:
        # 1. Initialize the client
        client = tinker.ServiceClient(api_key=api_key)

        # 2. Setup a SamplingClient
        model_name = "Qwen/Qwen3-8B"
        print(f"Initializing SamplingClient for {model_name}...")
        sampling_client = client.create_sampling_client(base_model=model_name)
        
        # 3. Get the tokenizer
        # In Tinker, TrainingClient is used to get the tokenizer for the base model
        print("Fetching tokenizer...")
        training_client = client.create_lora_training_client(base_model=model_name, rank=1)
        tokenizer = training_client.get_tokenizer()

        print(f"\n--- Multi-turn Chat with {model_name} ---")
        print("Type 'exit' to quit.")

        chat_history_tokens = []

        while True:
            try:
                user_input = input("\nUser: ")
            except EOFError:
                break
            
            if user_input.lower() in ['exit', 'quit']:
                break

            # 1. Format user message
            user_formatted = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
            user_tokens = tokenizer.encode(user_formatted)
            chat_history_tokens.extend(user_tokens)

            # 2. Prepare ModelInput
            prompt = types.ModelInput.from_ints(tokens=chat_history_tokens)
            
            # 3. Call sample_async
            params = types.SamplingParams(
                max_tokens=256,
                temperature=0.7,
                stop=["<|im_end|>", "User:"]
            )

            result = await sampling_client.sample_async(
                prompt=prompt,
                num_samples=1,
                sampling_params=params
            )

            # 4. Extract response
            response_seq = result.sequences[0]
            response_text = tokenizer.decode(response_seq.tokens).strip()
            print(f"Assistant: {response_text}")

            # 5. Update history
            chat_history_tokens.extend(response_seq.tokens)
            chat_history_tokens.extend(tokenizer.encode("<|im_end|>\n"))

    except Exception:
        import traceback
        traceback.print_exc()
        print("\nNote: If you see '[Errno 2]', ensure 'orjson' is installed and your environment is correctly activated.")

if __name__ == "__main__":
    # Ensure this works with Windows multiprocessing "spawn"
    try:
        asyncio.run(run_chat())
    except KeyboardInterrupt:
        pass
