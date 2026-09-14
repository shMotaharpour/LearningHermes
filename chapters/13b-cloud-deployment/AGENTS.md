# Chapter 13b — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Evidence standard — read before editing

This is the **only** chapter with a `Reviewed:` header instead of `Verified:`, because no
GCP project, Terraform registry or Kubernetes cluster is reachable from this repo. The
validator lists it in `REVIEWED_CHAPTERS` and enforces both directions: this chapter may not
claim `Verified:`, and no other chapter may use `Reviewed:`.

Do not "upgrade" the header without actually gaining the ability to run the commands, and do
not add a second chapter to that allowlist without a reason as concrete as this one. The
weaker standard existing at all is only defensible while it stays exceptional.

## Scope boundary

Deploying the gateway to GCP: Cloud Run and GKE, identity, secrets, the data layer, egress
at the platform layer, image pinning. Local and SSH backends stay in 13; the security
*reasoning* is 15's and is applied here rather than restated.

## Ships

`examples/cloud-gcp/` — Terraform for Cloud Run + Cloud SQL, GKE manifests, a default-deny
NetworkPolicy. Pinned by `tests/test_cloud_manifests.py`, which checks the DECISIONS (digest
pinning, no CPU limit, non-root, PDB, DNS egress, no secrets in HCL) rather than schemas.

## Care

- `kubectl apply --dry-run=client` is deliberately not used: it contacts a cluster for the
  OpenAPI schema, so it is not an offline check. The chapter says so; keep that.
- The tests skip without PyYAML and without terraform. Keep both skips — the suite must pass
  on a bare interpreter.
- Every quoted `gcloud`/`kubectl` line is unverified by construction. If you add one, it does
  not go through `verify_chapters.py` (there is no Hermes command here to check) and the
  only guard is your reading of the provider's current docs. Say where you checked it.
