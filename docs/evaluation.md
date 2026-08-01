# Evaluation Results

## Overview

PolicyAI is evaluated on retrieval quality, citation use, unsupported-question refusal, response length, and answer completeness.

The current benchmark contains 15 procurement-regulation questions:

- 13 supported questions
- 2 unsupported questions

## Latest Results

| Metric                   | Result |
| ------------------------ | -----: |
| Top-1 retrieval accuracy |   100% |
| Top-5 retrieval accuracy |   100% |
| Citation rate            |   100% |
| Refusal accuracy         |   100% |
| Word-limit compliance    |   100% |
| Answer completeness      |  92.3% |

## What the Metrics Mean

- **Top-1:** The expected section ranked first.
- **Top-5:** The expected section appeared in the first five results.
- **Citation rate:** Supported answers included source citations.
- **Refusal accuracy:** Unsupported questions were rejected correctly.
- **Word-limit compliance:** Answers stayed within the required length.
- **Answer completeness:** Answers covered the expected key points.

## Current Assessment

PolicyAI retrieves the correct evidence consistently, cites its sources, and refuses unsupported questions. The main remaining weakness is completeness for broad questions that require several provisions from the same section.
