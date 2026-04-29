# Agent Architecture Diagrams

One diagram per module. Renders in VS Code's built-in Markdown preview (`Cmd+Shift+V`) and natively on GitHub.

---

## Module 1 — Hello Claude (Single-Shot Agent)

```mermaid
flowchart LR
    A([sample_log.txt]) --> B[hello_claude.py\nrun_agent]
    B --> C{MOCK_MODE?}
    C -- yes --> D([MOCK_RESPONSE\ndict])
    C -- no --> E[ask\nSYSTEM_PROMPT\n+ log content]
    E --> F[(Claude API\nclaude-opus-4-5)]
    F --> G[JSON response]
    G --> D
    D --> H([output/output_module1.json])

    style A fill:#E8F4FD,stroke:#2E74B5
    style H fill:#E8F8E8,stroke:#2E6B2E
    style F fill:#FFF8E1,stroke:#B8860B
```

---

## Module 2 — Structured JSON Agent

```mermaid
flowchart LR
    A([sample_log.txt]) --> B[triage_agent.py\nrun_agent]
    B --> C{MOCK_MODE?}
    C -- yes --> D([MOCK_RESPONSE])
    C -- no --> E[ask\nSYSTEM_PROMPT\n+ log]
    E --> F[(Claude API)]
    F --> G["JSON\n{ summary\n  likely_cause\n  next_step\n  confidence\n  escalate }"]
    G --> D
    D --> H([output/output_module2.json])
    D --> I{escalate?}
    I -- true --> J([GitHub Issue body])

    style A fill:#E8F4FD,stroke:#2E74B5
    style H fill:#E8F8E8,stroke:#2E6B2E
    style J fill:#FFECEC,stroke:#CC3333
    style F fill:#FFF8E1,stroke:#B8860B
```

---

## Module 3 — ReAct Loop Agent

```mermaid
flowchart TD
    A([sample_data.json\nor --scenario text]) --> B[hello_agent.py\nrun_agent]
    B --> C[history = empty]
    C --> D["Build user_msg\n(iter 0: incident context\niter 1+: context + history)"]
    D --> E[ask\nSYSTEM_PROMPT\n+ user_msg]
    E --> F[(Claude API)]
    F --> G["JSON iteration\n{ thought\n  action\n  observation\n  finished\n  confidence\n  recommended_action\n  escalate }"]
    G --> H[Append to history]
    H --> I{finished == true\nor max_iterations?}
    I -- no --> D
    I -- yes --> J([Return history list])
    J --> K([output/output_module3.json])

    style A fill:#E8F4FD,stroke:#2E74B5
    style K fill:#E8F8E8,stroke:#2E6B2E
    style F fill:#FFF8E1,stroke:#B8860B
    style I fill:#F0E8FF,stroke:#6633CC
```

---

## Module 4 — CI/CD Diagnostic Agent

```mermaid
flowchart LR
    subgraph inputs [Log Sources — priority order]
        A1([--log file])
        A2([stdin])
        A3([built-in sample log])
    end

    A1 & A2 & A3 --> B[diagnose.py\nload_log]
    B --> C[ask\nSYSTEM_PROMPT\n+ log content]
    C --> D[(Claude API)]
    D --> E["JSON\n{ error_type\n  root_cause\n  confidence\n  fix: { file, line,\n    original, corrected }\n  post_mortem\n  escalate }"]
    E --> F([output/output_module4.json])
    E --> G{escalate?}
    G -- true --> H([GitHub Issue body])
    G -- false --> I([Auto-patch candidate])

    style inputs fill:#F8F8F8,stroke:#AAAAAA
    style F fill:#E8F8E8,stroke:#2E6B2E
    style H fill:#FFECEC,stroke:#CC3333
    style I fill:#E8F4FD,stroke:#2E74B5
    style D fill:#FFF8E1,stroke:#B8860B
```

---

## Module 5 — Quality Gate + Post-Deploy Monitor

```mermaid
flowchart TD
    subgraph config [Configuration]
        QG([quality-gates.json\n6 thresholds])
    end

    subgraph pre [Pre-Deploy Gate]
        A([sample_data.json\npipeline results]) --> B[triage_agent.py]
        QG --> B
        B --> C[(Claude API)]
        C --> D["APPROVE\nAPPROVE_WITH_CONDITIONS\nHOLD"]
    end

    subgraph post [Post-Deploy Monitor]
        E([live metrics\npost-deploy]) --> F[monitor.py]
        QG --> F
        F --> G[(Claude API)]
        G --> H["rollback_recommended\nseverity: NONE|SCHEDULED|IMMEDIATE\ntrigger, verification_steps"]
    end

    D --> I{decision?}
    I -- APPROVE --> J([Deploy proceeds])
    I -- APPROVE_WITH_CONDITIONS --> K([Deploy + conditions log])
    I -- HOLD --> L([Deploy blocked])

    H --> M{rollback_recommended?}
    M -- "true, IMMEDIATE" --> N([Page on-call now])
    M -- "true, SCHEDULED" --> O([Schedule off-hours rollback])
    M -- false --> P([Monitor continues])

    style config fill:#F8F8F8,stroke:#AAAAAA
    style pre fill:#E8F4FD,stroke:#2E74B5
    style post fill:#E8F8E8,stroke:#2E6B2E
    style L fill:#FFECEC,stroke:#CC3333
    style N fill:#FFECEC,stroke:#CC3333
```

---

## Module 6 — Two-Phase Conversational Observability Agent

```mermaid
flowchart TD
    Q(["Natural-language query\ne.g. 'We are getting paged...'"]) --> P1

    subgraph phase1 [Phase 1 — Route  max_tokens=64]
        P1[phase1_route] --> C1[(Claude API\nROUTING_SYSTEM_PROMPT)]
        C1 --> QT["query_type:\nhealth_check | investigation | incident"]
    end

    subgraph fetch [Data Fetch — 4 endpoints]
        S[observability_mock.py] --> E1([/health])
        S --> E2([/metrics])
        S --> E3([/anomalies])
        S --> E4([/events])
    end

    QT --> P2
    E1 & E2 & E3 & E4 --> P2

    subgraph phase2 [Phase 2 — Analyse  max_tokens=1024]
        P2[phase2_analyse] --> C2[(Claude API\nANALYSIS_SYSTEM_PROMPT)]
        C2 --> R["JSON\n{ status_summary\n  narrative\n  causal_chain[]\n  confidence\n  recommended_action\n  deploy_safe\n  escalate }"]
    end

    R --> OUT([output/output_module6.json])

    style phase1 fill:#E8F4FD,stroke:#2E74B5
    style fetch fill:#F8F8F8,stroke:#AAAAAA
    style phase2 fill:#E8F8E8,stroke:#2E6B2E
    style OUT fill:#E8F8E8,stroke:#2E6B2E
```

---

## Module 7 — Parallel Multi-Agent Orchestrator

```mermaid
flowchart TD
    SD(["sample_data.json\nscenario: no_conflict\npartial_conflict | full_conflict"]) --> ORCH[orchestrator.py\nThreadPoolExecutor]

    subgraph parallel [Parallel execution]
        direction LR
        GATE[run_gate_agent\nGATE_SYSTEM_PROMPT] --> CG[(Claude API)]
        ROLL[run_rollback_agent\nROLLBACK_SYSTEM_PROMPT] --> CR[(Claude API)]
    end

    ORCH --> GATE & ROLL

    CG --> GR["Gate result\n{ decision: APPROVE|\n  APPROVE_WITH_CONDITIONS|HOLD\n  risk_score, escalate }"]
    CR --> RR["Rollback result\n{ rollback_recommended\n  severity: IMMEDIATE|\n  SCHEDULED|OPTIONAL|NONE\n  trigger }"]

    GR & RR --> DC[detect_conflict]

    DC --> C1{"APPROVE\n+\nIMMEDIATE?"}
    C1 -- yes --> HC([HARD_CONFLICT\nSAFETY_FIRST_ESCALATE])
    C1 -- no --> C2{"APPROVE_WITH_CONDITIONS\n+\nSCHEDULED?"}
    C2 -- yes --> SC([SOFT_CONFLICT\nSOFT_ESCALATE])
    C2 -- no --> NC([No conflict\nSYNTHESISE])

    HC & SC & NC --> INT[interpret.py]
    INT --> OUT([rollout_memo\nfor Slack / GitHub])

    style parallel fill:#E8F4FD,stroke:#2E74B5
    style HC fill:#FFECEC,stroke:#CC3333
    style SC fill:#FFF8E1,stroke:#B8860B
    style NC fill:#E8F8E8,stroke:#2E6B2E
```

---

## Module 8 — Capstone 5-Step Platform Agent Pipeline

```mermaid
flowchart TD
    EV(["CI/CD failure event\n--simulate or sample_data.json"]) --> S1

    subgraph step1 [Step 1 — INGEST]
        S1[run_step_ingest\nINGEST_PROMPT] --> C1[(Claude API)]
        C1 --> R1["{ event_type, service\n  failure_stage, severity\n  summary }"]
    end

    R1 --> S2

    subgraph step2 [Step 2 — DIAGNOSE]
        S2["run_step_diagnose\nDIAGNOSE_PROMPT\ncontext: event + ingest"] --> C2[(Claude API)]
        C2 --> R2["{ error_type, root_cause\n  confidence, fix_possible\n  fix_script, post_mortem }"]
    end

    R2 --> S3

    subgraph step3 [Step 3 — GATE]
        S3["run_step_gate\nGATE_PROMPT\ncontext: event + diagnose"] --> C3[(Claude API)]
        C3 --> R3["{ decision, rationale\n  blocking_issues[]\n  risk_score, escalate }"]
    end

    R3 --> S4

    subgraph step4 [Step 4 — FIX OR ESCALATE]
        S4["run_step_fix_or_escalate\nFIX_OR_ESCALATE_PROMPT\ncontext: event + diagnose + gate"] --> C4[(Claude API)]
        C4 --> R4["{ path: AUTO_FIX|ESCALATE\n  reason, auto_fix_script\n  github_issue_title\n  github_issue_body }"]
    end

    R4 --> FX{path?}
    FX -- AUTO_FIX --> FS([fixes/fix_pipeline_id.py])
    FX -- ESCALATE --> GI([GitHub Issue])

    R4 --> S5

    subgraph step5 [Step 5 — REPORT]
        S5["generate_report\nREPORT_PROMPT\ncontext: pipeline_id + all steps"] --> C5[(Claude API)]
        C5 --> R5["{ post_mortem_summary\n  recommendations[] }"]
    end

    R5 --> OUT([output/output_module8_platform_agent.json])

    style step1 fill:#E8F4FD,stroke:#2E74B5
    style step2 fill:#EEF0FF,stroke:#5555CC
    style step3 fill:#F0E8FF,stroke:#8833CC
    style step4 fill:#FFF8E1,stroke:#B8860B
    style step5 fill:#E8F8E8,stroke:#2E6B2E
    style GI fill:#FFECEC,stroke:#CC3333
    style FS fill:#E8F4FD,stroke:#2E74B5
```
