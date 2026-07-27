import json
import re
import time
from pathlib import Path
from typing import Any

from policy_ai.generation.generator import generate_answer
from policy_ai.retrieval.retriever import retrieve

TEST_CASES = [
    {
        "question": "What are the requirements for open tendering?",
        "expected_sections": ["A. Open Tender"],
        "expected_keywords": [
            "State portal",
            "advertising threshold",
            "seven days",
            "sections 96, 97, and 98",
        ],
        "should_refuse": False,
        "max_words": 150,
    },
    {
        "question": "When can restricted tendering be used?",
        "expected_sections": ["D. Restricted Tendering"],
        "expected_keywords": [
            "conditions",
            "section 102",
            "procurement thresholds",
            "at least ten persons",
            "known suppliers",
        ],
        "should_refuse": False,
        "max_words": 150,
    },
    {
        "question": "What is required during preliminary evaluation?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "eligibility requirements",
            "required format",
            "tender security",
            "duly signed",
            "required number of copies",
            "validity period",
            "required documents",
        ],
        "should_refuse": False,
        "max_words": 150,
    },
    {
        "question": "How should tenders be advertised?",
        "expected_sections": ["A. Open Tender"],
        "expected_keywords": [
            "State portal",
            "advertising threshold",
            "Second Schedule",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "What is the minimum preparation time for open tenders?",
        "expected_sections": ["A. Open Tender"],
        "expected_keywords": [
            "seven days",
            "national",
            "county specific",
        ],
        "should_refuse": False,
        "max_words": 100,
    },
    {
        "question": "What checks are performed during technical evaluation?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "technical requirements",
            "goods",
            "works",
            "services",
            "rejected",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "How is the evaluated tender price determined?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "bid price",
            "minor deviations",
            "common currency",
            "exchange rate",
            "margin of preference",
            "ranked",
        ],
        "should_refuse": False,
        "max_words": 150,
    },
    {
        "question": "What information must be included in an evaluation report?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "tenders received",
            "preliminary evaluation",
            "technical evaluation",
            "rejected",
            "evaluated price",
            "ranking",
            "recommendation",
        ],
        "should_refuse": False,
        "max_words": 150,
    },
    {
        "question": "When should a tender be rejected as non-responsive?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "technical requirements",
            "major deviation",
            "miscalculation",
            "disqualification",
            "non-responsive",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "How should the mode of tender submission be communicated?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "tender advertisement invitation",
            "electronically",
            "manually",
        ],
        "should_refuse": False,
        "max_words": 100,
    },
    {
        "question": "What procurement thresholds apply to restricted tendering?",
        "expected_sections": ["D. Restricted Tendering"],
        "expected_keywords": [
            "Second Schedule",
            "procurement thresholds",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "How many suppliers should be invited for restricted tendering?",
        "expected_sections": ["D. Restricted Tendering"],
        "expected_keywords": [
            "at least ten persons",
            "known suppliers",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "What happens after preliminary evaluation is completed?",
        "expected_sections": ["PART VII- BASIC PROCUREMENT RULES"],
        "expected_keywords": [
            "technical evaluation",
            "technical requirements",
            "financial evaluation",
            "evaluated price",
        ],
        "should_refuse": False,
        "max_words": 120,
    },
    {
        "question": "What is the corporate income tax rate in Kenya?",
        "expected_sections": [],
        "expected_keywords": [],
        "should_refuse": True,
        "max_words": 60,
    },
    {
        "question": "Who is the current Cabinet Secretary for Health?",
        "expected_sections": [],
        "expected_keywords": [],
        "should_refuse": True,
        "max_words": 60,
    },
]


def evaluate(
    output_path: str | Path = "data/evaluation/results.json",
) -> Path:
    results: list[dict[str, Any]] = []

    for case in TEST_CASES:
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
