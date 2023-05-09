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


PROMPT_BASE = (
    "Act as an expert software tech lead during code review.\n"
    "Take into account that this is only a snippet, it does not contain full code.\n"
    "Answer in valid json in the following form:\n"
    '{{"should_comment": bool, "issues": "<possible issues with code with detailed explanation why>", "suggestions": "<suggestions of improvements that can be introduced to code with explanation why"}}\n\n'
    "Remember to format it readably and include newlines in your answer.\n"
)

# Having this exact phrase at the *end* of the prompt improves results
# https://openreview.net/forum?id=92gvk82DE-
STEP_BY_STEP = "Let’s work this out in a step by step way to be sure we have the right answer"

class CodeReviewer:
    @staticmethod
    async def review_code_diff(file_name: str, diff: str):
        prompt = (
            f"{PROMPT_BASE}\n"
            f"```\n"
            f"{diff}\n"
            f"```\n\n"
            f"Does this diff contain any issues? Can it be improved?\n"
            f"{STEP_BY_STEP}"
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
                {"role": "system", "content": PROMPT_BASE},
                *diff_messages,
                {
                    "role": "user", 
                    "content": (
                        f"Do these diffs contain any issues? Can they be improved?\n"
                        f"{STEP_BY_STEP}"
                    ),
                },
            ],
        )

        review_result = response.choices[0].message.content
        try:
            review_result = json.loads(review_result)
        except json.decoder.JSONDecodeError:
            review_result = None

        return review_result
