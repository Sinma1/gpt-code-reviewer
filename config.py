import os

import openai

env = os.environ

SERVICE_TOKEN = env.get("SERVICE_TOKEN", "secret-service-token")
OPEN_AI_KEY = env.get("OPENAI_API_KEY")
GITLAB_API_URL = env.get("GITLAB_API_URL", default="https://gitlab.com/api/v4")
GITLAB_ACCESS_TOKEN = env.get("GITLAB_ACCESS_TOKEN")
BITBUCKET_API_URL = env.get(
    "BITBUCKET_API_URL", default="https://api.bitbucket.org/2.0"
)
BITBUCKET_ACCESS_TOKEN = env.get("BITBUCKET_ACCESS_TOKEN")

GPT_MODEL = env.get("GPT_MODEL", default="gpt-3.5-turbo")

# Validate environment variables
if not OPEN_AI_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Set up the OpenAI API key
openai.api_key = OPEN_AI_KEY

if not GITLAB_ACCESS_TOKEN and not BITBUCKET_ACCESS_TOKEN:
    raise ValueError(
        "GITLAB_ACCESS_TOKEN or BITBUCKET_ACCESS_TOKEN environment variable is not set"
    )
