# utils/llm_loader.py

import os
from dotenv import load_dotenv

# OpenAI SDK
from openai import OpenAI

# Azure OpenAI via LangChain
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import AzureOpenAIEmbeddings

load_dotenv()

def get_llm():
    """
    Returns the appropriate chat LLM client (AzureChatOpenAI or OpenAI).
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "azure":
        return AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            openai_api_type="azure",
            temperature=0.2
        )
    else:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding_client():
    """
    Returns the embedding client (AzureOpenAIEmbeddings or OpenAI).
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "azure":
        return AzureOpenAIEmbeddings(
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
        )
    else:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
