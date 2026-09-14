"""Tests for examples/model-adaptation/ — Chapter 03d.

Offline, deterministic, seconds-fast. What is pinned here is the CONTRACT the
chapter teaches from, not the specific numbers: which parameters move under
each training mode, what the low-rank constraint can and cannot express, and
the direction of every effect the demo claims (drift grows with rank and is
worst for full fine-tuning). Exact mse values are asserted loosely — tightly
enough to catch a broken optimizer, loosely enough that refactoring the loop's
operation order does not rewrite the tests.
"""
import importlib.util
import json
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LORA_DIR = REPO / "examples" / "model-adaptation"
LORA = LORA_DIR / "lora.py"

_spec = importlib.util.spec_from_file_location("lora", LORA)
assert _spec is not None and _spec.loader is not None, f"cannot load {LORA}"
lora = importlib.util.module_from_spec(_spec)
sys.modules["lora"] = lora
_spec.loader.exec_module(lora)


def make_task(**overrides):
    """The demo defaults, pinned here on purpose: if someone retunes the module's
    defaults, these tests keep judging the numbers the README documents."""
    kwargs = dict(seed=0, noise=0.5, train_samples=48, sigma=1.0)
    kwargs.update(overrides)
    return lora.build_task(**kwargs)


class MatrixTests(unittest.TestCase):
    def test_matmul_shapes_and_values(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        self.assertEqual(lora.matmul(a, b), [[19.0, 22.0], [43.0, 50.0]])
        self.assertEqual(lora.matmul(a, [[1.0], [0.0]]), [[1.0], [3.0]])

    def test_transpose_twice_is_identity(self):
        m = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        self.assertEqual(lora.transpose(lora.transpose(m)), m)


class LinearTests(unittest.TestCase):
    def test_forward_is_the_matrix_product(self):
        model = lora.Linear(dims=2, outputs=2, W=[[1.0, 0.0], [0.0, 2.0]])
        self.assertEqual(model.forward([3.0, 4.0]), [3.0, 8.0])

    def test_copy_is_independent(self):
        model = lora.Linear(2, 1, [[1.0, 2.0]])
        clone = model.copy()
        clone.W[0][0] = 99.0
        self.assertEqual(model.W[0][0], 1.0)

    def test_quantization_error_shrinks_as_bits_grow(self):
        rng = random.Random(0)
        W = [[rng.gauss(0.0, 1.0) for _ in range(8)] for _ in range(4)]
        worst = None
        for bits in (2, 3, 5, 9):
            q, _ = lora.quantize_matrix(W, bits)
            err = math.sqrt(sum((a - b) ** 2 for ra, rb in zip(W, q)
                                for a, b in zip(ra, rb)))
            if worst is not None:
                self.assertLess(err, worst)
            worst = err

    def test_quantization_needs_at_least_two_bits(self):
        with self.assertRaises(ValueError):
            lora.quantize_matrix([[1.0]], 1)


class AdapterTests(unittest.TestCase):
    def test_parameter_count_is_rank_times_dims_plus_outputs(self):
        adapter = lora.LoRAAdapter.init(random.Random(0), dims=12, outputs=6, rank=2)
        self.assertEqual(adapter.param_count(), 2 * 12 + 6 * 2)

    def test_zero_adapter_leaves_the_base_bit_identical(self):
        """rank=0 means no edit at all: B@A is the zero matrix by shape, and the
        model's forward must agree with the bare base exactly."""
        adapter = lora.LoRAAdapter.init(random.Random(0), dims=4, outputs=3, rank=0)
        self.assertEqual(adapter.param_count(), 0)
        self.assertEqual(adapter.delta(), [[0.0] * 4 for _ in range(3)])
        model = lora.LoRAModel(lora.Linear(4, 3, [[1.0] * 4] * 3), adapter)
        self.assertEqual(model.forward([1.0, 2.0, 3.0, 4.0]), [10.0, 10.0, 10.0])

    def test_init_delta_is_zero_but_gradient_is_not(self):
        """B@A = 0 at init, yet the first update is nonzero: that is why one
        factor starts random. Both-zero would make the adapter never wake up."""
        rng = random.Random(1)
        adapter = lora.LoRAAdapter.init(rng, dims=3, outputs=2, rank=2)
        base = lora.Linear(3, 2, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        xs = [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 0.0]]
        ys = [[0.5, -0.5], [0.5, -0.5], [0.5, -0.5]]
        model = lora.LoRAModel(base, adapter)
        before = [row[:] for row in adapter.A]
        lora.train_adapter(model, xs, ys, lr=0.05, steps=1)
        self.assertNotEqual(adapter.A, before)

    def test_refuses_rank_larger_than_the_matrix_allows(self):
        with self.assertRaises(ValueError):
            lora.LoRAAdapter.init(random.Random(0), dims=4, outputs=3, rank=5)

    def test_merged_equals_unmerged_forward(self):
        """Serving merged vs serving adapter+base must give identical outputs."""
        task = make_task()
        adapter = lora.LoRAAdapter.init(random.Random(3), task.dims, task.outputs, 2)
        model = lora.LoRAModel(task.base.copy(), adapter)
        for x in task.new_eval_x[:5]:
            direct = model.forward(x)
            merged = model.merged().forward(x)
            for a, b in zip(direct, merged):
                self.assertAlmostEqual(a, b, places=12)

    def test_detached_base_is_bit_identical(self):
        task = make_task()
        adapter = lora.LoRAAdapter.init(random.Random(3), task.dims, task.outputs, 2)
        model = lora.LoRAModel(task.base.copy(), adapter)
        model.forward([1.0] * task.dims)  # inference must not touch the base
        self.assertEqual(model.without_adapter().W, task.base.W)


class TrainTests(unittest.TestCase):
    def test_full_training_moves_every_base_weight(self):
        task = make_task()
        model = task.base.copy()
        lora.train_full(model, task.train_x, task.train_y, steps=10)
        moved = sum(1 for row_a, row_b in zip(model.W, task.base.W)
                    for a, b in zip(row_a, row_b) if a != b)
        self.assertEqual(moved, task.dims * task.outputs)

    def test_adapter_training_never_moves_the_base(self):
        """The freeze, pinned where it is enforced: W0 is read every step and
        written never. This is the by-construction guarantee the chapter sells."""
        task = make_task()
        adapter = lora.LoRAAdapter.init(random.Random(0), task.dims, task.outputs, 2)
        model = lora.LoRAModel(task.base.copy(), adapter)
        lora.train_adapter(model, task.train_x, task.train_y, steps=10)
        self.assertEqual(model.base.W, task.base.W)

    def test_training_reduces_loss_on_the_training_data(self):
        task = make_task()
        report = lora.train_full(task.base.copy(), task.train_x, task.train_y, steps=50)
        self.assertLess(report.loss_last, report.loss_first)
        adapter = lora.LoRAAdapter.init(random.Random(0), task.dims, task.outputs, 2)
        model = lora.LoRAModel(task.base.copy(), adapter)
        report = lora.train_adapter(model, task.train_x, task.train_y, steps=50)
        self.assertLess(report.loss_last, report.loss_first)

    def test_adapter_training_needs_an_adapter(self):
        task = make_task()
        with self.assertRaises(ValueError):
            lora.train_adapter(lora.LoRAModel(task.base.copy(), None),
                               task.train_x, task.train_y)

    def test_losses_are_per_component(self):
        """The reported loss is mean squared error per output component: the
        first-step loss equals mse() of the untouched model on the training set.
        A silent normalization change here would silently retune every default
        learning rate in the module."""
        task = make_task()
        model = task.base.copy()
        report = lora.train_full(model, task.train_x, task.train_y, steps=3)
        self.assertAlmostEqual(report.loss_first,
                               lora.mse(task.base, task.train_x, task.train_y),
                               places=9)


class TaskTests(unittest.TestCase):
    def test_task_is_deterministic(self):
        self.assertEqual(lora.build_task(seed=7).train_x, lora.build_task(seed=7).train_x)

    def test_shapes_are_as_declared(self):
        task = make_task()
        self.assertEqual(len(task.train_x), 48)
        self.assertEqual(len(task.new_eval_x), len(task.old_eval_x))
        self.assertEqual(len(task.base.W), task.outputs)
        self.assertEqual(len(task.base.W[0]), task.dims)
        self.assertEqual(len(task.delta_true), task.outputs)
        self.assertEqual(len(task.new_basis), task.domain_dim)

    def test_delta_true_has_exactly_true_rank(self):
        """The rank story is only honest if the task's own edit has the rank it
        claims. Rank of an m x n matrix = number of singular values above
        tolerance; delta_true is B@A with A of rank true_rank, so this is exact."""
        task = make_task()
        self.assertLessEqual(lora.rank(task.delta_true), task.true_rank)

    def test_new_inputs_stay_off_the_old_domain(self):
        """New-only directions are invisible to old inputs and carry the true
        edit: otherwise the task could not be solved without moving old
        behaviour, and the demo's drift attribution would be worthless."""
        task = make_task()
        tol = 1e-9
        for x in task.train_x + task.new_eval_x:
            for row in task.old_basis[task.shared:]:
                self.assertLess(abs(sum(a * b for a, b in zip(row, x))), tol)
        for row in task.delta_true:
            for private_dir in task.old_basis[task.shared:]:
                self.assertLess(abs(sum(a * b for a, b in zip(private_dir, row))), tol)

    def test_base_is_perfect_on_the_old_domain(self):
        """Old labels come from the base, noiselessly: any old-domain error after
        adaptation is drift, not task noise."""
        task = make_task()
        self.assertEqual(lora.mse(task.base, task.old_eval_x, task.old_eval_y), 0.0)

    def test_rejects_impossible_geometry(self):
        with self.assertRaises(ValueError):
            make_task(domain_dim=12)   # no new-only directions left
        with self.assertRaises(ValueError):
            make_task(true_rank=4)     # edit cannot fit in 3 new-only directions


class EffectDirectionTests(unittest.TestCase):
    """The chapter's claims, as inequalities. These are the tests that would
    fail if someone 'fixed' the demo into asserting something untrue."""

    @classmethod
    def setUpClass(cls):
        cls.task = make_task()
        lr, steps = 0.05, 1200
        cls.rows = {r.name: r for r in
                    lora.compare_adaptation(cls.task, seed=0, lr=lr, steps=steps, bits=4)}
        cls.sweep = {r.rank: r for r in
                     lora.rank_sweep(cls.task, [1, 2, 4, 6], seed=0, lr=lr, steps=steps)}
        cls.floor = lora.quantization_floor(cls.task, 4)

    def test_every_training_run_is_fast(self):
        for row in self.rows.values():
            self.assertLess(row.seconds, 5.0)

    def test_full_finetune_fits_the_new_domain(self):
        base, full = self.rows["base (frozen)"], self.rows["full fine-tune"]
        self.assertLess(full.new_eval_mse, 0.1 * base.new_eval_mse)

    def test_full_finetune_drifts_and_lora_does_not(self):
        full = self.rows["full fine-tune"]
        lora_row = self.rows["lora r=2"]
        self.assertGreater(full.old_eval_mse, 0.01)
        self.assertLess(lora_row.old_eval_mse, full.old_eval_mse)

    def test_lora_fits_most_of_the_available_gain(self):
        """Rank 2 on a rank-2 task with an exactly-low-rank invisible edit: LoRA's
        constraint should cost nothing, and its smaller effective capacity should
        beat full fine-tuning's variance on BOTH columns. That is the bet LoRA
        makes; this task is the case where it pays."""
        full, lor = self.rows["full fine-tune"], self.rows["lora r=2"]
        self.assertLess(lor.trainable_params, full.trainable_params)
        self.assertLess(lor.new_eval_mse, full.new_eval_mse)
        self.assertLess(lor.old_eval_mse, full.old_eval_mse)

    def test_rank_1_cannot_express_a_rank_2_edit(self):
        self.assertGreater(self.sweep[1].new_eval_mse, 2.0 * self.sweep[2].new_eval_mse)

    def test_new_domain_error_has_a_minimum_at_the_true_rank(self):
        """The U-curve: rank 2 is the sweet spot, and both neighbours are worse."""
        self.assertLess(self.sweep[2].new_eval_mse, self.sweep[1].new_eval_mse)
        self.assertLess(self.sweep[2].new_eval_mse, self.sweep[4].new_eval_mse)
        self.assertLess(self.sweep[4].new_eval_mse, self.sweep[6].new_eval_mse)

    def test_old_domain_drift_climbs_with_rank(self):
        """The capacity knob turned up is forgetting turned up."""
        old = [self.sweep[r].old_eval_mse for r in (1, 2, 4, 6)]
        self.assertEqual(old, sorted(old))
        self.assertGreater(old[-1], 2.0 * old[0])

    def test_train_mse_drops_below_the_noise_floor(self):
        """train mse falling below noise^2 = 0.25 is the fingerprint of
        memorization: the only way to fit noise is to have capacity for it."""
        self.assertLess(self.sweep[6].train_mse, 0.25)

    def test_quantization_floor_shrinks_with_precision(self):
        """Bits are a different knob: the floor scales with quantization step,
        and rank has no effect on it whatsoever."""
        floor3 = lora.quantization_floor(self.task, 3)
        floor4 = self.floor
        floor6 = lora.quantization_floor(self.task, 6)
        self.assertGreater(floor3.quant_old_eval_mse, floor4.quant_old_eval_mse)
        self.assertGreater(floor4.quant_old_eval_mse, floor6.quant_old_eval_mse)

    def test_qlora_recovers_the_new_domain(self):
        """The QLoRA premise, verified: adapting on a 4-bit base lands close to
        what the float base's adapter achieved on the new domain."""
        q2 = self.rows["qlora r=2 (4-bit base)"]
        lor = self.rows["lora r=2"]
        self.assertLess(q2.new_eval_mse, 1.3 * lor.new_eval_mse)

    def test_more_rank_on_a_quantized_base_helps_nothing(self):
        """QLoRA's rank does not buy back base precision: r=3 on the 4-bit base is
        worse than r=2 on both columns. Precision is a different knob."""
        q2 = self.rows["qlora r=2 (4-bit base)"]
        q3 = self.rows["qlora r=3 (4-bit base)"]
        self.assertGreater(q3.new_eval_mse, q2.new_eval_mse)
        self.assertGreater(q3.old_eval_mse, q2.old_eval_mse)


class CliTests(unittest.TestCase):
    """Black-box runs of the CLI. Defaults take ~7 s; every mode here is
    deliberately throttled or quick-mode so the whole file stays fast."""

    @classmethod
    def setUpClass(cls):
        cls.quick = [sys.executable, str(LORA), "--quick"]

    def run_cli(self, args, expect_json=False):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def test_quick_run_prints_all_three_tables(self):
        proc = self.run_cli(self.quick)
        self.assertIn("head to head:", proc.stdout)
        self.assertIn("rank sweep", proc.stdout)
        self.assertIn("base-precision floor", proc.stdout)

    def test_json_mode_is_parseable_and_complete(self):
        proc = self.run_cli(self.quick + ["--json"])
        data = json.loads(proc.stdout)
        for key in ("comparison", "sweep", "floor", "true_rank", "steps", "seed"):
            self.assertIn(key, data)
        names = [row["name"] for row in data["comparison"]]
        self.assertIn("base (frozen)", names)
        self.assertIn("full fine-tune", names)
        self.assertIn("lora r=2", names)
        self.assertEqual(data["floor"]["bits"], 4)

    def test_ranks_flag_is_honoured(self):
        proc = self.run_cli(self.quick + ["--ranks", "1", "2", "--json"])
        data = json.loads(proc.stdout)
        self.assertEqual([row["rank"] for row in data["sweep"]], [1, 2])

    def test_same_seed_same_output(self):
        """Determinism, black-box: identical stdout byte-for-byte, except the
        wall-clock columns, which are timing and not behaviour."""
        a = json.loads(self.run_cli(self.quick + ["--json"]).stdout)
        b = json.loads(self.run_cli(self.quick + ["--json"]).stdout)
        for report in (a, b):
            for row in report["comparison"]:
                row.pop("seconds", None)
            for row in report["sweep"]:
                row.pop("seconds", None)
        self.assertEqual(a, b)

    def test_default_steps_are_documented_and_not_quick(self):
        """--quick exists so smoke tests can throttle; the defaults must stay
        the full run or the README's numbers stop being reproducible."""
        proc = self.run_cli([sys.executable, str(LORA), "--help"])
        self.assertIn("--steps", proc.stdout)
        data = json.loads(self.run_cli(self.quick + ["--json"]).stdout)
        self.assertEqual(data["steps"], 120)


if __name__ == "__main__":
    unittest.main()
