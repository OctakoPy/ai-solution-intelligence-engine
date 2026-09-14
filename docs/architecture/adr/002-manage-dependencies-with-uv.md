---
tags:
  - packaging
---

# ADR-002: Manage dependencies with uv
| | |
| ---| ---|
| **Status** |  🟢 Accepted |
| **Created**  | 2025-10-18 |
| **Last Updated**  | 2025-10-18 |
| **Deciders** | Octako |

---

## Context

Every software project needs a way to manage dependencies. This allows reproducible, consistent installs across operating systems and machines. The Python ecosystem has several options that have evolved over time. It is important to choose a dependency manager that is fast, easy to use in CI, well supported by the community, uses metadata in the pyproject.toml file (i.e. [PEP 621 compliant](https://peps.python.org/pep-0621/)) and provides a good developer experience.

## Problem Statement

What dependency manager is best for our project?

## Options Considered

|  Option  | Description | Developer Experience | Speed | Reproducibility | Adoption | CI | PEP 621 | Overall score | Notes |
|----------|-------------|-------------|-----------------|-------------| ----- | ------|------| ------|------|
| **Weight**      | - | 2 | 2 | 2 | 1| 1 | 1 | - | - |
| **uv**          | New, fast replacement for multiple tools, built in Rust by creators of ruff.  | ✅ | ✅ | ✅  | ⚠️ | ✅ |  ✅ | 26 | Very fast. Probably the future standard. Also manages python versions. |
| **Poetry**      | Well established packaging manager with wide adoption. | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | 25 | Mature, widely used but slower. |
| **PDM**         | Light-weight, standards-compliant, written in Python. | ✅ | ⚠️  | ✅ | ⚠️ | ✅  |  ✅ | 24 | Good option, not as fast or popular as uv. |
| **mamba**       | Reimplementation of conda in C++. | ⚠️ | ✅ | ✅ |  ✅ | ✅ | ❌ | 23 | Fast but not PEP 621 compliant |
| **conda**       | Binary package manager, widely used for scientific software. | ⚠️ | ⚠️ | ✅ |  ✅ | ✅ | ❌ | 21 | Not as fast and not PEP 621 compliant |
| **pipenv**      | Simplified packaging management tool. | ⚠️ | ⚠️ | ✅  | ⚠️ | ✅ | ❌ | 20 | Not PEP 621 compliant. |
| **pip + venv**  | Standard library tools. | ✅ | ⚠️  | ❌ | ✅   | ✅ | ⚠️ | 20 | Not suitable for complex environments |
 |
| **spack**       | HPC-oriented packaging manager. Supports full stack. | ❌ | ⚠️ | ✅ | ⚠️ | ⚠️ | ❌ | 17 | Best for multi-language environments on HPC clusters. |

✅ = 3 (good), ⚠️ = 2 (acceptable), ❌ = 1 (poor)

## Decision Outcome

We will use uv since it is extremely fast and likely to become the new standard. It provides a good developer experience and replaces multiple tools. Performance is particularly important for CI. Poetry and PDM are good alternatives. Poetry is more mature and widely adopted.

## Consequences

Using uv will simplify Python and dependency management. It is extremely fast and so will speed up continuous integration, reducing waiting time substantially where installing dependencies is the bottleneck. It also manages Python versions and is PEP 621 compliant. This tool is likely to become the new standard.

A risk is that this is under active development and is not yet widely adopted. Alternatives to fall back on include Poetry or PDM. This ADR should be revisited in one year since development in this area is ongoing and adoption of particular tools is in a state of flux.

## Confirmation

The project README will document the usage of uv. CI workflows will use uv and the uv.lock file will be placed under version control.

## Links

| Type | Links |
| -----| ------|
| **ADRs**   | |
| **Issues** | |
| **PRs**    | |
