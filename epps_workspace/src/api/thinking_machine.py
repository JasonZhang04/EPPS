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
        # Upgraded to the Instruct VL model for strict Pydantic JSON adherence
        # self.default_model = "Qwen/Qwen3-VL-30B-A3B-Instruct"
        self.default_model = "Qwen/Qwen3-4B-Instruct-2507"

        # Initialize tokenizer and sampling client once to avoid per-query overhead
        training_client = self.client.create_lora_training_client(base_model=self.default_model, rank=1)
        self.tokenizer = training_client.get_tokenizer()
        self.sampling_client = self.client.create_sampling_client(base_model=self.default_model)

    def query(self, messages: List[Dict[str, str]], temperature: float = 0.0, model: str = None) -> str:
        prompt_text = ""
        for msg in messages:
            prompt_text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        prompt_text += "<|im_start|>assistant\n"

        return asyncio.run(self._async_query(prompt_text, temperature, self.sampling_client, self.tokenizer))

    async def _async_query(self, prompt_text: str, temperature: float, sampling_client, tokenizer) -> str:
        # Tokenize prompt
        tokens = tokenizer.encode(prompt_text)
        prompt = types.ModelInput.from_ints(tokens=tokens)

        params = types.SamplingParams(
            max_tokens=4096,
            temperature=temperature,
            stop=["<|im_end|>"]
        )

        # Only the actual sampling is awaited
        result = await sampling_client.sample_async(
            prompt=prompt,
            num_samples=1,
            sampling_params=params
        )

        response_seq = result.sequences[0]
        response_text = tokenizer.decode(response_seq.tokens).strip()

        # Scrub the stop token so it doesn't break JSON parsing
        response_text = response_text.replace("<|im_end|>", "").strip()

        return response_text
