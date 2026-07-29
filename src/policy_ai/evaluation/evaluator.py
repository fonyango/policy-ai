import json
import re
import time
from pathlib import Path
from typing import Any

from policy_ai.generation.generator import generate_answer
from policy_ai.retrieval.retriever import retrieve

TEST_CASES_PATH = Path("data/evaluation/test_cases.json")


def load_test_cases() -> list[dict[str, Any]]:
    return json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))


def evaluate(
    output_path: str | Path = "data/evaluation/results.json",
) -> Path:
    results: list[dict[str, Any]] = []

    test_cases = load_test_cases()

    for case in test_cases:
        question = case["question"]

        start_time = time.perf_counter()

        retrieved = retrieve(question, limit=5)
        generated = generate_answer(
            question,
            limit=5,
            sources=retrieved,
        )

        response_time = time.perf_counter() - start_time

        retrieved_sections = [result["section"] for result in retrieved]

        expected_sections = case["expected_sections"]

        top_1_hit = bool(
            retrieved_sections and retrieved_sections[0] in expected_sections
        )

        top_5_hit = any(section in expected_sections for section in retrieved_sections)

        answer = generated["answer"]

        answer_word_count = len(answer.split())

        answer_lower = answer.lower()

        matched_keywords = [
            keyword
            for keyword in case["expected_keywords"]
            if keyword.lower() in answer_lower
        ]

        keyword_recall = (
            len(matched_keywords) / len(case["expected_keywords"])
            if case["expected_keywords"]
            else None
        )

        answer_complete = keyword_recall >= 0.6 if keyword_recall is not None else True

        under_word_limit = answer_word_count <= case["max_words"]

        refusal_phrases = [
            "could not find",
            "not enough evidence",
            "insufficient evidence",
            "not supported by the supplied sources",
        ]

        refused = any(phrase in answer.lower() for phrase in refusal_phrases)

        refusal_correct = refused if case["should_refuse"] else not refused

        citation_count = len(re.findall(r"\[Source \d+\]", answer))

        results.append(
            {
                "question": question,
                "expected_sections": expected_sections,
                "retrieved_sections": retrieved_sections,
                "top_1_hit": top_1_hit,
                "top_5_hit": top_5_hit,
                "top_score": (round(retrieved[0]["score"], 4) if retrieved else None),
                "citation_count": citation_count,
                "has_citations": citation_count > 0,
                "response_time_seconds": round(response_time, 2),
                "should_refuse": case["should_refuse"],
                "refused": refused,
                "refusal_correct": refusal_correct,
                "answer_word_count": answer_word_count,
                "max_words": case["max_words"],
                "under_word_limit": under_word_limit,
                "answer": answer,
                "expected_keywords": case["expected_keywords"],
                "matched_keywords": matched_keywords,
                "keyword_recall": (
                    round(keyword_recall, 4) if keyword_recall is not None else None
                ),
                "answer_complete": answer_complete,
            }
        )

    supported_results = [result for result in results if not result["should_refuse"]]

    answered_results = [result for result in supported_results if not result["refused"]]

    summary = {
        "total_questions": len(results),
        "top_1_accuracy": sum(result["top_1_hit"] for result in supported_results)
        / len(supported_results),
        "top_5_accuracy": sum(result["top_5_hit"] for result in supported_results)
        / len(supported_results),
        "citation_rate": sum(result["has_citations"] for result in answered_results)
        / len(answered_results),
        "average_response_time_seconds": round(
            sum(result["response_time_seconds"] for result in results) / len(results),
            2,
        ),
        "word_limit_rate": sum(result["under_word_limit"] for result in results)
        / len(results),
        "refusal_accuracy": sum(result["refusal_correct"] for result in results)
        / len(results),
        "average_answer_word_count": round(
            sum(result["answer_word_count"] for result in results) / len(results),
            2,
        ),
        "answer_completeness_rate": sum(
            result["answer_complete"] for result in supported_results
        )
        / len(supported_results),
    }

    output = {
        "summary": summary,
        "results": results,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    saved_path = evaluate()
    print(f"Saved evaluation results to: {saved_path}")
