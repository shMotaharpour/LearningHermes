# Model cost policy

## Tiers

Unsupervised and scheduled work runs on the cheap tier with capped output. Interactive work
may use the strong tier. Mixture-of-agents is reserved for judgment calls — architecture
reviews, eval design — because it multiplies cost by the number of slots.

## Auxiliary models

Compression, session titling, and vision pre-processing run on small auxiliary models. An
unreviewed auxiliary model is the classic silent cost leak: a large model titling sessions
burns money invisibly on every turn.

## Review

Token spend is reviewed weekly. A week-over-week jump of more than 40 percent is
investigated before the next review, not at it.

## Budgets

Every scheduled job has an owner and a monthly budget. A job with no owner is deleted at the
next review, whatever it does.
