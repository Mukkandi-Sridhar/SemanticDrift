# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dataset: 36 AssetOpsBench MCP tools at commit `0d04406`, nine description catalogs
  (original, placebo, three paraphrases, vaguer, narrower, and two built from the repository's
  git history), and 152 labelled requests.
- Experiment harness: request building for OpenAI (Responses API) and OpenRouter, a resumable
  parallel runner with spend caps and a run ledger, scoring, analysis and figures.
- Pre-registration, design notes, findings notebook and decision log in `research/`.
- Results of the main run: 38,304 decisions from ten models (scores, analysis and figures).
- CI that validates the dataset and runs the tests against the pinned AssetOpsBench commit.

### Changed
- README rewritten around the study that was run.
- The June 2026 proposal moved to `docs/history/`.

## [0.1.0] - 2026-06-29

### Added
- Initial repository setup for the Semantic Drift research project.
- Research proposal and README.md.
- Project structure including placeholders for datasets, paper, and code.
- Issue and PR templates.
- Code of Conduct, Contributing guidelines, and Security policies.
- GitHub Actions workflow for repository validation.
