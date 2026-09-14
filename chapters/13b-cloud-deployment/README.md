# Chapter 13b — Cloud Deployment on GCP

> **Reviewed:** 2026-09-14 · NOT verified against a live GCP project · checked by `terraform fmt` and `tests/test_cloud_manifests.py`

## Why this matters (job link)

Chapter 13 ships an agent to a machine. Postings want it shipped to infrastructure.
Reflection asks for a "track record of deploying enterprise software in cloud or hybrid
environments using modern DevOps practices (**Docker, Kubernetes, and CI/CD**)"
(`docs/research/jobs/source-04.md`); Paramount wants work "leveraging modern platforms such
as **Vertex AI**" (`docs/research/jobs/source-01.md`); Databricks asks you to "architect and
implement robust, scalable ML infrastructure" (`docs/research/jobs/source-02.md`).

**Read the header first.** Every other chapter in this course carries `Verified:` and means
it — `scripts/verify_chapters.py` re-runs each quoted command. This chapter cannot make that
claim: no GCP project, no Terraform registry access and no Kubernetes cluster are available
to this repository, so its `gcloud` and `kubectl` invocations have not been executed here.
It carries a different header, the validator **requires** it to (and forbids every other
chapter from using it), and the difference is the point rather than an apology. A course
that quietly loosened its own standard the moment it became inconvenient would have taught
you the wrong lesson about engineering.

What *is* machine-checked is stated below and runs in CI.

## Concepts

Everything here lives in `examples/cloud-gcp/`.

### A gateway agent is not a web service, and the config says so

Most GCP guidance assumes a stateless request/response service. A gateway agent is not one,
and four lines in `terraform/main.tf` are where that stops being true:

| Setting | Why it is not the default |
|---|---|
| `min_instance_count = 1` | Scaling to zero drops platform connections and in-flight turns. There is no cold start that recovers a half-finished conversation. |
| `cpu_idle = false` | The agent loop is long-running and idles between tool calls. With CPU throttled between requests, a turn stalls — and it looks exactly like a slow model. |
| `StatefulSet`, not `Deployment` | It holds a session store and a stable identity, and wants an orderly restart rather than interchangeable pods. |
| generous `startupProbe` | It reconnects to every platform on boot. A tight probe restarts it mid-reconnect, forever. |

Each is a line of YAML or HCL, and each was learned by someone whose gateway kept dying.

### Cloud Run or GKE

Cloud Run for one gateway: it is a container with a service account and a scaling policy,
and the Terraform is ninety lines. GKE when you already run GKE, need sidecars, or need
node-level control.

Choosing GKE because it looks more serious is how teams acquire an operations burden they
did not need. Both are in `examples/cloud-gcp/` so the comparison is concrete: read
`terraform/main.tf` against `k8s/gateway.yaml` and notice how much of the second is
re-implementing what the first gets for free.

### Identity: the single most common finding

Two rules, and both are about a credential that should never exist:

- **One service account per service, with only the roles it needs.** The default compute
  service account is over-privileged by design. `roles/editor` on a gateway is a finding.
- **Workload Identity, not a key file.** A downloaded service-account JSON is a credential
  the platform cannot rotate and that outlives whoever created it. The annotation in
  `k8s/gateway.yaml` lets the pod authenticate *as* a GCP service account with no key
  anywhere.

This is Chapter 15's least-privilege argument at the infrastructure layer: the credential
you did not create cannot leak.

### Secrets are not Terraform's job

`terraform/main.tf` creates the *container* for a secret and never its value. **State is not
a vault.** Anything you put in a variable ends up in the state file, and the state file ends
up in a bucket somebody can read. Terraform declares that a secret exists and who may read
it; a human or a narrower CI identity writes the version.

A test asserts no secret value appears in the configuration, because this is the kind of
thing that gets added later under time pressure.

### The data layer is Chapter 03c's target

Cloud SQL for PostgreSQL with pgvector — `examples/retrieval-scale/schema.sql` runs against
exactly this instance. AlloyDB is the alternative when you want ScaNN indexing; the schema
does not change.

Two settings are deliberate: `ipv4_enabled = false` (a database reachable from the internet
is a finding, not a convenience) and `deletion_protection = true` (destroying the vector
store should require a decision, not a typo).

### Egress control at the platform layer

`k8s/networkpolicy.yaml` is default-deny egress: DNS, the database, and an egress proxy you
control. Everything else — model providers, messaging platforms — goes through the proxy, so
the allowlist lives in one auditable place.

This is `hermes egress` (Chapter 15) expressed a layer down, and the difference matters: the
agent cannot reach the internet directly **even if it is talked into trying.** A control
below the agent is not subject to the agent's judgement.

One trap with no error message, called out in the file itself: a NetworkPolicy needs a CNI
that enforces it (on GKE, Dataplane V2 or Calico). On a cluster without enforcement the
object **applies cleanly and does nothing**, and you will believe you have egress control.
That is the most dangerous failure mode in this chapter.

### Pin by digest

Both the Terraform and the manifest pin the image by `@sha256:`, and the Terraform computes
`image_is_digest_pinned` as an output so a tag-based deploy is visible rather than silent.

A tag is a moving pointer. "It worked yesterday" is not a rollback plan. This is the same
argument as `hermes plugins install --ref <sha>` in Chapter 12, and it recurs because it is
the real rule: **reproducibility is a property of your references, not of your intentions.**

### What is actually checked, and what is not

This is the part that makes the header honest rather than an excuse.

| Checked in CI | How |
|---|---|
| Terraform syntax and layout | `terraform fmt -check` |
| Manifests parse; every object has kind and name | `tests/test_cloud_manifests.py` |
| The *decisions* above | the same tests: digest pinning, no CPU limit, non-root, read-only root with a writable `/tmp`, PDB on a single replica, DNS in the egress policy, no secret values in HCL, private database, no `roles/editor` |
| **Not checked** | that any of it deploys. No `terraform init`, `plan` or `apply`; no cluster. |

Checking decisions rather than schemas turned out to be the more useful half. A manifest can
be perfectly valid and still pin by tag, run as root, and cap CPU on an agent loop — those
are the things a reviewer catches, so those are the things the tests catch.

`kubectl apply --dry-run=client` is *not* used, and the reason is worth knowing: it still
contacts a cluster to fetch the OpenAPI schema. "Client dry-run" validates client-side, not
offline.

### The general pattern

Strip GCP out and three claims remain, and they are what an interviewer is checking:

- **Know which of your defaults are wrong for your workload.** Scale-to-zero, CPU
  throttling and aggressive probes are correct for a request/response service and wrong for
  a long-lived agent. The senior move is being able to name which four lines you changed
  and why, not reciting a provider's tutorial.
- **Push controls below the thing they constrain.** An egress policy the agent cannot
  disable beats an instruction the agent might ignore. Same for a credential that never
  exists versus one you rotate.
- **Reproducibility is a property of your references.** Digest pins, immutable versions,
  state you can read back. Every layer of this course reaches the same conclusion, which is
  how you know it is the rule and not a convention.

**Evidence:** `docs/research/jobs/source-01.md`, `source-02.md`, `source-04.md` (the postings
quoted above). No `docs/research/hermes/` evidence is cited **because there is none to
cite** — this chapter quotes no Hermes commands, which is itself a consequence of its
subject. The configuration's properties are pinned by `tests/test_cloud_manifests.py`.

## Verified commands

**These are reviewed, not verified** — see the header. They are written from the providers'
documented interfaces and have not been executed by this repository. Run them against your
own project, and check them against the current provider reference first: cloud CLIs change
faster than this course does.

What you *can* run here, and what CI runs:

```bash
cd examples/cloud-gcp/terraform
terraform fmt -check -diff .
python3 -m unittest discover -s ../../../tests -k cloud_manifests
```

The deployment itself, on your own project:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT
terraform init
terraform plan -var project_id=YOUR_PROJECT -var gateway_image=REGION-docker.pkg.dev/YOUR_PROJECT/hermes/gateway@sha256:DIGEST
```

Resolve a tag to the digest you should actually pin:

```bash
gcloud artifacts docker images describe REGION-docker.pkg.dev/PROJECT/hermes/gateway:latest --format='value(image_summary.digest)'
```

On GKE instead of Cloud Run:

```bash
gcloud container clusters get-credentials CLUSTER --region REGION
kubectl create namespace hermes
kubectl apply -f examples/cloud-gcp/k8s/gateway.yaml
kubectl apply -f examples/cloud-gcp/k8s/networkpolicy.yaml
kubectl rollout status statefulset/hermes-gateway -n hermes
```

Confirm the egress policy is actually enforced rather than merely present:

```bash
kubectl exec -n hermes statefulset/hermes-gateway -- curl -sS --max-time 5 https://example.com
```

## Common pitfalls

- **Trusting this chapter's commands as verified.** They are not, and the header says so.
  Check them against the provider's current reference.
- **Scaling a gateway to zero.** It drops platform connections and in-flight turns, and the
  symptom is intermittent, not obvious.
- **Leaving `cpu_idle` at its default.** Turns stall between tool calls and it looks like a
  slow model. You will blame the provider first.
- **A tight startup probe.** The gateway restarts mid-reconnect, forever, and the logs look
  like a crash loop with no crash.
- **Using the default compute service account.** Over-privileged by design; the most common
  finding in any GCP review.
- **Downloading a service-account key.** A credential the platform cannot rotate, which
  outlives the person who made it. Use Workload Identity.
- **Putting a secret value in Terraform.** It is in the state file, which is in a bucket.
- **A NetworkPolicy on a cluster with no enforcing CNI.** Applies cleanly, does nothing, and
  you believe you have egress control.
- **Deploying by tag.** Not reproducible, and your rollback is a hope.
- **A database with a public IP because it was easier during setup.** It will still be there
  in a year.
- **Choosing GKE because it looks more serious.** Read the two files side by side first.

## Exercises

Work through `exercises/ex13b-cloud-deployment.md`. Verification: a `terraform plan` on your
own project, the four gateway-specific settings explained, a digest-pinned deploy, an egress
policy proven to be *enforced* rather than merely applied, and a cost estimate before
anything runs.

### Senior interview probes

1. You are deploying a long-lived agent to Cloud Run. Which defaults are wrong for it, and
   what is the symptom of each if you leave them?
2. Cloud Run or GKE for a single gateway? Defend the choice, then argue the other side.
3. Why should a secret value never appear in Terraform, and where does it go instead?
4. What is wrong with a downloaded service-account key, and what replaces it?
5. Your NetworkPolicy is applied and traffic still reaches the internet. What do you check?
6. Explain why pinning a container by tag is a rollback problem and not a style preference.
7. Your vector database is on Cloud SQL and your agent is on Cloud Run. Walk through the
   network path and the identity that makes the connection.
8. How would you check a cloud deployment in CI when CI has no cloud credentials? What can
   you actually assert?
