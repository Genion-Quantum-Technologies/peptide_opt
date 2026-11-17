# Argo scientific stages

2026-11-17: the unused HTTP service, database poller and SeaweedFS client were removed. Run `python -m peptide_opt.steps --help` for the supported stages. Science stages use only the workflow work directory. `compute-foundry` owns scheduling, task status and storage I/O. Scientific algorithms are unchanged.

Legacy compose and service deployment instructions describe the retired poller and are not supported entrypoints. Existing zero-replica cluster Deployments retain their old image digests for rollback; new releases only update WorkflowTemplates.
