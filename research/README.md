# Research record

How the study was designed, checked and run, kept as it happened. Start with the
pre-registration and the findings; the rest is supporting detail.

| File or folder | What's in it |
|---|---|
| [`PREREG.md`](PREREG.md) | Hypotheses, measures and analysis plan, fixed before any paid model call, plus every later deviation with its date and reason |
| [`FINDINGS.md`](FINDINGS.md) | Append-only notebook: what each stage showed, with numbers and sources |
| [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) | Confirmatory and exploratory analyses, and how the data is preserved |
| [`RUNBOOK.md`](RUNBOOK.md) | The exact commands, pass criteria and spend caps used to run the experiment |
| [`LOG.md`](LOG.md) | Dated decision log |
| `01-literature/` | Related-work review, citation verification and the BibTeX file |
| `02-design/` | The design, model choice and pricing, and the reviews that shaped them |
| `03-dataset/` | Dataset notes, the meaning audit of every paraphrase, the manual review and the validation report |
| `04-harness/` | Notes on the experiment harness and its code-quality pass |
| `prompts/` | The prompts given to AI assistants during the project (see below) |

## How AI assistants were used

This project was done by one author with help from AI tools, and the record shows where:

- **Literature search:** ChatGPT produced first drafts of the related-work review. Every citation
  was then checked against arXiv; 7 of the first 21 arXiv IDs it gave were wrong and were
  corrected or dropped (`01-literature/verification.md`).
- **Code and data:** OpenAI Codex wrote much of the dataset tooling and harness from the prompts
  in `prompts/`. Claude (Anthropic) reviewed that work, wrote parts of the harness, checked
  results and drafted documentation.
- **Paraphrases:** the paraphrased, vaguer and narrower catalogs were written by a language model.
  The riskiest paraphrases were reviewed by the author, and all of them went through a meaning
  audit.
- **Decisions:** design choices, the manual review and the final interpretation are the
  author's.

Raw AI answers are kept as received (for example `01-literature/chatgpt-response.md`) and are
marked as not citable; only the verified versions are used.
