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

        self.default_model = "Qwen/Qwen3-8B"
        client = tinker.ServiceClient(api_key=api_key)

        # Initialize sampling client and tokenizer once, synchronously, before any
        # event loop is running — avoids the sync-in-async warning and the per-call
        # tokenizer re-download overhead.
        self._sampling_client = client.create_sampling_client(base_model=self.default_model)
        training_client = client.create_lora_training_client(base_model=self.default_model, rank=1)
        self._tokenizer = training_client.get_tokenizer()

    def query(self, messages: List[Dict[str, str]], temperature: float = 0.0, model: str = None) -> str:
        prompt_text = ""
        for msg in messages:
            prompt_text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        prompt_text += "<|im_start|>assistant\n"

        return asyncio.run(self._async_query(prompt_text, temperature))

    async def _async_query(self, prompt_text: str, temperature: float) -> str:
        tokens = self._tokenizer.encode(prompt_text)
        prompt = types.ModelInput.from_ints(tokens=tokens)

        params = types.SamplingParams(
            max_tokens=4096,
            temperature=temperature,
            stop=["<|im_end|>"]
        )

        result = await self._sampling_client.sample_async(
            prompt=prompt,
            num_samples=1,
            sampling_params=params
        )

        response_seq = result.sequences[0]
        return self._tokenizer.decode(response_seq.tokens).strip()
