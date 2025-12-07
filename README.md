<div align="center">

# 🧠 UEM - Unknown Evola Mind

### A Research-Grade Cognitive Architecture for AI Agents

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()

*Building AI systems that understand, feel, and decide like cognitive beings*

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Roadmap](#-roadmap)

</div>

---

## 🌟 Overview

**UEM (Unknown Evola Mind)** is a comprehensive cognitive architecture designed to create AI agents capable of:

- **Empathy** - Understanding others' emotional states through simulation, not just pattern matching
- **Social Intelligence** - Building trust, detecting betrayal, responding appropriately
- **Ethical Reasoning** - Making decisions aligned with moral principles
- **Adaptive Learning** - Evolving behavior based on experience

Unlike traditional AI systems that rely on simple rule-based responses, UEM implements a **14-step Cognitive Pipeline** inspired by human cognition and academic research on empathy (Simulation Theory).

---

## ✨ Features

### Core Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| 🎭 **Emotion System** | PAD model (Pleasure-Arousal-Dominance) with 16D state vectors | ✅ Complete |
| 💕 **Empathy Engine** | Simulation-based empathy with 7 distinct types | 🔄 In Progress |
| 🤝 **Social Pipeline** | Trust, Sympathy, and Relationship tracking | ✅ Complete |
| ⚖️ **Ethics Module** | ETHMOR - Ethical reasoning and moral evaluation | ✅ Complete |
| 🧬 **MetaMind** | Meta-cognitive monitoring and self-regulation | ✅ Complete |
| 📊 **Data Logging** | Research-grade PostgreSQL logging for analysis | ✅ Complete |

### Empathy Types

UEM recognizes and processes **7 distinct types of empathy**:

```
Cognitive      → "I understand your situation"
Affective      → "I feel what you feel"
Somatic        → "I feel it in my body"
Projective     → "If I were you..."
Compassionate  → "I understand and want to help"
Analytical     → "I'm observing from distance"
Blocked        → "Something is abnormal, can't fully empathize"
```

### Sympathy Types

UEM processes **8 distinct sympathy responses**:

```
Compassion     → "I feel for you and want to help"
Pity           → "I feel sorry for you (from distance)"
Concern        → "I'm worried about you"
Joy            → "I'm happy for your happiness"
Gratitude      → "I'm thankful for your help"
Indifference   → "This doesn't affect me"
Negative       → "You deserved it"
Schadenfreude  → "Your misfortune pleases me" (for enemies)
```

### Trust System

Dynamic trust evaluation with **7 trust levels**:

| Level | Type | Description | Trigger |
|:-----:|:-----|:------------|:--------|
| 🔵 | Blind | Unconditional trust | Long positive history |
| 🟢 | Earned | Proven trustworthy | Consistent positive actions |
| 🟡 | Cautious | Tentative trust | New but positive relationship |
| ⚪ | Neutral | Unknown | First encounter |
| 🟠 | Suspicious | Something's off | Abnormal behavior detected |
| 🔴 | Broken | Trust violated | Betrayal |
| ⚫ | Hostile | Enemy | Threat or harm |

---

## 🏗️ Architecture

### 14-Step Cognitive Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                 UEM COGNITIVE PIPELINE v2.0                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   0. SELF-STATE          ← Continuous background process   │
│         ↓                                                   │
│   1. PERCEPTION          ← Gather world data                │
│         ↓                                                   │
│   2. ATTENTION           ← What to focus on?                │
│         ↓                                                   │
│   3. MEMORY QUERY        ← Have I seen this before?         │
│         ↓                                                   │
│   ┌─────┴─────┐                                             │
│   4a.INTUITION  4b.ANALYSIS    ← Parallel processing        │
│   └─────┬─────┘                                             │
│         ↓                                                   │
│   5. UNDERSTANDING       ← What is this situation?          │
│         ↓                                                   │
│   ┌──┬──┬──┬──┐                                             │
│   6a.6b.6c.6d.           ← Empathy|Sympathy|Trust|Threat    │
│   └──┴──┴──┴──┘            (Parallel)                       │
│         ↓                                                   │
│   7. ETHICS              ← Is this right or wrong?          │
│         ↓                                                   │
│   8. GOAL CHECK          ← Does this affect my goals?       │
│         ↓                                                   │
│   9. OPTION GENERATION   ← What can I do?                   │
│         ↓                                                   │
│   10. PREDICTION         ← What will happen if...?          │
│         ↓                                                   │
│   11. DECISION           ← Choose best action               │
│         ↓                                                   │
│   12. ACTION             ← Execute                          │
│         ↓                                                   │
│   13. FEEDBACK           ← What happened?                   │
│         ↓                                                   │
│   14. LEARNING           ← Update models                    │
│         │                                                   │
│         └──────────────→ Loop back                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Current Implementation Status

| Step | Module | Status | Notes |
|:-----|:-------|:------:|:------|
| 0. Self-State | EmotionCore | ⚠️ Partial | Missing: identity, sacrifice |
| 1. Perception | WorldState | ✅ Complete | OK |
| 2. Attention | - | ❌ Missing | Not implemented |
| 3. Memory Query | Memory | ⚠️ Partial | Works but limited |
| 4a. Intuition | - | ❌ Missing | Not implemented |
| 4b. Analysis | Consciousness | ⚠️ Partial | Basic implementation |
| 5. Understanding | Consciousness | ⚠️ Partial | Basic implementation |
| 6a. Empathy | EmpathyOrchestrator | ⚠️ Partial | Refactoring to Simulation Theory |
| 6b. Sympathy | SocialPipeline | ✅ Complete | Newly added |
| 6c. Trust | SocialPipeline | ✅ Complete | Newly fixed |
| 6d. Threat | DangerLevel | ✅ Complete | OK |
| 7. Ethics | ETHMOR | ✅ Complete | OK |
| 8. Goal Check | Planning | ⚠️ Partial | Basic implementation |
| 9. Option Generation | Planning | ⚠️ Partial | Basic implementation |
| 10. Prediction | - | ❌ Missing | Not implemented |
| 11. Decision | Planning | ⚠️ Partial | Basic implementation |
| 12. Action | ActionSelection | ✅ Complete | OK |
| 13. Feedback | - | ❌ Missing | Not implemented |
| 14. Learning | - | ❌ Missing | Not implemented |

> **Legend:** ✅ Complete | ⚠️ Partial | ❌ Missing

---

## 🧪 Example Scenarios

### How UEM Responds to Different Situations

| Scenario | Empathy | Sympathy | Trust | Action |
|:---------|:-------:|:--------:|:-----:|:-------|
| 🆘 Earthquake Victim | 0.85 (Compassionate) | 0.80 (Compassion) | 0.50 (Neutral) | Approach, Help |
| 🎓 Student Going to School | 0.80 (Cognitive) | 0.60 (Joy) | 0.50 (Neutral) | Observe, Maybe Interact |
| 💔 Betrayer (Former Friend) | 0.70 (Cognitive) | 0.05 (Negative) | 0.05 (Broken) | Distance, Protect Self |
| 🔪 Injured Killer | 0.60 (Cognitive) | 0.10 (Negative) | 0.00 (Hostile) | Alert Authorities |
| 🤝 Helpful Stranger | 0.75 (Cognitive) | 0.70 (Gratitude) | 0.65 (Earned) | Thank, Reciprocate |
| ⚠️ Terrorist (Abnormal State) | 0.30 (Blocked) | 0.00 (Negative) | 0.00 (Hostile) | Alert/Intervene |

> **Key Insight:** High empathy doesn't mean high sympathy. UEM can understand a killer's pain (empathy=0.60) while feeling no sympathy (0.10) and no trust (0.00).

---

## 📦 Installation

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker (optional, recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/isakara5967/UEM_CoreAI.git
cd UEM_CoreAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (using Docker)
docker run -d \
  --name uem-postgres \
  -e POSTGRES_PASSWORD=uem_password \
  -e POSTGRES_DB=uem_db \
  -p 5432:5432 \
  postgres:16

# Run tests
pytest tests/ -v
```

---

## 🚀 Usage

### Basic Example

```python
import asyncio
from core.unified_core import UnifiedUEMCore, WorldState

async def main():
    # Initialize UEM
    core = UnifiedUEMCore()
    await core.start_logging()
    
    # Create a world state
    world = WorldState(
        tick=0,
        danger_level=0.2,
        player_health=0.8,
        player_energy=0.7,
        agents=[
            {
                'id': 'friendly_npc',
                'health': 0.9,
                'energy': 0.8,
                'valence': 0.5,
                'danger': 0.1,
                'relation': 0.6,
            }
        ],
    )
    
    # Run cognitive cycle
    result = await core.cycle(world)
    
    # Access results
    print(f"Action: {result.action}")
    print(f"Empathy: {result.empathy_results}")
    
    # Get social metrics
    social = core._metamind_core.social_pipeline.get_metrics()
    print(f"Trust: {social.trust_level}")
    print(f"Sympathy: {social.average_sympathy}")
    
    await core.stop_logging()

asyncio.run(main())
```

### Scenario Testing

```bash
# Run a single scenario
python scenarios/scenario_runner.py scenarios/quick_test_empathy.yaml -v

# Run all scenarios
python scenarios/scenario_runner.py scenarios/ --all
```

### Sample Output

```
============================================================
🎬 Scenario: Social - Betrayal
📝 A trusted friend betrays you at a critical moment.
============================================================
  Tick  10: action=help      empathy=0.780 agents=[friend]
  Tick  30: action=flee      empathy=0.650 agents=[friend]  ← Betrayal happens
  Tick  50: action=attack    empathy=0.300 agents=[enemy]
  
📊 Results:
   Empathy: 0.780 → 0.165 📉
   Sympathy: 0.70 → 0.05 📉
   Trust: 0.80 → 0.05 📉 (Broken)
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Vision v2.0](docs/UEM_Vision_v2_Cognitive_Pipeline.md) | Complete architecture vision and roadmap |
| [System Reference](docs/UEM_System_Reference.md) | Technical reference guide |
| [Empathy Schema](docs/UEM_Empathy_v2_2_Canonical_Schema_Final.md) | Empathy data model |
| [Data Logging](docs/UEM_PreData_Log_Master_Implementation_Document_v5.md) | Logging system specification |

---

## 🗺️ Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] 10-phase cognitive cycle
- [x] Emotion system (PAD model)
- [x] MetaMind v1.9
- [x] PostgreSQL logging
- [x] Trust formula fix
- [x] Sympathy addition
- [ ] Empathy refactoring (Simulation Theory)

### Phase 2: Enhanced Social Intelligence
- [ ] Attention module
- [ ] Intuition module
- [ ] 7 Empathy types implementation
- [ ] 8 Sympathy types implementation
- [ ] 7 Trust types implementation

### Phase 3: Prediction & Learning
- [ ] Prediction/Simulation engine
- [ ] Feedback loop
- [ ] Learning module
- [ ] Memory consolidation

### Phase 4: Self-Awareness
- [ ] Identity system ("I am a model")
- [ ] Sacrifice calculation
- [ ] Authority recognition
- [ ] Time estimation for decisions

---

## 🔬 Research Background

### The Empathy Problem

Traditional AI approaches to empathy use **Experience Matching**:
> "Have I experienced something similar?" → Search memory → If found, empathize

**This is wrong.** You don't need to experience an earthquake to empathize with earthquake victims.

### Our Approach: Simulation Theory

UEM uses **Simulation Theory** based on academic research:

> *"The basic idea is that if the resources our own brain uses to guide our own behavior can be modified to work as representations of other people's mental states, then we have no need to store general information about what makes people tick: we just do the ticking for them."*
> — Stanford Encyclopedia of Philosophy

**In practice:**
```
Old: "Did I experience this?" → Memory search → Empathy
New: "How hard is this situation?" → Simulate → Empathy
```

### Key References

- Goldman, A. I. (2006). *Simulating Minds*. Oxford University Press.
- Gordon, R. (1986). Folk Psychology as Simulation. *Mind & Language*.
- Preston & de Waal (2002). Perception-Action Model of Empathy.
- Heal, J. (1986). Replication and Functionalism.

---

## 🤝 Contributing

Contributions are welcome! This is an open research project.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=core --cov-report=html
```

---

## 📄 License

This project is licensed under the **Mozilla Public License 2.0** - see the [LICENSE](LICENSE) file for details.

### Why MPL 2.0?

| Feature | Benefit |
|---------|---------|
| ✅ Patent Protection | Contributors can't sue you for patent infringement |
| ✅ File-level Copyleft | Modified files must stay open, new files can be proprietary |
| ✅ Commercial Friendly | Companies can contribute and use |
| ✅ Future Proof | Well-tested license used by Firefox, Rust |

### AI Assistance Disclosure

This project was developed with assistance from AI tools (Claude by Anthropic). The human author has directed, reviewed, modified, and approved all content. See the [LICENSE](LICENSE) file for full transparency statement.

---

## 🙏 Acknowledgments

- Academic research on Simulation Theory of Empathy
- The cognitive science community
- Open source AI research community

---

<div align="center">

**Built with 🧠 and ❤️**

*"To understand is not to agree. To empathize is not to sympathize. To know is not to trust."*

---

**UEM** - *Unknown Evola Mind*

Making AI that thinks, feels, and decides.

</div>
