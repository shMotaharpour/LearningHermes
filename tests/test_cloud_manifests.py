"""Tests for examples/cloud-gcp/ — Chapter 13b.

This chapter carries the weaker `Reviewed:` header because no GCP project, Terraform
registry or Kubernetes cluster is available here. These tests are the "how it IS checked"
half of that header: they cannot prove the deployment works, but they can prove the
DECISIONS the chapter teaches are actually present in the files.

That turns out to be more useful than schema validation. A manifest can be perfectly valid
and still pin an image by tag, run as root, or cap CPU on an agent loop. These tests check
the things a reviewer would.

Note what is NOT claimed: nothing here contacts GCP, and a passing run says nothing about
whether `terraform apply` would succeed.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

CLOUD = Path(__file__).resolve().parents[1] / "examples" / "cloud-gcp"
TERRAFORM = CLOUD / "terraform" / "main.tf"
K8S = CLOUD / "k8s"

try:
    import yaml
    HAVE_YAML = True
except ImportError:  # pragma: no cover
    HAVE_YAML = False


def load_all(path: Path) -> list[dict]:
    return [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8")) if d]


@unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
class ManifestParseTests(unittest.TestCase):
    def test_every_manifest_parses_and_has_kind_and_name(self):
        for path in sorted(K8S.glob("*.yaml")):
            for doc in load_all(path):
                self.assertIn("apiVersion", doc, path.name)
                self.assertIn("kind", doc, path.name)
                self.assertIn("name", doc.get("metadata", {}), path.name)


@unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
class GatewayWorkloadTests(unittest.TestCase):
    def setUp(self):
        self.docs = load_all(K8S / "gateway.yaml")
        self.by_kind = {d["kind"]: d for d in self.docs}
        self.workload = self.by_kind["StatefulSet"]
        self.container = self.workload["spec"]["template"]["spec"]["containers"][0]

    def test_it_is_a_statefulset_not_a_deployment(self):
        """The gateway holds platform connections and a session store."""
        self.assertIn("StatefulSet", self.by_kind)
        self.assertNotIn("Deployment", self.by_kind)

    def test_image_is_pinned_by_digest(self):
        """A tag is a moving pointer, and 'it worked yesterday' is not a rollback plan."""
        self.assertRegex(self.container["image"], r"@sha256:")

    def test_memory_is_limited_but_cpu_is_not(self):
        """A throttled agent loop looks like a slow model; a leak should kill the pod."""
        limits = self.container["resources"]["limits"]
        self.assertIn("memory", limits)
        self.assertNotIn("cpu", limits)
        self.assertIn("cpu", self.container["resources"]["requests"])

    def test_runs_unprivileged_with_a_read_only_root(self):
        pod = self.workload["spec"]["template"]["spec"]
        self.assertTrue(pod["securityContext"]["runAsNonRoot"])
        sec = self.container["securityContext"]
        self.assertFalse(sec["allowPrivilegeEscalation"])
        self.assertTrue(sec["readOnlyRootFilesystem"])
        self.assertEqual(sec["capabilities"]["drop"], ["ALL"])

    def test_a_read_only_root_needs_writable_mounts(self):
        """readOnlyRootFilesystem without a writable /tmp is a container that crashes."""
        mounts = {m["mountPath"] for m in self.container["volumeMounts"]}
        self.assertIn("/tmp", mounts)

    def test_startup_probe_is_more_patient_than_the_liveness_probe(self):
        """A gateway reconnects to every platform on boot. A tight probe restarts it
        mid-reconnect, forever."""
        startup = self.container["startupProbe"]
        budget = startup["periodSeconds"] * startup["failureThreshold"]
        self.assertGreaterEqual(budget, 60)
        self.assertGreater(budget, self.container["livenessProbe"]["periodSeconds"])

    def test_state_is_persistent(self):
        claims = self.workload["spec"]["volumeClaimTemplates"]
        self.assertTrue(any(c["metadata"]["name"] == "state" for c in claims))

    def test_termination_grace_allows_in_flight_turns_to_finish(self):
        self.assertGreaterEqual(
            self.workload["spec"]["template"]["spec"]["terminationGracePeriodSeconds"], 30)

    def test_workload_identity_rather_than_a_key_file(self):
        """A downloaded service-account JSON outlives whoever created it."""
        sa = self.by_kind["ServiceAccount"]
        self.assertIn("iam.gke.io/gcp-service-account", sa["metadata"]["annotations"])

    def test_a_single_replica_service_has_a_disruption_budget(self):
        """A node upgrade should not silently take your only gateway down."""
        pdb = self.by_kind["PodDisruptionBudget"]
        self.assertEqual(pdb["spec"]["minAvailable"], 1)


@unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
class EgressPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_all(K8S / "networkpolicy.yaml")[0]

    def test_it_restricts_egress(self):
        self.assertEqual(self.policy["spec"]["policyTypes"], ["Egress"])

    def test_dns_is_allowed_or_nothing_resolves(self):
        """Forget this and every failure looks like a network outage."""
        ports = [p for rule in self.policy["spec"]["egress"]
                 for p in rule.get("ports", [])]
        self.assertTrue(any(p["port"] == 53 for p in ports))

    def test_general_internet_access_goes_through_a_proxy(self):
        """Chapter 15's egress lesson, enforced by the platform not by the agent."""
        selectors = [rule.get("to", []) for rule in self.policy["spec"]["egress"]]
        flat = [t for group in selectors for t in group]
        self.assertTrue(any(
            t.get("podSelector", {}).get("matchLabels", {}).get("app") == "egress-proxy"
            for t in flat))

    def test_the_file_warns_that_it_is_inert_without_an_enforcing_cni(self):
        """The most dangerous failure here: it applies cleanly and does nothing."""
        text = (K8S / "networkpolicy.yaml").read_text(encoding="utf-8")
        self.assertIn("does NOTHING", text)


class TerraformTests(unittest.TestCase):
    """Text assertions: there is no HCL parser in the standard library, and the decisions
    worth checking are all greppable."""

    def setUp(self):
        self.text = TERRAFORM.read_text(encoding="utf-8")

    def test_it_states_that_this_repo_does_not_apply_it(self):
        self.assertIn("NOT APPLIED BY THIS REPO", self.text)

    def test_no_secret_value_is_in_the_configuration(self):
        """State is not a vault: a value in a variable ends up in a bucket someone reads."""
        for pattern in (r'api_key\s*=\s*"[^"$]', r'password\s*=\s*"[^"$]',
                        r'secret_data\s*=\s*"[^"$]'):
            self.assertNotRegex(self.text, pattern)

    def test_the_database_is_not_reachable_from_the_internet(self):
        self.assertRegex(self.text, r"ipv4_enabled\s*=\s*false")
        self.assertIn("private_network", self.text)

    def test_the_vector_store_has_deletion_protection_and_backups(self):
        self.assertRegex(self.text, r"deletion_protection\s*=\s*true")
        self.assertRegex(self.text, r"point_in_time_recovery_enabled\s*=\s*true")

    def test_the_gateway_does_not_scale_to_zero(self):
        """Scaling to zero drops platform connections and in-flight turns."""
        match = re.search(r"min_instance_count\s*=\s*(\d+)", self.text)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)), 1)

    def test_cpu_stays_allocated_between_requests(self):
        """cpu_idle = true stalls a turn whenever the container is idle between tool calls."""
        self.assertRegex(self.text, r"cpu_idle\s*=\s*false")

    def test_it_uses_a_dedicated_service_account(self):
        """The default compute service account is over-privileged by design."""
        self.assertIn("google_service_account", self.text)
        self.assertNotIn("roles/editor", self.text)
        self.assertNotIn("roles/owner", self.text)

    def test_it_checks_its_own_image_pin(self):
        self.assertIn("image_is_digest_pinned", self.text)
        self.assertRegex(self.text, r"sha256:\[0-9a-f\]\{64\}")

    @unittest.skipUnless(shutil.which("terraform"), "terraform not installed")
    def test_terraform_fmt_is_clean(self):
        result = subprocess.run(
            ["terraform", "fmt", "-check", "-recursive", str(TERRAFORM.parent)],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
