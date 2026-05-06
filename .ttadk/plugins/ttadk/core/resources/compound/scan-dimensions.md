# Compound Scan Dimensions

> ⚠️ This file is for reference only — **schema.yaml is the authoritative source**.
> To modify dimension definitions, edit `resources/compound/schema.yaml`.
> AI agents executing compound should use schema.yaml as the sole data source
> and do not need to read this file.

This document provides human developers with a brief overview of dimension
design intent. Structured definitions (activation, priority, structure,
extraction_guidance, dedup, etc.) are maintained in schema.yaml.

## Dimension Overview

| # | Dimension | Output Path | Design Intent |
|---|-----------|-------------|---------------|
| 1 | Design Patterns | docs/arch/patterns.md | Identify reusable architectural patterns (factory, strategy, observer, etc.) |
| 2 | Coding Standards | docs/CODING.md | Coding style, naming conventions, error handling, logging standards |
| 3 | Common Bugs & Fixes | docs/references/fixes.md | Typical fixed issues and workarounds |
| 4 | Config Templates | docs/references/config-templates.md | Environment variables, Docker, CI config templates |
| 5 | Test Patterns | docs/references/testing-patterns.md | Test structure, mock strategies, coverage patterns |
| 6 | Deployment Scripts | docs/references/deployment.md | Build/deploy/release workflows |
| 7 | Reliability Practices | docs/RELIABILITY.md | Fault tolerance, retry, degradation, monitoring |
| 8 | Security Practices | docs/SECURITY.md | Authentication, authorization, encryption, auditing |
| 9 | Architecture Index | docs/arch/index.md | Architecture document navigation |
| 10 | Product Specs Index | docs/product-specs/index.md | Requirements document navigation |
| 11 | References Index | docs/references/index.md | Reference resource navigation |
| 12 | Project Constitution | docs/CONSTITUTION.md | Project principles and governance rules |
| 13 | Quality Standards | docs/QUALITY.md | Quality gates and testing strategy |
| 14 | Requirement Patterns | docs/product-specs/patterns.md | Requirement structure and decision patterns in specs/ |
| 15 | Service Topology | docs/arch/service-topology.md | Inter-service dependencies and interface contracts |
