# Incident response runbook

## Declaring an incident

Any engineer may declare an incident. Declaring early is cheap; declaring late is not.
Page the on-call rotation through the alerting channel, never by direct message — a direct
message has no escalation path if the person is asleep.

## Severity levels

SEV1 means customer-facing data loss or a full outage. SEV2 means degraded service for a
subset of customers. SEV3 is everything else that still needs tracking. Severity is set by
the incident commander and may be revised in either direction as facts arrive.

## The global stop

When the blast radius is "everything scheduled", engage the global stop rather than pausing
jobs one at a time. It halts new work and leaves in-flight work running. Record the reason.
Leaving the stop engaged is itself an incident: nothing scheduled runs while it is on.

## Postmortems

Every SEV1 and SEV2 gets a written postmortem within five working days. Postmortems are
blameless and name mechanisms, not people. A postmortem with no action item is not finished.
