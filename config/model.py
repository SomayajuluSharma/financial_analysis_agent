
import os
from pathlib import Path

from dotenv import load_dotenv
from strands.models.openai import OpenAIModel


# Locate the existing .env in the parent bootcamp directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def create_model():
    """Create the shared Groq model used by our agents."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in the bootcamp .env file"
        )

    return OpenAIModel(
        client_args={
            "api_key": api_key,
            "base_url": os.getenv(
                "GROQ_BASE_URL",
                "https://api.groq.com/openai/v1",
            ),
            "max_retries": 2,
        },
        model_id=os.getenv(
            "GROQ_MODEL_ID",
            "openai/gpt-oss-120b",
        ),
        params={
            "temperature": 0.2,
            "max_tokens": 6000,
        },
    )
