import json
from typing import TypedDict

import openai

import config

CodeDiff = TypedDict(
    "CodeDiff",
    {
        "file": str,
        "diff": str,
    },
)


class CodeReviewer:
    @staticmethod
    async def review_code_diff(file_name: str, diff: str):
        prompt = (
            f"Act a expert software tech lead during code review.\n"
            f"Take into account that this only snippet, it does not contain full code.\n"
            f"Does this code diffs contain any issues? Can it be improved?\n"
            f"Answer in valid json format in the following form:\n"
            f'{{"should_comment": bool, "issues": "<possible issues with code with detailed explanation why>", "suggestions": "<suggestions of improvements that can be introduced to code with explanation why"}}\n\n'
            f"Let's work this out in a step by step way to be sure we have the right answer.\n"
            f"```\n"
            f"{diff}\n"
            f"```\n\n"
            f"Let's work this out in a step by step way to be sure we have the right answer\n"
        )

        response = openai.ChatCompletion.create(
            model=config.GPT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
            ],
        )

        review_result = response.choices[0].message.content
        try:
            review_result = json.loads(review_result)
        except json.decoder.JSONDecodeError:
            review_result = None

        return {**review_result, "file": file_name} if review_result else None

    @staticmethod
    async def review_code_diffs(diffs: list[CodeDiff]):
        initial_prompt = (
            f"Act a expert software tech lead during code review.\n"
            f"Take into account that this only snippet, it does not contain full code.\n"
            f"Does this code diffs contain any issues? Can it be improved?\n"
            f"Answer in valid json format in the following form:\n"
            f'{{"should_comment": bool, "issues": "<possible problems with code with detailed explanation why>", "suggestions": "<suggestions of improvements that can be introduced to code with explanation why"}}\n\n'
            f"Remember to format it readably and add new lines to your answer.\n"
        )

        diff_messages = [
            {
                "role": "user",
                "content": f"File: {diff['file']}```\n{diff['diff']}\n```\n",
            }
            for diff in diffs
        ]
        response = openai.ChatCompletion.create(
            model=config.GPT_MODEL,
            messages=[
                {"role": "system", "content": initial_prompt},
                *diff_messages,
                {
                    "role": "user",
                    "content": "Let's work this out in a step by step way to be sure we have the right answer\n",
                },
            ],
        )

        review_result = response.choices[0].message.content
        try:
            review_result = json.loads(review_result)
        except json.decoder.JSONDecodeError:
            review_result = None

        return review_result
