# LOGVANTA

### Adaptive Universal Log Pre-Processing & Normalization Framework

LOGVANTA is a security log pre-processing framework designed to ingest heterogeneous security logs, automatically profile and parse their structure, normalize them into a common OCSF-based representation, validate the resulting events, and maintain traceability back to the original raw log.

The key differentiator of LOGVANTA is its **adaptive mapping lifecycle**. Instead of treating parsers and field mappings as permanently hardcoded rules, LOGVANTA maintains versioned mappings for each log source. When a source format changes, the system can detect structural drift, generate candidate mappings, calculate confidence, and create a new mapping version for controlled approval.

> **Project status:** Active development — first major engineering phase complete. The core ingestion → profiling → parsing → OCSF normalization → validation → traceability pipeline is implemented and working, along with a persistent versioned mapping registry. The full closed-loop adaptive cycle (drift → candidate → approval → automatic re-use) is built as separate pieces but not yet demonstrated end-to-end in one continuous run. See [Section 18](#18-current-project-status) for the exact breakdown of what's implemented, in progress, and planned.

---

## Table of Contents

1. [Problem](#1-problem)
2. [Current Architecture](#2-current-architecture)
3. [Implemented Features](#3-implemented-features)
4. [Parsing Engine](#4-parsing-engine)
5. [OCSF-Based Normalization](#5-ocsf-based-normalization)
6. [Versioned Mapping Registry](#6-versioned-mapping-registry)
7. [Active Mapping Selection](#7-active-mapping-selection)
8. [Adaptive Mapping](#8-adaptive-mapping)
9. [Drift Detection](#9-drift-detection)
10. [Candidate Mapping Generation](#10-candidate-mapping-generation)
11. [Controlled Mapping Activation](#11-controlled-mapping-activation)
12. [Traceability](#12-traceability)
13. [Field-Level Traceability](#13-field-level-traceability)
14. [Validation](#14-validation)
15. [Current API](#15-current-api)
16. [Example: Adaptive Mapping in Action](#16-example-adaptive-mapping-in-action)
17. [Technology Stack](#17-technology-stack)
18. [Current Project Status](#18-current-project-status)
19. [Design Philosophy](#19-design-philosophy)
20. [Planned Differentiator](#20-planned-differentiator)
21. [Current Development Stage](#21-current-development-stage)
22. [How to Test LOGVANTA](#22-how-to-test-logvanta)
23. [Basic Processing Test](#23-basic-processing-test)
24. [Test Mapping Versions](#24-test-mapping-versions)
25. [Test Drift Detection](#25-test-drift-detection)
26. [Test Adaptive Mapping](#26-test-adaptive-mapping)
27. [Activate a Mapping Version](#27-activate-a-mapping-version)
28. [Verify the New Mapping](#28-verify-the-new-mapping)
29. [Complete Test Flow](#29-complete-test-flow)

---

## 1. Problem

Security environments generate logs from many different sources:

- Firewalls
- Routers
- IDS/IPS systems
- Network security appliances
- Other perimeter devices

These systems produce logs in different formats and use different field names for the same concepts.

**Firewall A**
```text
src_ip=192.168.1.20 dst_ip=10.0.0.8 action=deny
```

**Firewall B**
```text
source_address=192.168.1.20 destination_address=10.0.0.8 decision=deny
```

Both represent similar security activity, but downstream security systems cannot reliably treat them as the same event without preprocessing and normalization.

Traditional approaches often depend heavily on manually written parsers and mappings. LOGVANTA aims to reduce this dependency through:

```text
Ingestion → Profiling → Parsing → Adaptive Mapping → OCSF Normalization → Validation → Traceability
```

---

## 2. Current Architecture

```text
                         LOGVANTA
                            │
                            ▼
                    ┌───────────────┐
                    │ Raw Log Input │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Ingestion   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Profiler   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Parser     │
                    └───────┬───────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Adaptive Mapping    │
                 │ Registry            │
                 │                     │
                 │ v1 → archived       │
                 │ v2 → active         │
                 │ v3 → candidate      │
                 └──────────┬──────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ OCSF Mapper   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Validation   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Traceability  │
                    └───────────────┘
```

---

## 3. Implemented Features

### 3.1 Log Ingestion

LOGVANTA accepts raw security log data through the processing API. Each incoming event receives a unique event identifier.

```json
{
  "source": "firewall-01",
  "raw_log": "source_address=192.168.1.20 destination_address=10.0.0.8 decision=deny"
}
```

The ingestion layer generates an `event_id` that is carried through the remaining pipeline.

### 3.2 Automatic Log Profiling

LOGVANTA analyzes the structure of incoming logs before parsing them. Currently supported structural detection includes:

- Key-value logs
- JSON
- Delimited structures
- Other supported parser formats

For key-value logs, the profiler identifies fields and infers their types.

```text
source_address=192.168.1.20
destination_address=10.0.0.8
decision=deny
severity_level=5
```

The profiler identifies:

| Field | Inferred Type |
|---|---|
| `source_address` | IP |
| `destination_address` | IP |
| `decision` | string |
| `severity_level` | number |

The profiler also produces confidence information for the detected structure and fields.

---

## 4. Parsing Engine

After profiling, LOGVANTA selects the appropriate parsing strategy.

```text
Raw Log → Format Detection → key_value → Parser →
{
    "source_address": "192.168.1.20",
    "destination_address": "10.0.0.8",
    "decision": "deny",
    "severity_level": "5"
}
```

This separates **format detection** from **normalization**, allowing the later mapping layer to operate on structured fields.

---

## 5. OCSF-Based Normalization

LOGVANTA uses an OCSF-oriented normalized representation instead of creating an entirely proprietary event schema. Different vendor-specific fields can therefore be mapped into common security concepts.

| Vendor Field | OCSF Field |
|---|---|
| `source_address` | `source_endpoint` |
| `destination_address` | `destination_endpoint` |
| `decision` | `action` |
| `severity_level` | `severity` |

**Example normalized event:**

```json
{
  "event_id": "fc066f40-30db-4c57-8306-3553b15895ae",
  "source": "firewall-01",
  "event_time": null,
  "source_endpoint": "192.168.1.20",
  "destination_endpoint": "10.0.0.8",
  "action": "deny",
  "severity": "5",
  "message": null,
  "ocsf_class": "Network Activity",
  "mapping_confidence": 1,
  "mapping_version": 2
}
```

---

## 6. Versioned Mapping Registry

One of LOGVANTA's core components is the mapping registry. Mappings are not treated as static hardcoded rules — each source can maintain multiple mapping versions.

```text
firewall-01
    Version 1 → archived
    Version 2 → active
    Version 3 → candidate
```

Every version stores: source, version number, field mappings, confidence, status, and creation timestamp.

The mapping registry is persisted using SQLAlchemy-backed database storage, meaning mappings survive application restarts.

---

## 7. Active Mapping Selection

When a log is processed, LOGVANTA retrieves the currently active mapping for that source.

```text
firewall-01 → Active Mapping → Version 2
```

The mapping is then applied during normalization. This means a mapping version is not merely stored for record keeping — **it actively controls how incoming logs are normalized.**

---

## 8. Adaptive Mapping

LOGVANTA contains an adaptive workflow for detecting changes in log structure.

```text
Baseline Logs → Baseline Profile
Current Log   → Current Profile
                     ↓
              Drift Comparison
                ↙         ↘
          No Drift      Drift Detected
                              ↓
                      Parse New Structure
                              ↓
                      Generate Candidates
                              ↓
                      Calculate Confidence
                              ↓
                      Create Candidate Version
```

Candidate mappings are intentionally **not automatically activated**. This prevents an uncertain adaptation from silently changing production normalization.

---

## 9. Drift Detection

LOGVANTA maintains a baseline profile for a source and compares new logs against it.

**Known Format**
```text
source_address, destination_address, decision, severity_level
```

**New Format**
```text
src_addr, dst_addr, action, severity
```

The structural difference can trigger the adaptive workflow, which then generates candidate mappings for the changed fields.

---

## 10. Candidate Mapping Generation

When drift is detected, LOGVANTA analyzes the newly observed fields and attempts to determine their likely normalized targets. Candidate decisions are based on signals such as:

- Field-name similarity
- Inferred data type
- Matching known fields
- Confidence scores

```json
{
  "field": "source_address",
  "target": "source_endpoint",
  "confidence": 0.95,
  "matched_known_field": "src_ip",
  "name_similarity": 0.91,
  "type_bonus": 0.1,
  "decision": "accepted"
}
```

The individual candidate confidences are aggregated into a mapping confidence for the generated version.

---

## 11. Controlled Mapping Activation

Candidate mappings are not immediately trusted:

```text
Candidate → Review → Approved → Active
```

Once approved, a version becomes active and the previous active version is archived.

```text
Before:              After approving v2:
v1 → active          v1 → archived
                      v2 → active
```

This provides controlled evolution of source mappings.

---

## 12. Traceability

Every processed event maintains a connection between the original event and its normalized representation. LOGVANTA currently records:

- Event ID
- Source
- Original raw log
- SHA-256 hash
- Normalized fields
- Mapping version
- Source of normalized fields

```json
{
  "event_id": "fc066f40-30db-4c57-8306-3553b15895ae",
  "source": "firewall-01",
  "raw_sha256": "fd576ce484a5219345877d426ce57e94ec5b8d2d312bd21ad160e54d940d9e81",
  "raw_preserved": true
}
```

This allows an analyst to understand how the normalized event relates to its original source data.

---

## 13. Field-Level Traceability

LOGVANTA also records the origin of normalized fields:

```text
source_endpoint       value: 192.168.1.20    source: source_endpoint
destination_endpoint  value: 10.0.0.8        source: destination_endpoint
action                value: deny            source: action
severity              value: 5               source: severity

mapping_version: 2
```

This makes it possible to identify which mapping version was responsible for the normalization.

---

## 14. Validation

After normalization, the resulting event passes through a validation layer:

```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

This provides a quality-control step between normalization and downstream processing.

---

## 15. Current API

The current API exposes the core LOGVANTA pipeline.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/process` | `POST` | Processes a raw event through the full pipeline: Ingestion → Profiling → Parsing → Mapping → OCSF normalization → Validation → Traceability |
| `/api/v1/drift/check` | `POST` | Compares baseline logs against a current log |
| `/api/v1/adaptation/analyze` | `POST` | Generates candidate mappings from parsed fields |
| `/api/v1/adaptation/version` | `POST` | Creates a persistent mapping version |
| `/api/v1/adaptation/{source}/versions` | `GET` | Returns the mapping history for a source |
| `/api/v1/adaptation/{source}/activate/{version}` | `POST` | Activates a selected mapping version |
| `/api/v1/adaptation/workflow` | `POST` | Runs the full workflow: Baseline → Drift Detection → Candidate Generation → Candidate Mapping Version |

---

## 16. Example: Adaptive Mapping in Action

**Input:**
```text
source_address=192.168.1.20
destination_address=10.0.0.8
decision=deny
severity_level=5
```

**Active mapping:** `Version 2`

**Output:**
```json
{
  "source_endpoint": "192.168.1.20",
  "destination_endpoint": "10.0.0.8",
  "action": "deny",
  "severity": "5",
  "ocsf_class": "Network Activity",
  "mapping_version": 2
}
```

The same response also contains validation and traceability information. This demonstrates that the versioned mapping is actually being used by the processing pipeline rather than simply stored in the database.

---

## 17. Technology Stack

**Backend**
- Python
- FastAPI
- Uvicorn

**Data & ORM**
- SQLAlchemy
- SQLite for local development
- PostgreSQL-compatible architecture

**Processing**
- Custom log profiler
- Format-specific parsing layer
- OCSF-oriented normalization
- Drift detection
- Adaptive mapping engine

**API Testing**
- FastAPI Swagger / OpenAPI
- Postman

**Deployment**
- Docker / Docker Compose *(planned)*

---

## 18. Current Project Status

### ✅ Implemented

- [x] Raw log ingestion
- [x] Event ID generation
- [x] Log profiling
- [x] Key-value parsing
- [x] OCSF-oriented normalization
- [x] Validation
- [x] Raw-event traceability
- [x] SHA-256 integrity hashing
- [x] Mapping registry
- [x] Persistent mapping versions
- [x] Active/archived mapping lifecycle
- [x] Active mapping integration with processing
- [x] Drift detection foundation
- [x] Candidate mapping generation
- [x] Adaptive workflow foundation
- [x] Candidate mapping persistence
- [x] Controlled mapping activation

### 🔄 In Progress

- [ ] Complete end-to-end drift → candidate → approval → processing demonstration
- [ ] More realistic perimeter-device log formats
- [ ] Improved onboarding workflow
- [ ] More sophisticated confidence scoring
- [ ] Parser/version lifecycle improvements

### 📋 Planned

- [ ] Multiple real firewall/router/IDS formats
- [ ] Export adapters
- [ ] Security data lake / SIEM integration
- [ ] Visualization dashboard
- [ ] ML/anomaly detection
- [ ] Air-gapped deployment hardening
- [ ] Threat-model-driven protections
- [ ] Comprehensive automated testing
- [ ] Production-oriented deployment
- [ ] Large-scale processing support

---

## 19. Design Philosophy

LOGVANTA is not intended to become another generic SIEM. The project focuses on the preprocessing layer:

```text
Heterogeneous Security Logs → LOGVANTA → Consistent OCSF Events → SIEM / Data Lake / ML
```

The key design principle:

> **Adapt the normalization process when log formats change instead of relying entirely on permanently hardcoded parsers.**

The system separates:

```text
Detection → Parsing → Mapping → Normalization → Validation → Traceability
```

This modular structure allows individual components to evolve without rebuilding the entire pipeline.

---

## 20. Planned Differentiator

The long-term differentiating capability of LOGVANTA is its **self-adapting mapping lifecycle**. Instead of simply supporting a fixed list of log formats:

```text
Format A → Parser A
Format B → Parser B
Format C → Parser C
```

LOGVANTA aims toward:

```text
Unknown / Changed Format
          ↓
    Profile Structure
          ↓
      Detect Drift
          ↓
  Generate Candidates
          ↓
   Score Confidence
          ↓
   Human Validation
          ↓
    New Mapping vN
          ↓
      Active Use
```

The objective is to reduce the amount of manual parser maintenance required when security devices introduce new or modified log formats.

---

## 21. Current Development Stage

LOGVANTA is currently **in active development**. The core processing pipeline and persistent adaptive mapping foundation are implemented.

The current implementation represents approximately the **first major engineering phase** of the project. The next major milestone is completing and validating the full adaptive lifecycle end-to-end:

```text
Existing Format → Format Drift → Detection → Candidate Generation →
Confidence → Approval → New Mapping Version → Automatic Use
```

The project will then expand toward multi-source interoperability, visualization, export, anomaly detection, and air-gapped deployment.

---

## 22. How to Test LOGVANTA

Follow the steps below to run and test the current implementation locally.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/vishalpro7/logvanta.git
cd logvanta
```

### Step 2 — Enter the Backend

```bash
cd backend
```

### Step 3 — Create and Activate Virtual Environment

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Start the API Server

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Step 6 — Open Swagger UI

Open the following URL in a browser:

```text
http://127.0.0.1:8000/docs
```

Swagger UI provides an interactive interface for testing the LOGVANTA APIs without requiring any additional frontend.

---

## 23. Basic Processing Test

Use the processing endpoint:

```text
POST /api/v1/process
```

Send a sample firewall log using the request body expected by the API.

Example key-value log:

```text
source_address=192.168.1.20 destination_address=10.0.0.8 decision=deny severity_level=5
```

The response should contain:

- Event ID
- Detected log profile
- Parsed fields
- OCSF-normalized event
- Validation result
- Traceability information
- Mapping version
- Raw-event SHA-256 hash

A successful response should contain information similar to:

```json
{
  "normalized": {
    "source_endpoint": "192.168.1.20",
    "destination_endpoint": "10.0.0.8",
    "action": "deny",
    "severity": "5"
  },
  "validation": {
    "valid": true
  },
  "traceability": {
    "raw_preserved": true,
    "raw_sha256": "..."
  }
}
```

---

## 24. Test Mapping Versions

Use:

```text
GET /api/v1/adaptation/{source}/versions
```

For example:

```text
GET /api/v1/adaptation/firewall-01/versions
```

This displays the mapping history for the source, including:

- Mapping version
- Field mappings
- Confidence
- Status
- Creation timestamp

A source may contain multiple versions:

```text
Version 1 → archived
Version 2 → active
```

---

## 25. Test Drift Detection

Use:

```text
POST /api/v1/drift/check
```

Provide baseline logs representing the known format and a current log representing the newly observed format.

The endpoint compares the current structure against the baseline and reports whether structural drift has occurred.

Example concept:

```text
Baseline:

source_address=192.168.1.20
destination_address=10.0.0.8
decision=deny


Current:

src_addr=192.168.1.20
dst_addr=10.0.0.8
action=deny
```

The changed field structure should be detected as potential format drift.

---

## 26. Test Adaptive Mapping

Use the adaptation workflow endpoint:

```text
POST /api/v1/adaptation/workflow
```

Provide:

- `source`
- `baseline_logs`
- `current_log`

The workflow performs the adaptation process:

```text
Baseline Logs
      ↓
Baseline Profile
      ↓
Current Log
      ↓
Drift Analysis
      ↓
Candidate Mapping
      ↓
Confidence Calculation
      ↓
New Mapping Version
```

The resulting candidate mapping can then be inspected before activation.

---

## 27. Activate a Mapping Version

After reviewing a candidate mapping, use:

```text
POST /api/v1/adaptation/{source}/activate/{version}
```

Example:

```text
POST /api/v1/adaptation/firewall-01/activate/2
```

The selected version becomes:

```text
ACTIVE
```

while the previously active version becomes:

```text
ARCHIVED
```

---

## 28. Verify the New Mapping

Run the processing endpoint again using a log matching the newly adapted format.

```text
POST /api/v1/process
```

Verify that the normalized output now uses the newly activated mapping.

Check the response for:

```json
{
  "mapping_version": 2
}
```

This confirms that the mapping version is not merely stored in the database but is actually being used by the processing pipeline.

---

## 29. Complete Test Flow

For a complete demonstration of the current LOGVANTA implementation, use the following sequence:

```text
 1. Start FastAPI
 2. Open /docs
 3. Process a known firewall log
 4. Inspect profiling + normalization
 5. Check mapping versions
 6. Submit a changed log format
 7. Run drift detection
 8. Run adaptation workflow
 9. Inspect generated mapping version
10. Activate the required version
11. Process the new-format log
12. Verify normalized output + mapping version
13. Verify traceability + SHA-256
```

This demonstrates the currently implemented LOGVANTA pipeline from **raw log ingestion through adaptive mapping, normalization, validation, and traceability**.

---

## Project

**LOGVANTA — Adaptive Universal Log Pre-Processing Framework**

Built for the **Universal Log Pre-processing Framework** problem statement (Smart India Hackathon 2026 — Problem Statement ID 26156, National Technical Research Organisation).
