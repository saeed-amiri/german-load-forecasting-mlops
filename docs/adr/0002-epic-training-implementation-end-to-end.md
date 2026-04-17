# ADR-0002: Epic-training-implementation-end-to-end

- Status: Accepted
- Date: 2026-04-12
- Jira: KAN-7 (https://saeed-amiri.atlassian.net/browse/KAN-7)
- PR:

## Context

At the moment, parts of the stack exist (configuration, data pipeline components, infrastructure skeleton), but the training lifecycle is not yet implemented as a complete MLOps workflow. That means we still lack a unified path from configuration -> training run -> best-parameter selection -> artifact/version tracking -> orchestration -> CI/CD integration.

This epic defines the implementation of that workflow as a sequence of linked deliverables: context management for runtime consistency, parameter optimization with tests, main training logic, containerized execution, DVC pipeline integration, DAG orchestration, and CI/CD automation. The goal is to establish a maintainable training system where experiments are traceable, outputs are reproducible, and model delivery can be continuously operated with clear engineering ownership.

## Decision
Implement the end-to-end training lifecycle in the following stages:
1. **Context Management**: Develop a context manager to ensure consistent runtime environments across training runs, handling configuration loading, logging setup, and resource management.  # TODO

2. **Parameter Optimization**: Implement a parameter optimization module with unit tests to validate its functionality and ensure it can effectively search for optimal hyperparameters.  # TODO

3. **Containerization**: Containerize the training workflow using Docker to ensure consistency across different environments and facilitate deployment.  # TODO

4. **Main Training Logic**: Develop the core training logic that integrates with the context manager and parameter optimization, ensuring it can execute training runs and produce artifacts.  # TODO

5. **Docker-compose, DVC Pipeline Integration**: Integrate the training workflow into a DVC pipeline to enable version control of data, code, and models, and to facilitate reproducibility.  # TODO

6. **DAG Orchestration**: Implement DAG orchestration using a tool like Airflow or Prefect to manage the execution of the training pipeline, allowing for scheduling and monitoring of training runs.  # TODO

7. **CI/CD Automation**: Set up CI/CD pipelines to automate the testing and deployment of the training workflow, ensuring that changes are validated and can be deployed seamlessly  # TODO

Each stage will be tracked as a separate Jira issue linked to this epic, with clear acceptance criteria and deliverables and a separate git branch. The implementation will be iterative, allowing for feedback and adjustments as we progress through the stages.


## Model:
Will start with a **simple linear regression** model for initial implementation and testing, with the possibility to extend to more complex models in the future as needed. For the main training will start with **GradientBoostingClassifier**

## Consequences
### Positive
- Establishes a clear and maintainable training workflow that can be iteratively improved.
- Enables reproducibility and traceability of training runs, facilitating debugging and optimization.
- Provides a foundation for future enhancements, such as adding more complex models or integrating additional tools.
### Negative / Trade-offs
- Initial implementation may require significant development effort and time.
- Requires coordination across multiple components and tools, which may introduce complexity.
- May require ongoing maintenance to ensure the workflow remains functional and up-to-date with evolving requirements and tools.

## Follow-up Actions
- [ ] Add new sources of data to the training pipeline as needed.
- [ ] Extend the training workflow to support additional models and algorithms.
- [ ] Continuously monitor and optimize the training workflow for performance and reliability.


# One moment on system design:

## Plan: Training-Selector Architecture for MLOps

Recommended direction: use a hybrid control plane.  
1. Config is the default behavior.  
2. API or runtime request can override mode/model safely.  
3. Matrix experiments run only when explicitly requested.  
4. Selector (tuner) is separate from trainer.  
5. Full local artifact versioning is required now, MLflow is added as an extra tracking layer.  
  
## Core design questions answered  
  
### Should selector be separate from training?  
Yes. Best practice is:  
1. Orchestrator decides flow.  
2. Selector finds best params.  
3. Trainer fits final model.  
4. Evaluator computes metrics.  
5. Artifact manager persists outputs.  
This separation keeps code testable and lets you replace selector later (for example RandomizedSearchCV to Optuna) without breaking training.  
  
### How should model choice work?  
Use a layered precedence:  
1. Explicit request model/params (from API/frontend).  
2. Pinned previous run params.  
3. Latest successful best params.  
4. Config defaults.  
This gives flexibility while preserving reproducibility.  
  
### Config-only or DAG/modeling logic?  
Use both, with clear boundaries:  
1. Config defines defaults and allowed model/search spaces.  
2. Runtime request chooses mode and optional overrides.  
3. Orchestrator enforces precedence and validation.  
4. DAG/CLI/API call the same training entrypoint payload.  
This avoids duplicated logic across interfaces.  
  
## Main questions to ask for ML system design  
1. What exact prediction target and business decision does the model support?  
2. What is the offline metric and what business KPI must improve?  
3. What failure is worse: false positive or false negative style errors in your domain?  
4. What data window and retraining cadence are required?  
5. What drift signals will trigger retraining?  
6. What is the rollback strategy if a new model underperforms?  
7. What artifacts must be reproducible for audit: data slice, params, code version, model binary, metrics?  
8. How will online/inference behavior match training feature logic?  
9. What latency and throughput limits exist for inference?  
10. Who approves model promotion to production?  
  
## Measures for ML design quality  
1. Reproducibility: same inputs produce same model/metrics.  
2. Traceability: every model has run_id, params source, data fingerprint.  
3. Modularity: selector/trainer/inference/artifacts are independently testable.  
4. Extensibility: adding a new model type requires minimal changes.  
5. Reliability: clear validation and failure messages at boundaries.  
6. Observability: metrics, params, and artifacts are logged and queryable.  
7. Operability: same training contract works for API, CLI, and DAG.  
8. Governance readiness: artifact and metadata are versioned before MLflow registry rollout.  
 