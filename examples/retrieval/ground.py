#!/usr/bin/env python3
"""Turn retrieved chunks into a grounded, cited answer — or refuse.

    python3 ground.py "how long are transcripts kept?" --dry   # show the prompt, no model
    python3 ground.py "how long are transcripts kept?"         # needs `hermes` on PATH
    python3 ground.py "what is our parental leave allowance?"  # watch it refuse

Retrieval is half a RAG system. This is the half where grounding is won or lost, and it
comes down to three decisions that have nothing to do with vector math:

1. WHAT THE MODEL IS ALLOWED TO USE. The prompt says: answer only from the passages, and
   if they do not contain the answer, say so. An instruction is not enforcement — see (3).
2. HOW CITATIONS ARE REQUESTED. Every claim carries [doc#chunk]. Asking for citations in a
   form you can PARSE is what makes the next step possible.
3. WHETHER THE CITATIONS ARE CHECKED. This is the step people skip. A model will cite a
   passage that does not support its claim, and a citation nobody verifies is decoration
   that makes a wrong answer look sourced.

Step 3 is deterministic and cheap. Do it before you reach for an LLM judge.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import Retriever, build_chunks  # noqa: E402

CITATION = re.compile(r"\[([a-z0-9-]+#[a-z0-9]+)\]")

REFUSAL = "NOT IN THE DOCUMENTS"

TEMPLATE = """Answer the question using ONLY the passages below.

Rules:
- Every factual claim must end with its source in square brackets, like [doc#chunk].
- Use only the passage ids shown. Never invent one.
- If the passages do not contain the answer, reply with exactly: {refusal}
- Do not add background knowledge. You know nothing except these passages.

PASSAGES
{passages}

QUESTION
{question}
"""


def build_prompt(question: str, results) -> str:
    passages = "\n\n".join(f"[{chunk.citation}]\n{chunk.text}" for chunk, _ in results)
    return TEMPLATE.format(refusal=REFUSAL, passages=passages, question=question)


def check_citations(answer: str, results) -> dict:
    """Verify every citation the answer made. Deterministic; run it before any judge.

    Two failure modes, and they are different bugs:
      * INVALID — the id does not exist in what we retrieved. The model made it up.
      * UNSUPPORTED — the answer carries no citation at all while asserting something.
    """
    offered = {chunk.citation for chunk, _ in results}
    used = set(CITATION.findall(answer))
    invalid = sorted(used - offered)
    refused = answer.strip().startswith(REFUSAL)
    return {
        "citations": sorted(used),
        "invalid": invalid,
        "uncited_claim": not used and not refused and bool(answer.strip()),
        "refused": refused,
        "ok": not invalid and (refused or bool(used)),
    }


def ask_model(prompt: str, model: str | None) -> str:
    cmd = ["hermes", "chat", "-q", prompt, "--oneshot", "-t", "none"]
    if model:
        cmd += ["-m", model]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                          stdin=subprocess.DEVNULL)
    return ((proc.stdout or "") + (proc.stderr or "")).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--model")
    parser.add_argument("--dry", action="store_true", help="print the prompt, call nothing")
    args = parser.parse_args()

    results = Retriever(build_chunks()).search(args.question, k=args.k)

    # Refuse BEFORE the model is involved. A generator handed no passages will still write
    # something plausible, so the cheapest guard against an invented answer is never to ask.
    if not results:
        print(REFUSAL)
        print("\n(retrieval returned nothing above threshold — the model was never called,"
              "\n which is the cheapest possible defence against an invented answer)")
        return 0

    prompt = build_prompt(args.question, results)
    if args.dry:
        print(prompt)
        return 0
    if not shutil.which("hermes"):
        print("no `hermes` on PATH — use --dry to see the prompt.", file=sys.stderr)
        return 2

    answer = ask_model(prompt, args.model)
    print(answer)

    report = check_citations(answer, results)
    print("\n--- citation check")
    if report["refused"]:
        print("  refused, as instructed — no citation needed")
    if report["invalid"]:
        print(f"  INVALID citations (not among the retrieved passages): {report['invalid']}")
    if report["uncited_claim"]:
        print("  UNCITED: the answer asserts something and cites nothing")
    if report["ok"] and not report["invalid"]:
        print(f"  all {len(report['citations'])} citations resolve: {report['citations']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
