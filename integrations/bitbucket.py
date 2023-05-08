import logging

import httpx
import config
from code_reviewer import CodeReviewer

from event_handler import EventHandler

logger = logging.getLogger(__name__)


class Bitbucket:
    @staticmethod
    async def get_pull_request_changes(
        diff_link: str,
    ):
        headers = {"Authorization": f"Bearer {config.BITBUCKET_ACCESS_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(diff_link, headers=headers)
        return response.text

    @staticmethod
    def comment_on_pull_request(
        workspace: str, repo_slug: str, pull_request_id: int, comment: str
    ):
        url = f"{config.BITBUCKET_API_URL}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/comments"
        headers = {
            "Authorization": f"Bearer {config.BITBUCKET_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        response = httpx.post(url, headers=headers, json={"content": {"raw": comment}})

        if response.status_code == 201:
            logger.warning("Comment posted successfully")
        else:
            logger.warning(
                f"Failed to post comment: {response.status_code} {response.text}"
            )


class BitbucketEventHandler(EventHandler):
    async def handle_event(self):
        pull_request_id = self.data["pullrequest"]["id"]
        repo_slug = self.data["repository"]["uuid"]
        workspace = self.data["repository"]["workspace"]["uuid"]
        diff_link = self.data["pullrequest"]["links"]["diff"]["href"]

        logger.warning("Get the pull request changes (diff)")
        diff = await Bitbucket.get_pull_request_changes(diff_link)

        logger.warning(
            "Process the diff, review it using GPT, and post comments on Bitbucket"
        )
        review_result = await CodeReviewer.review_code_diff(
            file_name=f"",
            diff=diff,
        )
        logger.warning(f"Review result: {review_result}")

        if review_result and review_result["should_comment"]:
            Bitbucket.comment_on_pull_request(
                workspace,
                repo_slug,
                pull_request_id,
                comment=(
                    f"GPT Code Review\n\n"
                    f""
                    f'Possible issues: \n{review_result["issues"]}\n\n'
                    f'Suggestions: \n{review_result["suggestions"]}'
                ),
            )
        elif review_result is None:
            logger.error(
                "Failed to get review result",
            )
