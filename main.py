import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, Request, Header, Depends, HTTPException
from fastapi.params import Param

from integrations.bitbucket import BitbucketEventHandler
from integrations.gitlab import GitLabEventHandler

import config

logger = logging.getLogger(__name__)

app = FastAPI()

logger.warning("GPT model: " + config.GPT_MODEL)


@app.get("/")
async def root():
    return {"status": "ok"}


def require_service_token(service_token: str = Param()):
    if service_token != config.SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid service token")


@app.post("/code-review/gitlab", dependencies=[Depends(require_service_token)])
async def review_code_gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(),
):
    logger.warning("Received GitLab webhook")
    data = await request.json()
    action = data.get("object_attributes", {}).get("action")
    if x_gitlab_event == "Merge Request Hook" and action == "open":
        asyncio.create_task(GitLabEventHandler(data).handle_event())

    logger.warning("Finished processing GitLab webhook")
    return {"status": "ok"}


@app.post("/code-review/bitbucket", dependencies=[Depends(require_service_token)])
async def review_code_bitbucket_webhook(
    request: Request,
    x_event_key: str = Header(),
):
    logger.warning("Received Bitbucket webhook")
    data = await request.json()
    if x_event_key == "pullrequest:created" or x_event_key == "pullrequest:updated":
        asyncio.create_task(BitbucketEventHandler(data).handle_event())

    logger.warning("Finished processing Bitbucket webhook")
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
