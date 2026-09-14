# `examples/cloud-gcp/` — the gateway on GCP

Chapter 13b. **Not applied by this repo**: no GCP project, no Terraform registry access, no
Kubernetes cluster. These are reviewed designs, not tested deployments.

```
terraform/main.tf        Cloud Run + Cloud SQL (pgvector) + Secret Manager + a VPC
k8s/gateway.yaml         the GKE alternative: StatefulSet, Service, PDB, ServiceAccount
k8s/networkpolicy.yaml   default-deny egress
```

## What is actually checked

```bash
terraform fmt -check -diff terraform/
python3 -m unittest discover -s ../../tests -k cloud_manifests
```

The tests check the **decisions**, not the schemas — which turned out to be the more useful
half. A manifest can be perfectly valid and still pin an image by tag, run as root, and cap
CPU on an agent loop. Those are what a reviewer catches, so those are what the tests catch:
digest pinning · no CPU limit but a memory limit · non-root with a read-only root *and* a
writable `/tmp` · a PDB on a single replica · DNS in the egress policy · no secret values in
HCL · a private database · no `roles/editor`.

`kubectl apply --dry-run=client` is deliberately **not** used: it contacts a cluster to fetch
the OpenAPI schema, so "client dry-run" is not an offline check.

## The four settings that make it a gateway and not a web service

| | Why |
|---|---|
| `min_instance_count = 1` | Scale-to-zero drops platform connections and in-flight turns. |
| `cpu_idle = false` | The loop idles between tool calls; throttled CPU stalls a turn and looks like a slow model. |
| `StatefulSet` not `Deployment` | Session store and stable identity; orderly restart. |
| generous `startupProbe` | It reconnects to every platform on boot. A tight probe restarts it mid-reconnect, forever. |

## Two things that fail silently

- **A NetworkPolicy on a cluster with no enforcing CNI** applies cleanly and does nothing.
  You will believe you have egress control. On GKE you need Dataplane V2 or Calico; test it
  from inside the pod, not from the manifest.
- **A secret value in Terraform** ends up in the state file, which ends up in a bucket. The
  configuration here creates the secret *container* and never its value.
