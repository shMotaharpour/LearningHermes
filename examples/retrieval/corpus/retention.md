# Data retention policy

## Session transcripts

Agent session transcripts are retained for 90 days, then deleted. Transcripts containing
customer data are retained for 30 days. There is no archival tier: deleted means deleted.

## Backups

Full backups are kept for 7 rotations. Older archives are pruned automatically after each
successful full backup. Backups contain environment files, so every retained copy is another
place credentials live — retention here is a security decision, not a storage one.

## Logs

Runtime logs are retained for 14 days. Error logs are retained for 90 days. Logs are never
the system of record for anything a customer might ask about.

## Exceptions

A retention exception requires written approval from the data owner and an expiry date. An
exception without an expiry date is a policy change, and goes through the policy process.
