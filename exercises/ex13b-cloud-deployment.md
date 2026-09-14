# Exercise 13b — Cloud Deployment on GCP

## Objective

Deploy the gateway to infrastructure you do not own the hardware for, and know which of the
platform's defaults you had to change and why.

You need a GCP project with billing enabled. **Everything here costs money** — task 1 is
estimating how much, before you create anything.

Budget: 4–6 hours. Destroy what you create.

## Tasks

1. **Estimate before you build.** Read `examples/cloud-gcp/terraform/main.tf` and price it
   with the GCP pricing calculator: the Cloud Run service at `min_instance_count = 1` with
   `cpu_idle = false`, and the Cloud SQL tier. Write down the monthly figure **before**
   running anything.

   Then answer the question that actually matters: which single line would cut it most, and
   what would that cost you operationally?

2. **Read the two deployments against each other.** `terraform/main.tf` and
   `k8s/gateway.yaml` describe the same service. List what the Kubernetes version has to
   state explicitly that Cloud Run provides for free, then pick one for a team of four and
   defend it in two sentences.

3. **Run what can be run offline.**

   ```bash
   cd examples/cloud-gcp/terraform
   terraform fmt -check -diff .
   python3 -m unittest discover -s ../../../tests -k cloud_manifests
   ```

   Then read `tests/test_cloud_manifests.py` and find the test for
   `test_memory_is_limited_but_cpu_is_not`. Explain, in one sentence, the production symptom
   it exists to prevent.

4. **Plan against your own project.**

   ```bash
   gcloud auth application-default login
   terraform init
   terraform plan -var project_id=YOUR_PROJECT -var gateway_image=...@sha256:...
   ```

   Record anything the plan does that the chapter did not lead you to expect. **This
   chapter is unverified — if a resource argument has changed in the provider, you are the
   one who finds out.** Note what you had to fix; that is the exercise's real output.

5. **Pin by digest, deliberately.** Resolve a tag to a digest with
   `gcloud artifacts docker images describe`, deploy with the digest, then try to deploy
   with the tag and observe `image_digest_pinned` in the outputs. Write down why a CI
   pipeline should fail on that output rather than warn.

6. **Break identity on purpose.** Deploy once using the default compute service account
   instead of the dedicated one. Enumerate what that identity can reach in your project
   (`gcloud projects get-iam-policy`). Then revert. Write down what an attacker who reached
   your gateway would have gained in each case.

7. **Prove the egress policy is enforced, not merely applied.** On GKE, apply
   `networkpolicy.yaml`, then from inside the pod:

   ```bash
   kubectl exec -n hermes statefulset/hermes-gateway -- curl -sS --max-time 5 https://example.com
   ```

   If that succeeds, your CNI is not enforcing policy. Find out which one your cluster runs
   and what it would take to enforce it. **A policy that applies cleanly and does nothing is
   the failure mode this task exists for.**

8. **Wire the data layer to Chapter 03c.** Apply
   `examples/retrieval-scale/schema.sql` to your Cloud SQL instance and run `bench.py`
   against it with `--store pgvector`. Compare the latency numbers to the local sqlite-vec
   run and explain the difference — network, instance size, or index.

9. **Destroy it.** `terraform destroy`. Note what refused to be destroyed and why
   (`deletion_protection`), and whether you agree with that default for a vector store.

10. **Write the runbook.** One page for whoever is on call: how to roll back, how to read
    logs, what to do if the gateway crash-loops, who can stop it, and what it costs per day.

11. **Answer the interview question, then check your own answer.** Write half a page on
    *"why did you build an agent instead of using Google's managed one?"* — as a layer
    decision, naming what you keep and what you give up.

    Then do the part almost nobody does: **open current Google documentation and check the
    product names and capabilities you just relied on.** The chapter's table is a dated
    snapshot and says so; the research behind it is in
    `docs/research/google/ai-stack-2026-09-14.md`, with source URLs. Record every name or
    capability that has changed since that date, and whether any change weakens your
    answer. If the managed option has grown a capability you claimed it lacked, your answer
    is now wrong — rewrite it.

    This is the transferable habit, not a chapter chore. Confidently describing a
    competitor's product as it was eighteen months ago is a common and expensive way to
    lose a design argument, and the only defence is a dated check.

## Verification checklist

- [ ] Monthly cost estimated **before** creating anything, with the biggest single lever
      named and its operational cost stated.
- [ ] Cloud Run and GKE compared from the two files, with a defended choice.
- [ ] Offline checks run; the no-CPU-limit test explained in production terms.
- [ ] `terraform plan` succeeded against your own project, with any drift from this
      (unverified) chapter recorded.
- [ ] A digest-pinned deploy, and a written reason CI should fail rather than warn on a tag.
- [ ] Default-service-account blast radius enumerated and then reverted.
- [ ] Egress policy tested from inside the pod, with the CNI enforcement question answered.
- [ ] `schema.sql` applied to Cloud SQL and `bench.py` run against it, latency difference
      explained.
- [ ] Everything destroyed; `deletion_protection` behaviour noted.
- [ ] A one-page on-call runbook including the daily cost.
- [ ] A written layer-decision answer, plus a dated re-check of the product names it
      depends on and a note of anything that has changed since the chapter's snapshot.
