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
exactly this instance. AlloyDB is the alternative when you want ScaNN indexing (the
`alloydb_scann` extension); the schema does not change, and the threshold at which the
switch is worth making is a measurement, not a preference — see observation 4 below.

Two settings are deliberate: `ipv4_enabled = false` (a database reachable from the internet
is a finding, not a convenience) and `deletion_protection = true` (destroying the vector
store should require a decision, not a typo).

And one thing is easy to leave out, which is why the file calls it out and a test now pins
it: **`private_network` alone does not give you a private IP.** Cloud SQL does not run in
your VPC — it runs in a Google-managed VPC *peered* with yours, so you must reserve an
address range (`google_compute_global_address`) and establish the peering
(`google_service_networking_connection`) before the instance has anywhere to get an address
from. Leave either out and `apply` fails at create time. That shape — *the managed service
is not where you think it is, and the thing you must build is the path to it* — is most of
cloud networking.

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

### Google's AI stack, and which layer you are building at

> **Snapshot: 2026-09-14.** This is the most perishable section in the course. Google's AI
> product names and boundaries change faster than anything else here — things get renamed,
> merged and retired between releases. **Verify every product name against current
> documentation before you rely on it**, and read the table for its *columns*, which are
> stable, rather than its middle column, which is not. This is not a hypothetical warning:
> the first draft of this section was written with the names of twelve months ago, and
> external verification (`docs/research/google/ai-stack-2026-09-14.md`) found that **almost
> every name in the middle column had changed** — and that one of the five claims below had
> become flatly wrong and another overstated. Both corrections are left visible below
> rather than edited away, because how a claim went stale is the more useful lesson.

Deploying a Hermes gateway to GCP raises a question a GCP-shop interviewer will ask
directly, and the course has so far given you no answer to it:

> *"Why did you build an agent instead of using Google's managed one?"*

"I wanted to learn" is a true answer and a losing one. The real answer is a layer decision,
and it is the same decision on AWS or Azure with different nouns:

| Layer | You provide | Google's offering (2026-09) | Right when | What you give up |
|---|---|---|---|---|
| **Model API** | everything — the loop, tools, state | Gemini API, via **Google AI Studio** (an API key) or the **Gemini Enterprise Agent Platform** (formerly Vertex AI) | you need control of the loop (Chapter 01) | nothing; you own all of it |
| **Open weights** | serving too | **Gemma** (current generation: Gemma 3) | data cannot leave, or cost at volume demands it | managed scaling and the newest frontier capability |
| **Agent framework** | the application, not the plumbing | **ADK** (Agent Development Kit) — Python, TypeScript, Go, Java | you want a loop you did not write but still control | the framework's opinions become yours |
| **Managed agent** | prompts, data, configuration | **Gemini Enterprise Agent Platform** (which absorbed Vertex AI Agent Builder) | a first version has to exist next week | the loop itself, and any behaviour the platform exposes no knob for |
| **Managed retrieval** | documents | **Agent Search** (formerly Vertex AI Search); **RAG Engine** for a pipeline you configure rather than build | retrieval is not your differentiator | the last increment of chunking and ranking control (Chapters 03b, 03c) |
| **Vector index** | embeddings and the schema | **Vector Search** (formerly Matching Engine), **AlloyDB AI** (`alloydb_scann`), Cloud SQL + pgvector, **BigQuery** vector search | you own the pipeline, not the ANN implementation | little — this layer is genuinely commoditised |
| **Evaluation** | the task set and rubric | **Gen AI evaluation service** (Agent Platform → Optimize → Evaluation) | you want managed scoring | less than this course used to claim — see observation 2 |

Five observations that outlive the names in that middle column:

**1. There are two ways to reach Gemini, and the difference is governance, not endpoints.**
An AI Studio key is a key: fast, personal, and it does not belong in production. The Cloud
path uses IAM, service accounts, VPC Service Controls, audit logs and per-project data
handling. Teams prototype with the first and ship with the second — and the migration is
the moment someone discovers the data-governance terms differ *by tier*: free-tier AI
Studio content may be used to improve Google's products and may be read by human reviewers,
while the paid API and the Cloud platform carry an explicit no-training commitment. (Users
in the EEA, Switzerland and the UK get the paid terms on every tier.) Read both before you
choose, not after — and note that reaching *zero* retention is a further step still,
requiring the input/output cache to be disabled and an abuse-monitoring exception filed.

**2. The managed-agent trade is the loop, not the evaluation — and this section said the
opposite until it was checked.** The original claim here was that a managed agent costs you
a frozen task set, a regression gate and trajectory-level visibility. That is now false.
The Gen AI evaluation service ships six trajectory metrics — `trajectory_exact_match`,
`trajectory_in_order_match`, `trajectory_any_order_match`, `trajectory_precision`,
`trajectory_recall`, `trajectory_single_tool_use` — and the platform adds offline
evaluation sets, continuous evaluation with configurable quality alerts (that is a
regression gate), failure-cluster analysis and Cloud Trace tracing. All three things the
claim said you lose are natively available.

What you actually give up is narrower and more durable: **the loop**. You cannot change
what the platform does not expose, and the set of exposed knobs is the vendor's decision,
not yours. Chapter 14 is still the chapter that matters, but for a different reason than
stated — not because the managed option has no evals, but because *you* have to own the
task set and the thresholds regardless of who computes the metrics. A vendor's default
metric is not your acceptance criterion.

Keep the correction visible rather than quietly fixing the sentence: being confidently
wrong about a competitor's capabilities is a specific way engineers lose credibility in
design reviews, and the fix is always the same — check before you claim, and date the
check.

**3. Managed retrieval is the right default for longer than you think.** Agent Search
supports hybrid semantic-plus-keyword search and configurable answer generation, including
abstention-style controls for adversarial and non-summary-seeking queries; RAG Engine
exposes chunking configuration, layout and LLM parsers, and a dedicated reranking step. So
the honest line is not "managed retrieval cannot chunk or rank" — it can, and it is
configurable. The line is further out: when you need a chunking strategy or an abstention
rule that is *specific to your corpus* (Chapter 03b), you are building it anyway, and you
will build it better for having measured the managed one first. Measure before you build
remains right; "it gives you no control" was overstated.

**4. The vector-index layer is commoditised, so pick by where your data already lives.**
pgvector on Cloud SQL if you have PostgreSQL. BigQuery vector search if the corpus is
already in BigQuery. A dedicated service when scale genuinely demands it. Moving data to a
vector database it did not need to live in is the expensive mistake.

The nuance is the one Chapter 03c's recall benchmark predicts: "commoditised" describes the
*interface*, not the performance. Google's own numbers put AlloyDB's ScaNN index at 431 ms
where pgvector HNSW takes over 4 s once the index no longer fits in memory, with roughly a
quarter of the memory footprint and up to 60× lower index-build cost at a billion vectors.
Read that as a threshold rather than a verdict: below the memory line the choice barely
matters, above it the index implementation is the whole latency budget. Know which side of
that line your corpus sits on — which means measuring it, not guessing.

**5. A2A and MCP are not competitors, and neither is a Google product.** **Agent2Agent**
addresses agents talking to *other agents* (Chapter 09's peers); **MCP** addresses agents
talking to *tools* (Chapter 11). A system can use both, and Google's own stack does: ADK
takes MCP servers, the Gemini SDK reaches them through function calling, and the platform
offers managed MCP servers. Governance is worth getting right in an interview, because it
is a fact people state wrongly: Google announced A2A and then donated it, and both A2A and
MCP are now hosted under the Linux Foundation's **Agentic AI Foundation**. Neither protocol
is owned by the vendor whose name you associate with it — MCP came from Anthropic, A2A from
Google, and both are now governed elsewhere. A candidate who treats them as rivals, or who
calls either one a vendor's proprietary protocol, has read headlines rather than
specifications.

**Where Hermes sits.** It is the first row and part of the third: your own loop, your own
tools, any provider — with a gateway, a scheduler and a skill system on top. Using Gemini
on Agent Platform as the *provider* underneath it (Chapter 02's routing) is a normal
configuration, and it is the combination this chapter's Terraform assumes: Google's
infrastructure and models, somebody else's agent runtime. That is a legitimate architecture
and you should be able to say why you chose it.

**Evidence:** `docs/research/google/ai-stack-2026-09-14.md` — the verbatim external
verification behind every name and every claim above, with source URLs. It is dated
research, not a command transcript, which is exactly why this chapter carries `Reviewed:`
and not `Verified:`.

### What is actually checked, and what is not

This is the part that makes the header honest rather than an excuse.

| Checked in CI | How |
|---|---|
| Terraform syntax and layout | `terraform fmt -check` |
| Manifests parse; every object has kind and name | `tests/test_cloud_manifests.py` |
| The *decisions* above | the same tests: digest pinning, no CPU limit, non-root, read-only root with a writable `/tmp`, PDB on a single replica, DNS in the egress policy, no secret values in HCL, private database, no `roles/editor` |
| **Not checked** | that any of it deploys. No `terraform init`, `plan` or `apply`; no cluster. |
| **Not checked by CI** | every product name in "Google's AI stack" above. No test can tell you Google renamed something last week. What exists instead is dated external research (`docs/research/google/ai-stack-2026-09-14.md`) with source URLs — weaker than a test, stronger than a memory, and the reason that section carries its own warning. |

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
- **Setting `private_network` and stopping there.** Without the reserved range and the
  service-networking peering, `apply` fails at create — and under deadline pressure the
  fastest-looking fix is to turn the public IP back on, which is how the pitfall above gets
  created.
- **Quoting a managed product's limitations from memory.** Vendors ship features; a
  capability you claimed was missing eighteen months ago may have shipped last quarter, and
  being wrong about it in a design review is expensive. Date your check.
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
9. Your company runs on GCP. Why did you build an agent instead of using the managed one?
   Answer without saying "I wanted to learn" — and name three things the managed platform
   *does* give you, because an answer that only lists its weaknesses tells the interviewer
   you have not looked at it recently.
10. What is the difference between reaching Gemini through an AI Studio key and through
    Google Cloud, and at what point in a project does that difference start to matter?
11. When is managed retrieval the right answer, and what specifically would make you replace
    it with your own pipeline?
12. A2A or MCP? Describe a system that needs both, and say who governs each.
13. A design doc you wrote last year says a managed service cannot do X. How would you find
    out whether that is still true, and what would you change if it is not?
