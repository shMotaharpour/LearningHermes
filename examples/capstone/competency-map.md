# Competency-to-evidence map

The portfolio's index, and the thing an interviewer actually wants. Copy it, fill it in
against your own capstone, and keep it in your repo's README.

Ten competency clusters, from the job evidence in `CURRICULUM.md` — regenerate the counts
with `python3 scripts/job_evidence_stats.py`, never by hand.

| Cluster | Chapters | Your artifact | Where it lives | The question it answers |
|---|---|---|---|---|
| Agentic orchestration | 01, 05, 09 | | | "Walk me through an agent loop you built." |
| Shipping & DevOps | 13 | | | "How does your agent work get to production?" |
| Evaluation & observability | 14 | | | "How do you know a change made it better?" |
| Stakeholder/product skills | 06, 08, 16 | | | "Who uses this, and how did you find out it helped?" |
| RAG & context engineering | 03, 03b | | | "Walk me through your chunking and your abstention logic." |
| Security & governance | 15 | | | "It has write access. Why is that safe?" |
| Prompt & context engineering | 03, 10 | | | "What is in your prompt, and what did you take out?" |
| API & systems integration | 12 | | | "How does it talk to systems you don't own?" |
| Workflow automation platforms | 07, 08 | | | "What runs without you, and how do you know it ran?" |
| Cost & performance optimization | 02, 15 | | | "What does it cost, and what is the dominant term?" |

## How to fill a row

An artifact is a thing with a URL or a path. Three rules:

1. **A commit, a file, or an output — not a claim.** "Built an eval harness" is a claim.
   `evals/compare.py` plus a baseline and a diff that caught a regression is an artifact.
2. **One artifact can serve two rows, but say how each row uses it.** The same nightly job
   is evidence for automation *and* for observability, for different reasons.
3. **An empty row is information.** It tells you where to spend your next week, and it is
   better to know before an interview than during one.

## The three artifacts that carry the most weight

Interviewers ask about these disproportionately, and they are the ones a demo cannot fake:

- **A regression you caught.** The eval diff, and what you did about it. This proves the
  gate is wired into your change process rather than decorating it.
- **An incident you handled.** The postmortem — `postmortem-template.md`, and
  `postmortem-example.md` for the shape. Detection time is the number they will ask for.
- **A risk you accepted.** Something you deliberately did *not* guard against, with the
  reasoning. This is the clearest single signal of seniority in the whole portfolio,
  because it requires having thought about cost rather than only about correctness.
