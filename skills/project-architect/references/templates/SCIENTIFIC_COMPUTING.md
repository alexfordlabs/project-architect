---
template_name: SCIENTIFIC_COMPUTING
generate_when: "decisions.project.type == 'scientific'"
required_decisions: [scientific.compute_backend, scientific.reproducibility]
optional_decisions: [scientific.notebooks, scientific.environment_pinning, scientific.workflow, scientific.publication]
depends_on: []
revision_triggers: [scientific.compute_backend, scientific.reproducibility, scientific.environment_pinning]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Scientific Computing: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Domain & Goal](#domain-goal)
- [Compute Backend](#compute-backend)
- [Reproducibility Strategy (seeds, env freeze, container/Nix)](#reproducibility-strategy-seeds-env-freeze-containernix)
- [Notebooks vs Scripts](#notebooks-vs-scripts)
- [🗄️ Data Scale & Storage](#data-scale-storage)
- [Workflow Engine (Snakemake / Nextflow / Dagster)](#workflow-engine-snakemake-nextflow-dagster)
- [🚀 Publication Pipeline (Quarto / LaTeX)](#publication-pipeline-quarto-latex)
- [Provenance & Lineage](#provenance-lineage)
- [↻ Revision Log](#revision-log)

## Domain & Goal
Scientific domain (genomics, climate, particle physics, astronomy, materials, etc.) and the concrete scientific question or artifact this project produces.

## Compute Backend
Compute environment (laptop, HPC cluster, SLURM, Kubernetes batch, cloud — AWS Batch / Azure Batch / GCP Batch, GPUs / TPUs), parallelism model, and resource budget.

## Reproducibility Strategy (seeds, env freeze, container/Nix)
Reproducibility practices: random-seed discipline, environment freezing (conda-lock, uv lock, poetry.lock, renv), containerization (Docker, Apptainer/Singularity), Nix/Guix where applicable.

## Notebooks vs Scripts
Notebook policy (exploration only vs source-of-truth) and script discipline (papermill / nbconvert / jupytext for sync, linting, CI execution of notebooks).

## 🗄️ Data Scale & Storage
Data volumes per stage, storage tier (local SSD, parallel filesystem — Lustre/GPFS, object store — S3/GCS), file formats (Parquet, Zarr, HDF5, FITS, BAM/CRAM), and access patterns.

## Workflow Engine (Snakemake / Nextflow / Dagster)
Workflow / pipeline tool (Snakemake, Nextflow, Cromwell/WDL, Dagster, Prefect, Airflow), DAG layout, and resume / partial-rerun semantics.

## 🚀 Publication Pipeline (Quarto / LaTeX)
Manuscript & figure pipeline (Quarto, R Markdown, LaTeX/Overleaf, MyST, Jupyter Book) and how figures/tables are regenerated from data, not hand-edited.

## Provenance & Lineage
Provenance capture (W3C PROV, OpenLineage, Snakemake reports, nf-core MultiQC), code-version + data-version + parameter pinning per result, and FAIR data principles adherence.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
