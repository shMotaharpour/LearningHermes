# Agent failure taxonomy

A pass rate tells you *how often*. A taxonomy tells you *what kind*, and only the second
one tells you what to fix. Tag every failing run with exactly one primary class — the
earliest point in the trajectory where things went wrong — and extend the list from your
own incidents.

The ordering matters: classes are listed in trajectory order, so "the earliest applicable
class" is just the first one that fits.

| Class | The agent… | Where it comes from | Usual fix |
|---|---|---|---|
| `misread-task` | solved a different problem than the one stated | ambiguous prompt, missing constraint | rewrite the task; add the constraint the agent could not have known |
| `missing-context` | lacked a fact it needed and had no way to get it | context files, memory, retrieval | Chapter 03 — fix what is in the prompt, not the model |
| `wrong-tool` | picked a tool that cannot answer the question | too many enabled tools, vague descriptions | Chapter 05 tool scoping; Chapter 11 filtering |
| `tool-misuse` | picked the right tool and called it wrong | bad schema, unclear parameter names | fix the tool's schema and description |
| `tool-failure` | called correctly, the tool errored or timed out | environment, credentials, network | runtime fix; then decide whether the agent should have retried |
| `ignored-result` | got the right tool result and answered as if it had not | context pressure, long trajectory | shorten the trajectory; Chapter 03 compression |
| `hallucination` | asserted something no tool result supports | model, prompt permissiveness | grounding instructions, a `NOT PRESENT` escape hatch, a stronger model |
| `format-drift` | was right but unusable by the consumer | under-specified output contract | state the contract; validate it deterministically |
| `overreach` | took an action nobody asked for | permissive toolset, no approval gate | Chapter 15 approvals; narrow the toolset |
| `gave-up` | returned a plan, a question, or an apology instead of an answer | unattended prompt written as if a human were watching | Chapter 07 — self-contained prompts, explicit empty case |
| `inefficient` | got there, expensively (loops, redundant reads) | no step budget, no cost signal | cost-per-task next to pass rate; step cap |

Two rules that make a taxonomy useful rather than decorative:

1. **One primary class per failure, at the earliest point.** A run that misread the task,
   then used the wrong tool, then hallucinated is `misread-task`. Fixing the hallucination
   would fix nothing.
2. **A class with no fix column is not a class.** If you cannot say what you would change,
   you have written a synonym for "it was bad".

`inefficient` is the one people leave out, and it is the one that shows up on the invoice.
A trajectory that reads the same file nine times passes every deterministic check.
