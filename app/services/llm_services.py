import os
from langchain_aws import ChatBedrock

# This file now provides a unified Bedrock LLM interface using ChatBedrock,
# which supports both regular completions and tool-calling for agents.

class BedrockLLM:
    def __init__(self):
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.llm = ChatBedrock(
            model_id=self.model_id,
            region_name=self.region
        )

    def chat(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        # For simple completions, pass a single message.
        result = self.llm.invoke(
            [ {"role": "user", "content": prompt} ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        # The ChatBedrock response is an object with content as the reply.
        return result.content

    def get_llm(self):
        # Return the ChatBedrock instance for use in agents (LangGraph, etc.)
        return self.llm

# ✅ Instantiate the Bedrock client for convenience
llm_service = BedrockLLM()

# ✅ Synchronous interface
def generate_text(prompt: str) -> str:
    return llm_service.chat(prompt)

# ✅ For agent use (LangGraph), pass llm_service.get_llm() as the LLM object.
def get_agent_llm():
    return llm_service.get_llm()

# ✅ Asynchronous interface (used in FastAPI)
import asyncio
async def generate_text_async(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_text, prompt)