# Contributing to SemanticDrift

Thank you for your interest in contributing to the SemanticDrift project! As this is an active research project, we welcome feedback, bug reports, and discussions.

## How to Contribute

### 1. Issue Discussions
We highly encourage discussing ideas in the Issues section before submitting Pull Requests.

### 2. Submitting Pull Requests
If you are contributing code, datasets, or documentation:
- Fork the repository and create your branch from `main`.
- If you've added code that should be tested, add tests.
- Ensure your code passes all linting and test suites.
- Update the documentation if applicable.
- Make sure your PR clearly describes the problem and solution.

### 3. Feedback on the Paper
If you have feedback on the study or its results, please use the `Research Feedback` issue template to share your thoughts.

## Development Environment
Python 3.11 or newer; the harness uses only the standard library (figures need `matplotlib`).
See the Quick start in the README for cloning the pinned AssetOpsBench source, validating the
dataset and running the tests. Please keep `python3 src/semdrift/validate_dataset.py` and the
test suite passing, and do not edit files listed in `datasets/MANIFEST.json` by hand.

## Code of Conduct
By participating, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

Thank you for helping advance research in Agentic AI reliability!
