import json
import logging

import httpx

import config
from code_reviewer import CodeReviewer
from event_handler import EventHandler

logger = logging.getLogger(__name__)


class GitLab:
    @staticmethod
    async def get_merge_request_changes(project_id: int, merge_request_id: int):
        url = f"{config.GITLAB_API_URL}/projects/{project_id}/merge_requests/{merge_request_id}/diffs"
        headers = {"Private-Token": config.GITLAB_ACCESS_TOKEN}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        return response.json()

    @staticmethod
    def comment_on_merge_request(project_id, merge_request_id, comment):
        url = f"{config.GITLAB_API_URL}/projects/{project_id}/merge_requests/{merge_request_id}/notes"
        headers = {
            "Private-Token": config.GITLAB_ACCESS_TOKEN,
            "Content-Type": "application/json",
        }
        data = json.dumps({"body": comment})

        response = httpx.post(url, headers=headers, data=data)

        if response.status_code == 201:
            logger.warning("Comment posted successfully")
        else:
            logger.warning(
                f"Failed to post comment: {response.status_code} {response.text}"
            )


class GitLabEventHandler(EventHandler):
    async def handle_event(self):
        project_id = self.data["project"]["id"]
        merge_request_id = self.data["object_attributes"]["iid"]

        logger.warning("Process the merge request data and get the code diff")
        changes = await GitLab.get_merge_request_changes(project_id, merge_request_id)

        logger.warning("Interact with GPT to review code and post comments on GitLab")
        for review_result in await self.review_changes_at_once(changes):
            logger.warning(f"Review result: {review_result}")
            if review_result and review_result["should_comment"]:
                GitLab.comment_on_merge_request(
                    project_id,
                    merge_request_id,
                    comment=(
                        f"GPT Code Review\n"
                        f'Possible issues: {review_result["issues"]}\n'
                        f'Suggestions: {review_result["suggestions"]}'
                    ),
                )
            elif review_result is None:
                logger.error(
                    "Failed to get review result",
                )

    @staticmethod
    async def review_changes_at_once(changes: list[dict]) -> list[dict]:
        diffs = [
            {"file": change["new_path"], "diff": change["diff"]} for change in changes
        ]
        return [await CodeReviewer.review_code_diffs(diffs)]

    @staticmethod
    async def review_change_one_by_one(changes: list[dict]) -> list[dict]:
        results = []
        for change in changes:
            if change["deleted_file"]:
                continue
            diff = change["diff"]

            review_result = await CodeReviewer.review_code_diff(
                file_name=change["new_path"], diff=diff
            )
            results.append(review_result)

        return results
