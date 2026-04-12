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