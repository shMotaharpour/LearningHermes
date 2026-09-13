# Engineer onboarding

## First week

Get access to the repository, the alerting channel, and the staging environment. Run the
project's verification pass end to end before changing anything: if you cannot tell whether
the app builds and starts, you cannot tell whether your first change broke it.

## Pairing

New engineers pair for their first two weeks. Pairing is for transferring context that is
not written down anywhere, which is most of it.

## First on-call shift

No engineer takes an on-call shift before shadowing two. Shadowing means being paged at the
same time as the primary and writing your own diagnosis before reading theirs.

## Tooling

Install the agent CLI and run its health check. Credentials go in the environment file, never
in configuration and never in a commit.
