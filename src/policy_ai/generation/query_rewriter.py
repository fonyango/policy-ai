from ollama import chat

MODEL_NAME = "qwen3:8b"


def rewrite_query(
    question: str,
    history: list[dict[str, str]],
) -> str:
    if not history:
        return question

    conversation = "\n".join(
        f"User: {item['question']}\nAssistant: {item['answer']}"
        for item in history[-3:]
    )

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite the latest question as a standalone search query. "
                    "Use the conversation only to resolve references such as "
                    "'that', 'it', or 'the same rule'. "
                    "Return only the rewritten question."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Conversation:\n{conversation}\n\n" f"Latest question:\n{question}"
                ),
            },
        ],
        think=False,
        options={
            "temperature": 0,
            "num_predict": 80,
        },
    )

    rewritten = response.message.content.strip()
    return rewritten or question
