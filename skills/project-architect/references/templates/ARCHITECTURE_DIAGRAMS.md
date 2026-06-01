---
template_name: ARCHITECTURE_DIAGRAMS
generate_when: "decisions.scale >= 'growth' OR decisions.complexity == 'high'"
required_decisions: []
optional_decisions: []
depends_on: [PROJECT_OVERVIEW]
revision_triggers: [project.type, frontend.framework, backend.framework, database.engine, hosting.*]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Architecture Diagrams: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🏗️ C4 Context Diagram](#c4-context-diagram)
- [🏗️ C4 Container Diagram](#c4-container-diagram)
- [🏗️ C4 Component Diagrams (per major area)](#c4-component-diagrams-per-major-area)
- [🏗️ Sequence Diagrams (for key flows)](#sequence-diagrams-for-key-flows)
- [🏗️ Data Flow Diagram](#data-flow-diagram)
- [↻ Revision Log](#revision-log)

## 🏗️ C4 Context Diagram
System-in-the-world view. Show the project as a single box with all external actors (users, admins, third-party APIs, partner systems) and the high-level interactions between them. Use Mermaid `flowchart` or PlantUML C4-PlantUML. Caption the audience and the question this view answers.

## 🏗️ C4 Container Diagram
Break the system into deployable containers (web app, API, workers, DB, cache, queue, edge functions). Show technology choices on each container and the protocols between them (HTTPS, WebSocket, gRPC, SQL, etc.). Reference DEPLOYMENT.md for runtime details.

## 🏗️ C4 Component Diagrams (per major area)
One component diagram per major bounded context (e.g., Auth, Billing, Search, Realtime). Each diagram zooms into a container and shows its internal modules/services and how they collaborate. Keep each diagram focused — split if it grows past ~12 components.

## 🏗️ Sequence Diagrams (for key flows)
Mermaid `sequenceDiagram` for the critical flows. Cover at minimum: signup/login, the primary user action (checkout / publish / deploy), background-job dispatch, and any cross-service call that hits a third party. Each diagram names the actors, includes error/timeout branches, and links to the code path that implements it.

## 🏗️ Data Flow Diagram
Where data originates, where it lands, how it transforms, where it's stored, and where it exits the system. Highlight PII boundaries and cross-region flows. Link to DATABASE_DESIGN.md and SECURITY_AND_COMPLIANCE.md for storage and compliance specifics.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
