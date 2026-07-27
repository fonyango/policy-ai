# Evaluation Results

## Purpose

The evaluation measures whether PolicyAI retrieves the correct evidence, produces cited answers, refuses unsupported questions, respects response-length limits, and covers expected answer content.

## Current Test Set

The current benchmark contains 15 questions:

- 13 supported questions based on the indexed procurement regulations
- 2 unsupported questions designed to test refusal behavior

Question types include:

- open tendering requirements
- restricted tendering
- preliminary evaluation
- technical evaluation
- financial evaluation
- evaluation reports
- exact procedural questions
- unsupported tax and current-office-holder questions

## Latest Results

| Metric                             |        Result |
| ---------------------------------- | ------------: |
| Total questions                    |            15 |
| Top-1 retrieval accuracy           |          100% |
| Top-5 retrieval accuracy           |          100% |
| Citation rate                      |          100% |
| Unsupported-query refusal accuracy |          100% |
| Word-limit compliance              |          100% |
| Answer completeness                |         84.6% |
| Average response time              | 10.96 seconds |
| Average answer length              |      66 words |

## Metric Definitions

### Top-1 Retrieval Accuracy

The proportion of supported questions where the expected section ranked first.

### Top-5 Retrieval Accuracy

The proportion of supported questions where the expected section appeared within the first five results.

### Citation Rate

The proportion of generated supported answers containing at least one `[Source X]` citation.

### Refusal Accuracy

The proportion of questions where the system correctly answered supported questions and refused unsupported questions.

### Word-Limit Compliance

The proportion of answers that remained within the test-specific word limit.

### Answer Completeness

The proportion of supported answers that matched at least 60% of expected answer keywords.

### Response Time

Elapsed time for retrieval and answer generation during evaluation.

## Strong Results

The current system performs well in:

- locating the correct document section
- rejecting unsupported questions
- producing concise answers
- adding source citations consistently
- answering direct procedural questions

## Known Evaluation Weakness

The current metrics show that PolicyAI is a strong MVP but requires further improvements. The main weakness is answer completeness for broad sections containing several legal provisions.
