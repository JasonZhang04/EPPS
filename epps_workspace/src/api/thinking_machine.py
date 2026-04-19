import os
import json
import asyncio
from typing import List, Dict

# Fix for Windows Git Bash/Anaconda pathing causing FileNotFoundError in Tinker's httpx client
ssl_cert_file = os.environ.get("SSL_CERT_FILE")
if ssl_cert_file and not os.path.exists(ssl_cert_file):
    del os.environ["SSL_CERT_FILE"]

import tinker
from tinker import types

class ThinkingMachineClient:
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.environ.get("TINKER_API_KEY")
        
        if not api_key:
            raise ValueError("TINKER_API_KEY environment variable is not set. Please set it before running the pipeline.")
            
        self.client = tinker.ServiceClient(api_key=api_key)
        self.default_model = "Qwen/Qwen3-8B" # Replacing Llama-3.1-70b default based on Tinker API endpoints

    def query(self, messages: List[Dict[str, str]], temperature: float = 0.0, model: str = None) -> str:
        """
        Synchronous wrapper calling the sampling async client to mimic standard requests.
        """
        if model is None:
            model = self.default_model
        
        # Determine the user instructions out of the messages block
        # Since Tinker uses prompt tokens or formatted strings directly for sampling
        prompt_text = ""
        for msg in messages:
            prompt_text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        prompt_text += "<|im_start|>assistant\n"
        
        return asyncio.run(self._async_query(prompt_text, temperature, model))

    async def _async_query(self, prompt_text: str, temperature: float, model: str) -> str:
        # Initialize training client just to get the tokenizer for the base model
        training_client = self.client.create_lora_training_client(base_model=model, rank=1)
        tokenizer = training_client.get_tokenizer()
        
        # Init sampling client for generation
        sampling_client = self.client.create_sampling_client(base_model=model)
        
        # Tokenize prompt
        tokens = tokenizer.encode(prompt_text)
        prompt = types.ModelInput.from_ints(tokens=tokens)
        
        # Sampling parameters
        params = types.SamplingParams(
            max_tokens=1024,
            temperature=temperature,
            stop=["<|im_end|>"]
        )

        result = await sampling_client.sample_async(
            prompt=prompt,
            num_samples=1,
            sampling_params=params
        )

        response_seq = result.sequences[0]
        response_text = tokenizer.decode(response_seq.tokens).strip()
        return response_text
