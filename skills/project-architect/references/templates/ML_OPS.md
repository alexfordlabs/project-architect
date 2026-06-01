---
template_name: ML_OPS
generate_when: "decisions.project.type == 'ai_ml' AND decisions.ml.training == true"
required_decisions: [ml.training_framework]
optional_decisions: [ml.dataset_versioning, ml.experiment_tracking, ml.serving, ml.monitoring, ml.evaluation_benchmarks]
depends_on: [AI_AND_ML]
revision_triggers: [ml.training_framework, ml.serving, ml.experiment_tracking]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# ML Ops: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Training Framework](#training-framework)
- [🗄️ Dataset Versioning & Provenance](#dataset-versioning-provenance)
- [🧪 Experiment Tracking (Weights & Biases / MLflow / Trackio)](#experiment-tracking-weights-biases-mlflow-trackio)
- [Hyperparameter Sweep Strategy](#hyperparameter-sweep-strategy)
- [🗄️ Model Registry](#model-registry)
- [Serving Stack (inference)](#serving-stack-inference)
- [📊 Model Monitoring (drift, latency, cost)](#model-monitoring-drift-latency-cost)
- [📊 Evaluation Benchmarks](#evaluation-benchmarks)
- [↻ Revision Log](#revision-log)

## Training Framework
Training stack (PyTorch, JAX, TensorFlow, HuggingFace Trainer, Lightning, Axolotl, Unsloth) and the hardware target (single-GPU, multi-GPU DDP, TPU, accelerator clusters).

## 🗄️ Dataset Versioning & Provenance
Versioning tooling (DVC, LakeFS, HuggingFace Datasets, Pachyderm) and provenance capture (source, license, collection date, transformation pipeline).

## 🧪 Experiment Tracking (Weights & Biases / MLflow / Trackio)
Tracker choice, what's logged (hyperparameters, metrics, artifacts, system stats), team conventions for run naming, and run-comparison practices.

## Hyperparameter Sweep Strategy
Sweep tooling (W&B Sweeps, Optuna, Ray Tune, Hydra), search method (grid, random, Bayesian, ASHA), and budget per sweep.

## 🗄️ Model Registry
Registry choice (W&B Model Registry, MLflow Registry, HuggingFace Hub, custom S3-based), lifecycle stages (staging → production → archived), and approval gates.

## Serving Stack (inference)
Serving infrastructure (vLLM, TGI, Triton, TorchServe, Ray Serve, Modal, Replicate, SageMaker), batching strategy, accelerator type, and autoscaling policy.

## 📊 Model Monitoring (drift, latency, cost)
Monitoring stack (Arize, WhyLabs, Fiddler, Evidently, custom), tracked signals (input drift, prediction drift, latency, error rate, cost per request), and alert thresholds.

## 📊 Evaluation Benchmarks
Internal eval suites + external benchmarks (MMLU, HumanEval, GSM8K, custom), gating criteria for promotion to production, and human-eval cadence.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
