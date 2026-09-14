#!/usr/bin/env python3
"""LoRA on a linear model: three knobs, and only one of them is rank. Chapter 03d.

A base model arrives pretrained. The task then shifts — a new domain, new label
conventions — and you must change the model's behaviour without losing what it
already knew. This module is the smallest setting where that trade is real: a
linear model `y = W0 @ x`, a new domain whose data lives on a low-dimensional
subspace, and a required edit `delta_W` of known true rank. Three things vary,
and keeping them separate is the whole chapter:

* **Freezing (the by-construction guarantee).** Full fine-tuning moves every
  entry of W0, so when it is done the base model no longer exists — nothing to
  un-learn, nothing to compose, nothing to recover. LoRA freezes W0 and learns
  `delta_W = B @ A`, so the base model is bit-identical after training and the
  edit is a detachable object. That guarantee is about the PARAMETERS, and it
  holds no matter how training goes.
* **Rank (the capacity knob).** The adapter can only express edits of rank <= r.
  Below the true rank of the needed edit it underfits; at the true rank the
  new-domain error bottoms out; above it, spare capacity fits label noise — the
  new domain gets worse again, and fitting noise in directions the old domain
  shares IS forgetting. Forgetting with a visible cause.
* **Base precision (a different knob).** QLoRA quantizes the frozen base and
  adapts on top. The quantization error exists before any adapter and is set
  by BITS, not by rank: in the demo below, more rank on the same quantized
  base made both columns worse, because spare capacity just chased the same
  noise harder. Precision is the knob to turn when the base itself is wrong.

Honesty about what the toy can and cannot show: with plain full-batch gradient
descent on a linear model, BOTH arms stay confined to the span of the training
inputs, so the forgetting mechanism here is concrete and inspectable — edits
along directions the old domain's inputs share, driven partly by label noise
the extra capacity fits. Real LLM forgetting adds nonconvexity, SGD noise, and
optimizer drift in directions the data does not span. The mechanism differs;
the conclusion (capacity you do not need becomes drift you did not ask for)
is the same, and here every number in the demo is computable by hand.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import asdict, dataclass, field

# --- matrices ------------------------------------------------------------------------


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """(m x k) @ (k x n) -> (m x n). Stdlib only; clarity beats speed here."""
    cols = list(zip(*b))
    return [[sum(x * y for x, y in zip(row, col)) for col in cols] for row in a]


def transpose(m: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*m)]


def rank(m: list[list[float]], tol: float = 1e-9) -> int:
    """Rank by Gaussian elimination with partial pivoting. The one matrix fact
    this chapter cannot do without: 'the edit has rank r' has to be checkable."""
    rows = [row[:] for row in m]
    rows_used = 0
    cols = len(m[0]) if m else 0
    for col in range(cols):
        pivot = max(range(rows_used, len(rows)), key=lambda r: abs(rows[r][col]))
        if abs(rows[pivot][col]) <= tol:
            continue
        rows[rows_used], rows[pivot] = rows[pivot], rows[rows_used]
        pv = rows[rows_used][col]
        for r in range(len(rows)):
            if r != rows_used and abs(rows[r][col]) > tol:
                factor = rows[r][col] / pv
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[rows_used])]
        rows_used += 1
        if rows_used == len(rows):
            break
    return rows_used


def mse(model, xs: list[list[float]], ys: list[list[float]]) -> float:
    """Mean squared error per output component over a dataset."""
    if not xs:
        return 0.0
    total = 0.0
    for x, y in zip(xs, ys):
        pred = model.forward(x)
        total += sum((p - t) ** 2 for p, t in zip(pred, y))
    return total / (len(xs) * len(ys[0]))


# --- the model -----------------------------------------------------------------------


@dataclass
class Linear:
    """A plain linear map y = W @ x. W is `outputs x dims` (one row per output).

    This is the entire "model architecture". That is deliberate: LoRA's
    mechanics — which parameters move, which never do — are already fully
    visible here, and nothing about them depends on depth or nonlinearity.
    """

    dims: int
    outputs: int
    W: list[list[float]]

    def forward(self, x: list[float]) -> list[float]:
        return [sum(w * xj for w, xj in zip(row, x)) for row in self.W]

    def predict(self, xs: list[list[float]]) -> list[list[float]]:
        return [self.forward(x) for x in xs]

    def copy(self) -> "Linear":
        return Linear(self.dims, self.outputs, [row[:] for row in self.W])

    def param_count(self) -> int:
        return self.dims * self.outputs


def quantize_matrix(W: list[list[float]], bits: int) -> tuple[list[list[float]], list[float]]:
    """Per-row symmetric quantization to `bits` bits; returns (dequantized, scales).

    Simulated, not packed: each row gets one float scale, entries round to the
    integer grid `[-2^(b-1)+1, 2^(b-1)-1]`, and dequantization multiplies back.
    Real int4 kernels store the packed integers and fuse the multiply — the
    error model here (one rounding per entry against one scale per row) is the
    part that matters for the floor demonstrated below.
    """
    if bits < 2:
        raise ValueError("quantization needs at least 2 bits")
    levels = 2 ** (bits - 1) - 1
    q: list[list[float]] = []
    scales: list[float] = []
    for row in W:
        peak = max(abs(w) for w in row)
        scale = (peak / levels) if peak else 1.0
        scales.append(scale)
        q.append([max(-levels, min(levels, round(w / scale))) * scale for w in row])
    return q, scales


def quantize_linear(model: Linear, bits: int) -> Linear:
    """The QLoRA premise: the frozen base, carried at lower precision."""
    q, _ = quantize_matrix(model.W, bits)
    return Linear(model.dims, model.outputs, q)


@dataclass
class LoRAAdapter:
    """The low-rank edit: delta_W = B @ A, with A (rank x dims), B (outputs x rank).

    Init: A is zeros and B is random. Two reasons, one practical and one that is
    part of this chapter's claim. Practical: if both started at zero, the first
    update to B would be zero (it is scaled by A's output) and the adapter would
    never wake up. Substantive: because A starts at zero and every gradient
    update to A is a multiple of a training input, A's rows live in the span of
    the training data FOREVER — so on any input orthogonal to that span,
    B @ A @ x is exactly zero and the merged model behaves exactly like the
    base. The edit cannot leak into directions the data never showed it. (Real
    LoRA usually inits the other way — A random, B zero — which leaks slightly
    off the data span; see the README's honest limits.)
    """

    rank: int
    A: list[list[float]]
    B: list[list[float]]
    dims: int = 0

    @classmethod
    def init(cls, rng: random.Random, dims: int, outputs: int, rank: int) -> "LoRAAdapter":
        max_rank = min(dims, outputs)
        if not 0 <= rank <= max_rank:
            raise ValueError(f"rank must be in 0..min(dims, outputs)={max_rank}, got {rank}")
        A = [[0.0] * dims for _ in range(rank)]
        B = [[rng.gauss(0.0, 1.0) for _ in range(rank)] for _ in range(outputs)]
        return cls(rank=rank, A=A, B=B, dims=dims)

    def project(self, x: list[float]) -> list[float]:
        return [sum(a * xj for a, xj in zip(row, x)) for row in self.A]

    def combine(self, a: list[float]) -> list[float]:
        return [sum(b * aj for b, aj in zip(row, a)) for row in self.B]

    def delta(self) -> list[list[float]]:
        """The edit as a dense matrix, B @ A. Rank 0 is special-cased because a
        product of two empty factors cannot reveal the output width."""
        if self.rank == 0:
            return [[0.0] * self.dims for _ in self.B]
        return matmul(self.B, self.A)

    def param_count(self) -> int:
        a_params = self.rank * (len(self.A[0]) if self.A else 0)
        return a_params + len(self.B) * self.rank


@dataclass
class LoRAModel:
    """A frozen base plus a detachable low-rank edit. forward(x) = W0 x + B (A x)."""

    base: Linear
    adapter: LoRAAdapter | None = None

    def forward(self, x: list[float]) -> list[float]:
        out = self.base.forward(x)
        if self.adapter is None or self.adapter.rank == 0:
            return out
        delta = self.adapter.combine(self.adapter.project(x))
        return [b + d for b, d in zip(out, delta)]

    def predict(self, xs: list[list[float]]) -> list[list[float]]:
        return [self.forward(x) for x in xs]

    def without_adapter(self) -> Linear:
        """The base model, exactly as it arrived. Not an approximation: bit-identical."""
        return self.base.copy()

    def merged(self) -> Linear:
        """The edit folded into the weights, for serving without adapter overhead."""
        if self.adapter is None or self.adapter.rank == 0:
            return self.base.copy()
        d = self.adapter.delta()
        W = [[w + e for w, e in zip(row, drow)] for row, drow in zip(self.base.W, d)]
        return Linear(self.dims, self.outputs, W)

    @property
    def dims(self) -> int:
        return self.base.dims

    @property
    def outputs(self) -> int:
        return self.base.outputs

    def param_count(self) -> int:
        return self.base.param_count() + (self.adapter.param_count() if self.adapter else 0)


# --- training ------------------------------------------------------------------------


@dataclass
class FitReport:
    """What one training run spent and earned. `mode` is the experimental control:
    "adapter" trains B and A only; "full" trains W. Same optimizer, same data,
    same steps — so any difference in the tables below has exactly one cause."""

    mode: str
    steps: int
    lr: float
    loss_first: float
    loss_last: float
    trainable_params: int
    seconds: float = 0.0


def train_full(model: Linear, xs: list[list[float]], ys: list[list[float]],
               lr: float = 0.05, steps: int = 1200) -> FitReport:
    """Full fine-tuning: gradient descent on EVERY entry of W. This is the arm
    that forgets, and it forgets because nothing constrains the edit's rank."""
    n = len(xs)
    out_n = len(ys[0])
    denom = n * out_n
    loss_first = loss_last = 0.0
    started = time.monotonic()
    for step in range(steps):
        dW = [[0.0] * model.dims for _ in range(model.outputs)]
        loss = 0.0
        for x, y in zip(xs, ys):
            pred = model.forward(x)
            e = [p - t for p, t in zip(pred, y)]
            loss += sum(ei * ei for ei in e)
            for o, eo in enumerate(e):
                g = (2.0 / denom) * eo
                drow = dW[o]
                for j, xj in enumerate(x):
                    drow[j] += g * xj
        if step == 0:
            loss_first = loss / denom
        loss_last = loss / denom
        for row, grow in zip(model.W, dW):
            for j, g in enumerate(grow):
                row[j] -= lr * g
    return FitReport("full", steps, lr, loss_first, loss_last,
                     model.param_count(), time.monotonic() - started)


def train_adapter(model: LoRAModel, xs: list[list[float]], ys: list[list[float]],
                  lr: float = 0.05, steps: int = 1200) -> FitReport:
    """LoRA training: identical optimizer, but the gradient only ever touches
    B and A. W0 is read every step and written never — that is the freeze, and
    it is enforced by this loop's shape, not by a regularizer or a promise."""
    if model.adapter is None or model.adapter.rank == 0:
        raise ValueError("train_adapter needs an adapter with rank >= 1")
    ad = model.adapter
    base = model.base
    n = len(xs)
    out_n = len(ys[0])
    denom = n * out_n
    rank = ad.rank
    dims = base.dims
    outputs = base.outputs
    loss_first = loss_last = 0.0
    started = time.monotonic()
    for step in range(steps):
        dA = [[0.0] * dims for _ in range(rank)]
        dB = [[0.0] * rank for _ in range(outputs)]
        loss = 0.0
        for x, y in zip(xs, ys):
            base_out = base.forward(x)
            a = ad.project(x)
            pred = [b + d for b, d in zip(base_out, ad.combine(a))]
            e = [p - t for p, t in zip(pred, y)]
            loss += sum(ei * ei for ei in e)
            for o, eo in enumerate(e):
                g = (2.0 / denom) * eo
                drow = dB[o]
                for j, aj in enumerate(a):
                    drow[j] += g * aj
            for j in range(rank):
                bte = (2.0 / denom) * sum(ad.B[o][j] * e[o] for o in range(outputs))
                drow = dA[j]
                for i, xi in enumerate(x):
                    drow[i] += bte * xi
        if step == 0:
            loss_first = loss / denom
        loss_last = loss / denom
        for row, grow in zip(ad.A, dA):
            for j, g in enumerate(grow):
                row[j] -= lr * g
        for row, grow in zip(ad.B, dB):
            for j, g in enumerate(grow):
                row[j] -= lr * g
    return FitReport("adapter", steps, lr, loss_first, loss_last,
                     ad.param_count(), time.monotonic() - started)


# --- the task: a pretrained base, a shifted domain, a rank-2 edit ---------------------


def _orthonormal_rows(rng: random.Random, k: int, d: int) -> list[list[float]]:
    """k orthonormal rows in R^d via Gram-Schmidt. Deterministic given rng."""
    rows: list[list[float]] = []
    for _ in range(k):
        v = [rng.gauss(0.0, 1.0) for _ in range(d)]
        for u in rows:
            p = sum(a * b for a, b in zip(u, v))
            v = [a - p * b for a, b in zip(v, u)]
        norm = math.sqrt(sum(a * a for a in v))
        rows.append([a / norm for a in v])
    return rows


@dataclass
class TaskData:
    """The synthetic world, with nothing hidden — including the geometry that makes
    clean adaptation possible at all.

    Three input regions, built from one random orthonormal frame:

    * ``new_only`` directions — used by the new domain, never by the old one. The
      true edit ``delta_true`` lives entirely here, so a model that learned it
      PERFECTLY would be invisible on the old domain. That is the best case, and
      it is why the demo's residual drift is attributable to training, not to
      the task being impossible.
    * ``shared`` directions — used by both domains. Label noise on the new data
      can only be fit inside the new domain's span, and this is the part of that
      span the old domain also occupies: fitting noise here IS forgetting. This
      is where every old-domain mse in the demo comes from.
    * ``old_only`` directions — used by the old domain alone. Gradients never
      point here (no new-domain data lives here), so no training arm moves
      behaviour here at all.

    The base model W0 plays the pretrained model: you get its weights, the way
    you always get a base model, without its training run. Old-domain labels are
    noiseless and come from W0, so the base model's old-domain error is exactly
    zero and ANY old-domain error after adaptation is drift you can attribute.
    New-domain labels carry noise, because few-shot adaptation data always
    does — and that noise is what excess capacity spends itself on.
    """

    dims: int
    outputs: int
    domain_dim: int
    new_only: int
    shared: int
    true_rank: int
    noise: float
    base: Linear
    delta_true: list[list[float]]
    new_basis: list[list[float]]         # domain_dim x dims, orthonormal rows
    old_basis: list[list[float]]         # domain_dim x dims, orthonormal rows
    train_x: list[list[float]]
    train_y: list[list[float]]
    new_eval_x: list[list[float]]
    new_eval_y: list[list[float]]
    old_eval_x: list[list[float]]
    old_eval_y: list[list[float]]


def build_task(seed: int = 0, dims: int = 12, outputs: int = 6, domain_dim: int = 9,
               true_rank: int = 2, noise: float = 0.5, train_samples: int = 48,
               eval_samples: int = 64, base_std: float = 1.0,
               sigma: float = 1.0) -> TaskData:
    """Build the world. The defaults are the tuned demo setting: with them the
    head-to-head and the sweep both show the pattern the chapter claims (see the
    README for the numbers). The extra knobs exist so the task itself can be
    swept — a teaching module whose world is fixed is a module students cannot
    experiment on.

    Geometry: the frame is one random orthonormal basis of R^dims. The new domain
    uses the first ``domain_dim`` directions; the old domain uses the last
    ``domain_dim``; the overlap (``2*domain_dim - dims`` directions, when
    positive) is the shared region where noise-fitting becomes forgetting. The
    true edit is placed entirely in the first ``new_only = dims - domain_dim``
    directions, which the old domain never sees — so the task admits a perfect,
    invisible edit, and every old-domain error the demo measures is training
    drift, not task geometry. That placement requires ``true_rank <= new_only``;
    if the edit needed shared directions, old behaviour would move no matter
    what was frozen, which is a different (and worth knowing) failure mode.
    """
    new_only = dims - domain_dim
    shared = domain_dim - new_only
    if new_only <= 0:
        raise ValueError("domain_dim must be a strict subset of dims")
    if not true_rank <= new_only:
        raise ValueError(f"true_rank must fit in the {new_only} new-only directions, "
                         f"or no invisible edit exists; got {true_rank}")
    if true_rank > outputs:
        raise ValueError("true_rank cannot exceed the number of outputs")
    rng = random.Random(seed)
    frame = _orthonormal_rows(rng, dims, dims)
    new_basis = frame[:domain_dim]            # new_only private + shared
    old_basis = frame[new_only:]              # shared + old_only private

    base = Linear(dims, outputs,
                  [[rng.gauss(0.0, base_std / math.sqrt(dims)) for _ in range(dims)]
                   for _ in range(outputs)])
    # The true edit: rank `true_rank`, its row space INSIDE the new-only
    # directions of the frame, so W1 = W0 + delta_true differs from W0 only
    # where the old domain has no support — a perfect adapter would be
    # invisible on the old domain, and every old-domain error in the demo is
    # training drift, not task geometry.
    a_true = _orthonormal_rows(rng, true_rank, new_only)
    a_rows = matmul([[sigma * v for v in row] for row in a_true],
                    frame[:new_only])
    b_true = [[rng.gauss(0.0, 1.0) for _ in range(true_rank)] for _ in range(outputs)]
    delta_true = matmul(b_true, a_rows)

    def new_input() -> list[float]:
        """A random point of the new domain: coordinates on its slice of the frame."""
        c = [rng.gauss(0.0, 1.0) for _ in range(domain_dim)]
        return [sum(c[k] * new_basis[k][i] for k in range(domain_dim)) for i in range(dims)]

    def old_input() -> list[float]:
        """A random point of the old domain: a different slice of the same frame,
        overlapping the new domain's slice in exactly the shared directions."""
        c = [rng.gauss(0.0, 1.0) for _ in range(domain_dim)]
        return [sum(c[k] * old_basis[k][i] for k in range(domain_dim)) for i in range(dims)]

    def label(model: Linear, x: list[float], noisy: bool) -> list[float]:
        y = model.forward(x)
        if noisy:
            y = [v + rng.gauss(0.0, noise) for v in y]
        return y

    adapted = Linear(dims, outputs,
                     [[w + e for w, e in zip(row, drow)]
                      for row, drow in zip(base.W, delta_true)])

    # Training labels are noisy, because few-shot adaptation data always is. The
    # EVAL sets are NOT: they hold the noiseless expected targets, so the tables
    # measure what a model LEARNED (population risk) rather than how unlucky one
    # noisy draw was. That separation is the point — training against noisy data
    # and being scored against the clean expectation is exactly the situation
    # fine-tuning puts you in, and it is what lets a rank sweep show a sweet
    # spot instead of a floor of eval noise that no rank setting can cross.
    train_x = [new_input() for _ in range(train_samples)]
    train_y = [label(adapted, x, noisy=True) for x in train_x]
    new_eval_x = [new_input() for _ in range(eval_samples)]
    new_eval_y = [label(adapted, x, noisy=False) for x in new_eval_x]
    old_eval_x = [old_input() for _ in range(eval_samples)]
    old_eval_y = [label(base, x, noisy=False) for x in old_eval_x]
    return TaskData(dims, outputs, domain_dim, new_only, shared, true_rank, noise,
                    base, delta_true, new_basis, old_basis, train_x, train_y,
                    new_eval_x, new_eval_y, old_eval_x, old_eval_y)


# --- experiments ---------------------------------------------------------------------


@dataclass
class MethodRow:
    """One line of the head-to-head: what was trained, what it cost, what moved."""

    name: str
    trainable_params: int
    total_params: int
    new_eval_mse: float
    old_eval_mse: float
    seconds: float


@dataclass
class RankRow:
    """One line of the rank sweep: the capacity knob, turned one click at a time."""

    rank: int
    trainable_params: int
    train_mse: float
    new_eval_mse: float
    old_eval_mse: float
    seconds: float


@dataclass
class FloorReport:
    """Base-precision floor: the quantization error itself, measured on both domains.
    An adapter can cancel the low-rank slice of this error on the domain span and
    nothing more; the rest is set by `bits`, not by rank."""

    bits: int
    quant_new_eval_mse: float
    quant_old_eval_mse: float


@dataclass
class ExperimentReport:
    """Everything one run of the demo computed, in a shape --json can emit directly."""

    seed: int
    steps: int
    lr: float
    dims: int
    outputs: int
    domain_dim: int
    true_rank: int
    noise: float
    bits: int
    comparison: list[MethodRow] = field(default_factory=list)
    sweep: list[RankRow] = field(default_factory=list)
    floor: FloorReport | None = None


def evaluate(model, task: TaskData) -> tuple[float, float]:
    """(new-domain mse, old-domain mse) for any model with a forward()."""
    return mse(model, task.new_eval_x, task.new_eval_y), \
        mse(model, task.old_eval_x, task.old_eval_y)


def compare_adaptation(task: TaskData, *, seed: int = 0, lr: float = 0.05,
                       steps: int = 1200, lora_rank: int = 2, bits: int = 4,
                       qlora_ranks: tuple[int, ...] = (2, 3)) -> list[MethodRow]:
    """Base vs full fine-tune vs LoRA vs QLoRA, everything else held fixed."""
    rows: list[MethodRow] = []

    new_mse, old_mse = evaluate(task.base, task)
    rows.append(MethodRow("base (frozen)", 0, task.base.param_count(),
                          new_mse, old_mse, 0.0))

    full = task.base.copy()
    report = train_full(full, task.train_x, task.train_y, lr=lr, steps=steps)
    new_mse, old_mse = evaluate(full, task)
    rows.append(MethodRow("full fine-tune", report.trainable_params,
                          task.base.param_count(), new_mse, old_mse, report.seconds))

    adapter = LoRAAdapter.init(random.Random(seed + 1), task.dims, task.outputs, lora_rank)
    lora = LoRAModel(task.base.copy(), adapter)
    report = train_adapter(lora, task.train_x, task.train_y, lr=lr, steps=steps)
    new_mse, old_mse = evaluate(lora, task)
    rows.append(MethodRow(f"lora r={lora_rank}", report.trainable_params,
                          lora.param_count(), new_mse, old_mse, report.seconds))

    qbase = quantize_linear(task.base, bits)
    for rank in qlora_ranks:
        adapter = LoRAAdapter.init(random.Random(seed + 1), task.dims, task.outputs, rank)
        qlora = LoRAModel(qbase.copy(), adapter)
        report = train_adapter(qlora, task.train_x, task.train_y, lr=lr, steps=steps)
        new_mse, old_mse = evaluate(qlora, task)
        rows.append(MethodRow(f"qlora r={rank} ({bits}-bit base)", report.trainable_params,
                              qlora.param_count(), new_mse, old_mse, report.seconds))
    return rows


def rank_sweep(task: TaskData, ranks: list[int], *, seed: int = 0, lr: float = 0.05,
               steps: int = 1200) -> list[RankRow]:
    """Train one adapter per rank on the same data. Read it as the capacity knob:
    below the true rank the adapter cannot express the edit and new-domain error
    stays high; at the true rank the new-domain error bottoms out; above it,
    train mse keeps falling (past the label-noise floor — that is noise being
    fit), the new domain gets worse again, and old-domain drift climbs."""
    rows: list[RankRow] = []
    for rank in ranks:
        started = time.monotonic()
        if rank == 0:
            train_mse = mse(task.base, task.train_x, task.train_y)
            new_mse, old_mse = evaluate(task.base, task)
            rows.append(RankRow(0, 0, train_mse, new_mse, old_mse,
                                time.monotonic() - started))
            continue
        adapter = LoRAAdapter.init(random.Random(seed + rank), task.dims, task.outputs, rank)
        model = LoRAModel(task.base.copy(), adapter)
        train_adapter(model, task.train_x, task.train_y, lr=lr, steps=steps)
        train_mse = mse(model, task.train_x, task.train_y)
        new_mse, old_mse = evaluate(model, task)
        rows.append(RankRow(rank, adapter.param_count(), train_mse, new_mse, old_mse,
                            time.monotonic() - started))
    return rows


def quantization_floor(task: TaskData, bits: int) -> FloorReport:
    """What the quantized base is wrong by, before any adapter exists: the mean
    squared norm of (quantized(x) - float(x)) per output component, on both domains.
    This is the number an adapter starts from, and its low-rank budget cannot
    cancel all of it."""
    qbase = quantize_linear(task.base, bits)
    err = [[q - w for q, w in zip(qrow, wrow)]
           for qrow, wrow in zip(qbase.W, task.base.W)]
    err_model = Linear(task.dims, task.outputs, err)

    def error_mse(xs: list[list[float]]) -> float:
        if not xs:
            return 0.0
        total = 0.0
        for x in xs:
            e = err_model.forward(x)
            total += sum(ei * ei for ei in e)
        return total / (len(xs) * task.outputs)

    return FloorReport(bits, error_mse(task.new_eval_x), error_mse(task.old_eval_x))


def run_experiment(*, seed: int = 0, lr: float = 0.05, steps: int = 1200,
                   ranks: list[int] | None = None, bits: int = 4,
                   quick: bool = False) -> ExperimentReport:
    if quick:
        steps = min(steps, 120)
    task = build_task(seed=seed)
    ranks = ranks if ranks is not None else [0, 1, 2, 4, 6]
    return ExperimentReport(
        seed=seed, steps=steps, lr=lr, dims=task.dims, outputs=task.outputs,
        domain_dim=task.domain_dim, true_rank=task.true_rank, noise=task.noise,
        bits=bits,
        comparison=compare_adaptation(task, seed=seed, lr=lr, steps=steps, bits=bits),
        sweep=rank_sweep(task, ranks, seed=seed, lr=lr, steps=steps),
        floor=quantization_floor(task, bits),
    )


# --- CLI -----------------------------------------------------------------------------


def format_report(rep: ExperimentReport) -> str:
    lines = []
    lines.append(f"task: {rep.dims} dims, {rep.outputs} outputs, domain on a "
                 f"{rep.domain_dim}-dim subspace, true edit rank {rep.true_rank}, "
                 f"label noise {rep.noise}")
    lines.append(f"training: full-batch GD, lr {rep.lr}, {rep.steps} steps, "
                 f"seed {rep.seed} — the ONLY difference between rows is what was trainable")
    lines.append("")
    lines.append("head to head:")
    lines.append(f"{'method':>26}{'trainable':>11}{'new-domain mse':>16}"
                 f"{'old-domain mse':>16}{'seconds':>9}")
    lines.append("-" * 78)
    for row in rep.comparison:
        lines.append(f"{row.name:>26}{row.trainable_params:>11,}"
                     f"{row.new_eval_mse:>16.4f}{row.old_eval_mse:>16.4f}"
                     f"{row.seconds:>9.2f}")
    lines.append("")
    lines.append("rank sweep (same data, same steps, one adapter per rank):")
    lines.append(f"{'rank':>6}{'trainable':>11}{'train mse':>12}"
                 f"{'new-domain':>13}{'old-domain':>13}{'seconds':>9}")
    lines.append("-" * 64)
    for row in rep.sweep:
        lines.append(f"{row.rank:>6}{row.trainable_params:>11,}{row.train_mse:>12.4f}"
                     f"{row.new_eval_mse:>13.4f}{row.old_eval_mse:>13.4f}"
                     f"{row.seconds:>9.2f}")
    if rep.floor is not None:
        lines.append("")
        lines.append(f"base-precision floor ({rep.floor.bits}-bit base, before any adapter):")
        lines.append(f"  quantization error on new-domain inputs: "
                     f"{rep.floor.quant_new_eval_mse:.4f}")
        lines.append(f"  quantization error on old-domain inputs: "
                     f"{rep.floor.quant_old_eval_mse:.4f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=1200, help="GD steps per training run")
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--ranks", type=int, nargs="+", default=[0, 1, 2, 4, 6],
                        help="ranks for the sweep; include 0 for the frozen-base row")
    parser.add_argument("--bits", type=int, default=4, help="base precision for QLoRA")
    parser.add_argument("--quick", action="store_true",
                        help="fewer steps, for smoke tests")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    rep = run_experiment(seed=args.seed, lr=args.lr, steps=args.steps,
                         ranks=args.ranks, bits=args.bits, quick=args.quick)
    if args.json:
        print(json.dumps(asdict(rep), indent=2))
        return 0

    print(format_report(rep))
    print()
    print(f"Read the head-to-head first. Full fine-tune moved all {rep.dims * rep.outputs}")
    print("base weights; LoRA moved the equivalent of a rank-capped edit and beat it on")
    print("BOTH columns here — because this task's true edit is exactly low-rank and")
    print("invisible to the old domain, so the constraint cost nothing while full")
    print("fine-tuning's extra freedom went to fitting label noise. That is the bet you")
    print("make when you choose LoRA: that the edit is low-rank. This demo is the case")
    print("where the bet pays; the sweep below is how you check it on your own task.")
    print()
    print("Now the sweep, the capacity knob. Below the true rank the adapter cannot")
    print(f"express the edit it is asked for. At rank {rep.true_rank} the new-domain error bottoms")
    print("out. Above it, watch two columns move in opposite directions: train mse")
    print("keeps falling PAST the label-noise floor — that is noise being memorized —")
    print("while the new domain gets WORSE again and the old domain keeps drifting.")
    print("Rank is not 'more is better'. It is a capacity knob, and the right setting")
    print("is the size of the edit, which you find by sweeping, not by hoping.")
    print()
    print("The floor row is the third knob: base precision, a number that exists before")
    print("any adapter does. Compare the two qlora rows: more rank on the same")
    print("quantized base made BOTH columns worse — extra capacity just chased the")
    print("same noise harder. What shrinks the quantization error is more BITS, and")
    print("the error shrinks with precision before training even starts. If your")
    print("adapter has plateaued and the base itself is the thing that is wrong, no")
    print("adapter setting will fix it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
