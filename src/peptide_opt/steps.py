"""Stateless CLI steps for Argo Workflows (ADR 0012 P1/P2).

    python -m peptide_opt.steps fold       --work-dir /work   # step 1     (OmegaFold)
    python -m peptide_opt.steps dock-score --work-dir /work   # steps 2-6  (the long one)
    python -m peptide_opt.steps redesign   --work-dir /work   # step 7     (ProteinMPNN)
    python -m peptide_opt.steps report     --work-dir /work   # step 8

Replaces `tasks/processor.py` (the polling worker). No DB, no SeaweedFS, no asyncio: Argo
claims the work, compute-foundry's fetch/publish move the bytes, the operator owns status.

## Do not use `peptide-opt run --step N`

That path has never worked. `cli.py:66` calls `optimizer.run_step(step)` and
`PeptideOptimizer` has no such method — it raises AttributeError on every invocation. A
second, shadow dispatcher exists at `optimizer.py:578-626` but is not wired to any console
script and cannot pass `receptor_pdb_filename`, so it dies in step 2. This module is the
first working per-stage entry point in the repo.

## The layout, and why it survives a pod boundary

`PeptideOptimizer` derives `middle_dir = output_dir.parent / "middlefiles"`. With
`output_dir=/work/output` that lands on `/work/middlefiles` — i.e. on the workflow's shared
PVC, which every stage of the same workflow mounts. Steps 1-7 write only into
`middlefiles/`; only step 8 writes into `output/`. So the inter-stage working set persists
for free, and `publish` still only has to upload `output/`.

The old worker destroyed `middlefiles/` twice over (`cleanup_intermediate_files()` plus an
`rmtree` of the temp dir), which is why nothing intermediate ever reached storage. We pass
`cleanup=False` for every stage — cleanup is now the PVC's job, and Argo deletes it with
the workflow.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("peptide-step")

# Where stage `dock-score` records the pose count adcp ACTUALLY produced. See _make().
_NPOSES_FILE = "n_poses.actual.json"


def _load_params(work_dir: Path) -> Dict[str, Any]:
    return json.loads((work_dir / "params.json").read_text())


def _proteinmpnn_dir() -> str:
    # cli.py's own finder ignores PROTEINMPNN_PATH and walks a hardcoded list that only
    # resolves because WORKDIR happens to be /app. Our steps set their own cwd, so read the
    # env var the Dockerfile actually sets (Dockerfile:176).
    return os.environ.get("PROTEINMPNN_PATH", "/app/vendor/ProteinMPNN")


def _make(work_dir: Path, params: Dict[str, Any]):
    """Rebuild the PeptideOptimizer in a fresh pod, with the same state it would have had
    inside the old single-process run.

    ⚠️ `n_poses` is the trap. `step3_docking` OVERWRITES `self.n_poses` at runtime
    (optimizer.py:198-210) when adcp returns fewer poses than requested, and steps 4-8 all
    loop `range(1, self.n_poses + 1)`. Worse, step 5 *names* its score file
    `score_rank_1_{n_poses}.dat` and step 8 re-derives that same name. In one process that
    mutation is invisible; across pods it is data loss — `redesign`/`report` would iterate
    a stale count and then look for a score file that `dock-score` never wrote under that
    name. So `dock-score` persists the real count and later stages read it back.
    """
    from peptide_opt.core.optimizer import PeptideOptimizer

    n_poses = int(params.get("n_poses", 10))
    actual = work_dir / "middlefiles" / _NPOSES_FILE
    if actual.exists():
        n_poses = int(json.loads(actual.read_text())["n_poses"])
        logger.info("using the pose count adcp actually produced: %d", n_poses)

    return PeptideOptimizer(
        input_dir=str(work_dir / "input"),
        output_dir=str(work_dir / "output"),
        proteinmpnn_dir=_proteinmpnn_dir(),
        cores=None,  # cgroup-aware detection; the manifest's CPU_CORES/limits decide.
        cleanup=False,  # never — the next pod needs middlefiles/.
        n_poses=n_poses,
        num_seq_per_target=int(params.get("num_seq_per_target", 10)),
        proteinmpnn_seed=int(params.get("proteinmpnn_seed", 37)),
        receptor_pdb_filename=params.get("receptor_pdb_filename"),
    )


def stage_fold(work_dir: Path, params: Dict[str, Any]) -> None:
    """Step 1 — OmegaFold.

    Historically the only GPU-touching stage, and the reason peptide-opt held the platform's
    single card for an entire hour-long run. ADR 0012 P0 measured it on CPU: 26.5 s for an
    11-mer. It stays CPU-only and the card belongs to HighFold's AlphaFold2.
    """
    opt = _make(work_dir, params)
    opt.middle_dir.mkdir(parents=True, exist_ok=True)
    opt.step1_model_peptide()


def stage_dock_score(work_dir: Path, params: Dict[str, Any]) -> None:
    """Steps 2-6 — PyMOL → adcp docking → Vina scoring → merge. Pure CPU, the bulk of the run."""
    opt = _make(work_dir, params)
    opt.step2_add_hydrogens()
    requested = opt.n_poses
    opt.step3_docking()  # may lower opt.n_poses in place
    if opt.n_poses != requested:
        logger.warning("adcp produced %d poses, not the %d requested", opt.n_poses, requested)
    # Persist it BEFORE steps 4-6 so that even a crash mid-stage leaves the truth on disk.
    (work_dir / "middlefiles" / _NPOSES_FILE).write_text(json.dumps({"n_poses": opt.n_poses}))
    opt.step4_sort_atoms()
    opt.step5_score_binding()
    opt.step6_merge_structures()


def stage_redesign(work_dir: Path, params: Dict[str, Any]) -> None:
    """Step 7 — ProteinMPNN sequence redesign.

    Also a torch program, and it will grab cuda:0 if it can see one. It must NOT: the card
    is HighFold's. We simply never request `nvidia.com/gpu` for this step, so there is no
    CUDA device in the pod and torch falls back to CPU. The model is small; this is fine.
    """
    _make(work_dir, params).step7_proteinmpnn_optimization()


def stage_report(work_dir: Path, params: Dict[str, Any]) -> None:
    """Step 8 — the only stage that writes into output/."""
    opt = _make(work_dir, params)
    (work_dir / "output").mkdir(parents=True, exist_ok=True)
    opt.step8_final_analysis()

    result = work_dir / "output" / "result.csv"
    if not result.exists():
        raise RuntimeError("stage `report` produced no result.csv")
    logger.info("report written: %s", result)


STAGES = {
    "fold": stage_fold,
    "dock-score": stage_dock_score,
    "redesign": stage_redesign,
    "report": stage_report,
}


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    p = argparse.ArgumentParser(prog="peptide_opt.steps")
    p.add_argument("stage", choices=sorted(STAGES))
    p.add_argument("--work-dir", default="/work")
    args = p.parse_args()

    work_dir = Path(args.work_dir)
    params = _load_params(work_dir)
    logger.info("stage=%s work_dir=%s", args.stage, work_dir)

    # steps 3 and 5 chdir into middle_dir and back; the old worker also chdir'd into the
    # job dir first. Reproduce that so relative paths inside the science code still resolve.
    (work_dir / "middlefiles").mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)

    try:
        STAGES[args.stage](work_dir, params)
    except Exception as e:
        print(f"FATAL [{args.stage}] {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
