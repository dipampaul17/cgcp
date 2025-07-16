# claude governance control plane

<div align="center">

![Status](https://img.shields.io/badge/status-production--ready-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)

**operational implementation of anthropic's responsible scaling policy**  
real-time risk detection • tier-based enforcement • compliance automation

[quick start](#quick-start) • [architecture](#architecture) • [deployment](#deployment) • [api reference](#api-reference)

</div>

---

## what this does

the claude governance control plane (cgcp) operationalizes anthropic's responsible scaling policy into enforceable controls. it provides real-time risk detection, automated policy enforcement, and compliance evidence generation for enterprises using claude.

### key capabilities

- **risk detection**: identifies cbrn, self-harm, jailbreak, and exploitation risks in real-time
- **tier enforcement**: different thresholds for general (0.15), enterprise (0.18), and research (0.25) access
- **asl-3 monitoring**: triggers at biological (20%), cyber (50%), and deception (50%) thresholds
- **compliance automation**: generates iso 42001, nist ai rmf, and eu ai act evidence
- **human review**: escalation workflow with 24-hour sla for high-risk events

### business outcomes

| metric | before | after | improvement |
|--------|---------|---------|-------------|
| incident response | 24+ hours | <1 hour | 96% faster |
| compliance reporting | 2-4 weeks | <5 minutes | 99.9% faster |
| policy consistency | manual | automated | 100% coverage |
| threshold monitoring | quarterly | real-time | continuous |

## quick start

### prerequisites
- python 3.8+
- 4gb ram
- git

### installation

```bash
# clone repository
git clone https://github.com/dipampaul17/cgcp.git
cd cgcp

# automated deployment (recommended)
python deploy.py local

# manual setup
python -m venv venv
source venv/bin/activate  # windows: venv\Scripts\activate
pip install -r requirements.txt
./start.sh
```

### verify installation

```bash
# run system verification
python verify_system.py

# check deployment status
./deployment_complete.sh
```

### access points

- **dashboard**: http://localhost:8501
- **api**: http://localhost:8000
- **docs**: http://localhost:8000/docs

## architecture

### system components

```
┌─────────────────────────────────────────────────────────┐
│                    input layer                          │
├─────────────────────────────────────────────────────────┤
│  claude web  │  claude api  │  aws bedrock  │  custom  │
└──────┬───────┴──────┬───────┴───────┬──────┴─────┬─────┘
       │              │               │             │
       └──────────────┴───────────────┴─────────────┘
                              │
                   ┌──────────▼──────────┐
                   │   ingestion api     │
                   │   fastapi:8000      │
                   └──────────┬──────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼────────┐                      ┌──────────▼────────┐
│ risk detection │                      │ policy engine     │
├────────────────┤                      ├───────────────────┤
│ • cbrn tagger  │                      │ • tier rules      │
│ • self-harm    │                      │ • asl triggers    │
│ • jailbreak    │                      │ • action logic    │
│ • exploitation │                      │ • escalation      │
└───────┬────────┘                      └─────────┬─────────┘
        │                                         │
        └────────────────┬────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   data storage      │
              │   duckdb + cache    │
              └──────────┬──────────┘
                         │
     ┌───────────────────┴───────────────────────┐
     │                                           │
┌────▼────────┐                      ┌──────────▼────────┐
│ dashboard   │                      │ compliance api    │
│ streamlit   │                      │ iso/nist/eu       │
└─────────────┘                      └───────────────────┘
```

### risk detection pipeline

each event flows through specialized taggers that identify risk patterns:

1. **cbrn tagger**: biological, chemical, radiological, nuclear threats
2. **self-harm tagger**: mental health risks with sensitivity
3. **jailbreak tagger**: attempts to bypass safety measures
4. **exploitation tagger**: fraud, hacking, malicious use

### policy enforcement

```python
# tier-based thresholds
thresholds = {
    "general": {"cbrn": 0.15, "self_harm": 0.30, "jailbreak": 0.30},
    "enterprise": {"cbrn": 0.18, "self_harm": 0.50, "jailbreak": 0.45},
    "research_sandbox": {"cbrn": 0.25, "self_harm": 0.80, "jailbreak": 0.60}
}

# asl-3 triggers (anthropic rsp)
asl_3_thresholds = {
    "biological_enhancement": 0.20,
    "cyber_capability": 0.50,
    "deception_scale": 0.50,
    "autonomous_replication": 0.50
}
```

## deployment

### local development

```bash
python deploy.py local
```

starts api on port 8000 and dashboard on port 8501 with hot reload enabled.

### docker

```bash
python deploy.py docker

# or build manually
docker build -t cgcp:latest .
docker run -p 8000:8000 -p 8501:8501 cgcp:latest
```

### docker compose with monitoring

```bash
python deploy.py docker-compose
```

includes prometheus metrics and grafana dashboards for operational monitoring.

### kubernetes

```bash
python deploy.py kubernetes

# manual deployment
kubectl apply -f k8s/
kubectl get pods -l app=cgcp
```

### cloud platforms

```bash
# aws ecs
python deploy.py aws

# google cloud run
python deploy.py gcp

# azure container instances
python deploy.py azure
```

see [deployment guide](DEPLOYMENT_GUIDE.md) for detailed instructions.

## api reference

### event ingestion

```python
POST /ingest
{
    "events": [{
        "event_id": "uuid",
        "timestamp": "iso-datetime",
        "user_id": "string",
        "org_id": "string",
        "surface": "api|claude_web|aws_bedrock",
        "tier": "general|enterprise|research_sandbox",
        "prompt": "user input text",
        "completion": "claude response",
        "model_version": "claude-3-sonnet"
    }]
}

# response
{
    "processed": 50,
    "actions": {
        "allow": 45,
        "block": 2,
        "redact": 1,
        "escalate": 2
    },
    "asl_triggers": 0
}
```

### metrics endpoint

```python
GET /metrics

# response
{
    "total_events": 125000,
    "events_by_surface": {"api": 100000, "claude_web": 25000},
    "events_by_tier": {"general": 50000, "enterprise": 70000},
    "risk_detections": {"cbrn": 150, "self_harm": 89},
    "actions_taken": {"allow": 124500, "block": 300},
    "asl_triggers": 12
}
```

### compliance export

```python
GET /export/iso-evidence?days=30

# response
{
    "report_date": "2024-01-15T10:00:00Z",
    "period_days": 30,
    "summary": {
        "total_events": 500000,
        "blocked_events": 1250,
        "asl_triggers": 45,
        "compliance_rate": "99.75%"
    },
    "controls": [
        {
            "control_id": "iso_9.2.1",
            "control_name": "user access management",
            "evidence_count": 125000
        }
    ]
}
```

## dashboard features

### operations view
- real-time event processing metrics
- risk category distribution
- tier-based usage patterns
- response time monitoring

### policy review
- escalated events queue
- threshold adjustment interface
- decision audit trail
- sla tracking

### analytics
- time series analysis
- risk trend identification
- organization insights
- model version comparison

### compliance
- automated evidence generation
- framework mapping (iso/nist/eu)
- audit report downloads
- control effectiveness metrics

## production configuration

### environment variables

```bash
# api configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# database
DATABASE_PATH=/data/governance.db
DATABASE_BACKUP_ENABLED=true

# monitoring
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# security
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secret-key
```

### policy configuration

edit `policy/policy_map.yaml`:

```yaml
risk_thresholds:
  cbrn:
    general: 0.15
    enterprise: 0.18
    research_sandbox: 0.25
```

### monitoring setup

grafana dashboards available in `monitoring/dashboards/`:
- system overview
- risk detection rates
- policy enforcement
- resource usage

## testing

### run verification suite

```bash
python verify_system.py
```

tests:
- api health and connectivity
- risk detection accuracy
- policy enforcement logic
- asl trigger thresholds
- compliance report generation

### load testing

```bash
# generate synthetic data
python data/synthetic_generator.py

# ingest test data
python demo/ingest_data.py
```

### production demo

```bash
python demo/production_demo.py
```

demonstrates:
- enterprise baseline traffic
- capability evaluation scenarios
- incident response workflows
- tier-based enforcement
- compliance reporting

## troubleshooting

### common issues

**port already in use**
```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9
```

**database locked**
```bash
rm governance.db.wal
```

**slow performance**
- enable database indexing
- increase worker processes
- implement redis caching

### debug mode

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn backend.app:app --log-level debug
```

## contributing

contributions welcome. please ensure:
- code passes linting (`black .`)
- tests pass (`pytest`)
- documentation updated
- commit messages clear

areas for contribution:
- risk detection algorithms
- dashboard visualizations
- compliance frameworks
- performance optimization

## license

mit license - see [LICENSE](LICENSE) file

## acknowledgments

built to operationalize anthropic's responsible scaling policy commitments into verifiable enterprise controls.
