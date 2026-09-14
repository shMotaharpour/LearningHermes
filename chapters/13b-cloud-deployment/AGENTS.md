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

## The AI-stack section is on a shorter clock than the rest

"Google's AI stack, and which layer you are building at" is the most perishable content in
the course: product names, boundaries and availability move faster than anything else here,
and this repo can verify none of them.

Rules for it, enforced by `tests/test_cloud_manifests.py`:

- It keeps its `**Snapshot: YYYY-MM-DD.**` line, and that date must EQUAL the chapter's
  `Reviewed:` date. Re-reviewing the chapter means re-checking this section; if you cannot
  re-check it, do not re-date the chapter.
- It keeps the instruction to verify every product name against current documentation.
- The "what is not checked" table keeps admitting the section is in it.
- Edit the middle column (the product names) freely as things change. Do NOT let the other
  columns — the layer, when it is right, what you give up — drift into product marketing.
  Those columns are why the section survives a rename; the names are not.

## Care

- `kubectl apply --dry-run=client` is deliberately not used: it contacts a cluster for the
  OpenAPI schema, so it is not an offline check. The chapter says so; keep that.
- The tests skip without PyYAML and without terraform. Keep both skips — the suite must pass
  on a bare interpreter.
- Every quoted `gcloud`/`kubectl` line is unverified by construction. If you add one, it does
  not go through `verify_chapters.py` (there is no Hermes command here to check) and the
  only guard is your reading of the provider's current docs. Say where you checked it.
