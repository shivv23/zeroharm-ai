# ZeroHarm AI — Presentation Deck

## Slide 1: Title
**ZeroHarm AI: AI-Powered Industrial Safety Intelligence for Zero-Harm Operations**
- Tagline: "Sensors already exist. We connect the dots before people die."
- Team Name / Logo
- ET AI Hackathon 2026

## Slide 2: The Problem — A National Crisis
- **6,500+** fatal workplace accidents in FY2023 (DGFASLI)
- **January 2025**: 8 workers died at Visakhapatnam Steel Plant — entrapped gases ignited in coke oven battery
- **The root cause**: Warning signals from gas pressure sensors existed, but no intelligence layer connected readings to operational decisions
- **60%** of large plants rely on manual handoffs between digital safety tools (FICCI 2024)
- **The pattern**: Data present, but unacted upon — repeats across Indian heavy industry

## Slide 3: Why Existing Solutions Fail
- Single-sensor threshold alarms → high false positive rate → alarms silenced
- Disconnected systems: SCADA, permits, maintenance, CCTV — no unified picture
- Manual permit-to-work review — no dynamic cross-referencing with real-time conditions
- Reaction time measured in hours — by then, the damage is done
- **Compound risks go undetected**: Hot work + gas accumulation + maintenance bypass = explosion

## Slide 4: ZeroHarm AI — The Solution
**A unified AI intelligence layer that:**
- Fuses data from IoT sensors, SCADA, permit logs, CCTV, and shift records
- Detects compound risk conditions that no single sensor would flag alone
- Triggers preemptive interventions before escalation
- Orchestrates coordinated emergency response when needed

**Key differentiator**: Detects *combinations* of risks, not just individual threshold breaches

## Slide 5: Architecture (4-Agent System)
[Show architecture diagram from docs/architecture.md]

1. **Sensor Monitor Agent** — Tracks 80+ sensors across 10 plant zones
2. **Permit Activity Agent** — Analyzes active permits, detects overlaps
3. **Maintenance Status Agent** — Equipment in bypass/maintenance mode
4. **Fusion Supervisor** — Combines all 3, scores risks, prioritizes alerts

**Supporting Systems:**
- Knowledge Graph (equipment↔permit↔risk↔regulatory)
- RAG Pipeline (regulatory document compliance)
- Emergency Response Orchestrator (autonomous dispatch)
- Incident Pattern Intelligence (historical analysis)

## Slide 6: Demo — Compound Risk Detection (Crown Jewel)
**Scenario**: Confined space entry permit in Coke Oven Battery
- O₂ sensor drops to 18.1% (warning but not critical individually)
- LEL sensor rises to 14% (warning but not critical individually)
- **Together: COMPOUND RISK CRITICAL**
- ZeroHarm AI: "IMMEDIATE SUSPENSION: Unsafe oxygen with flammable atmosphere during confined space entry"
- **Result**: Entry stopped before fatality

**Impact**: Catches the Vizag Steel Plant scenario — gas pressure warnings + maintenance activity → explosion prevented

## Slide 7: Demo — Geospatial Safety Heatmap
- Real-time risk overlay on plant layout
- Zone colors: Green → Amber → Red → Crimson
- Sensor dots with live readings
- Permit indicator badges on zones
- Click any zone → drill into contributing factors
- **Effect**: Safety officers get situational awareness across the entire facility in seconds

## Slide 8: Demo — Emergency Response Orchestrator
- One-click emergency trigger (Gas Leak / Fire / Explosion / Medical)
- Autonomous multi-channel dispatch: Sirens, Slack, Telegram, SMS
- Evacuation protocol with radius-based zone clearance
- Emergency shutdown sequence initiation
- Rescue team dispatch with timeline tracking
- **Regulatory-compliant incident report generated in seconds**
- **10 minutes of chaos → 10 seconds of coordinated response**

## Slide 9: Business Impact & ROI
**Safety Impact:**
- Catches compound risks hours before critical threshold
- Reduces false negative rate — the metric that saves lives
- Vicinity of Vizag-like events: averted

**Financial ROI:**
- Avg cost per major industrial accident: ₹2-5 Cr
- Avg cost per fatal accident (compensation + penalties + shutdown): ₹10-25 Cr
- ZeroHarm AI cost: fraction of one incident
- **ROI: 50x+ for any plant with >500 workers**

**Scalability:**
- Steel, Oil & Gas, Chemicals, Mining, Power — every heavy industry
- New plant = new config (zones, sensors, permits), not new code
- Modular agent architecture — add new sensor types as new agents

## Judging Criteria Map

| Criteria | Weight | How ZeroHarm AI Wins |
|----------|--------|---------------------|
| Innovation | 25% | Compound risk fusion (multi-condition correlation) is genuinely novel. No existing product does this. |
| Business Impact | 25% | 6,500+ lives lost/year. Each prevention saves ₹2-25 Cr. ROI is immediate and undeniable. |
| Technical Excellence | 20% | Multi-agent architecture, KG, RAG, real-time geospatial, autonomous orchestration. Full-stack depth. |
| Scalability | 15% | Modular agent design. New zone = new config, not new code. Any heavy industry. |
| User Experience | 15% | Geospatial heatmap is intuitive. One-click emergency. Compliance reports auto-generated. |

## Demo Script (3 Minutes)

| Time | Screen | Narration |
|------|--------|-----------|
| 0:00-0:30 | Static plant map (all green) | "Every Indian steel plant has sensors. Every plant has permits. But they never talk to each other. Eight workers died at Vizag because of exactly this gap. Meet ZeroHarm." |
| 0:30-1:00 | Compound risk: O₂ dropping, LEL rising, permit overlapping | "Watch: a confined space entry is active in the Coke Oven Battery. The O₂ sensor drops to 18.1%. The LEL sensor reads 14%. Individually? Just warnings. Together — a death sentence." |
| 1:00-1:30 | Heatmap zone turns red, alert fires | "The compound risk engine catches what no single sensor could. The zone turns red. The permit intelligence agent fires a suspension order before the worker enters." |
| 1:30-2:00 | Permit conflict detected | "Here the Permit Intelligence Agent catches a hot work permit issued 20m from a gas holder with rising LEL — and blocks it instantly." |
| 2:00-2:30 | Emergency trigger demo | "But if the worst happens? One click. Sirens dispatch. Evacuation initiated. Rescue team paged. And a regulator-ready incident report generated in 10 seconds, not 10 hours." |
| 2:30-3:00 | Architecture + close | "Multi-agent AI over existing infrastructure. No new sensors. No forklift upgrade. Connects the dots that Vizag couldn't — and saves lives." |

## Team Competencies Required
- Full-stack: React + FastAPI + Python
- AI/ML: LLM integration, RAG, multi-agent systems
- Data: Real-time streaming, WebSocket architecture
- Domain: Industrial safety (OISD/DGMS/Factory Act knowledge)
- Design: Clean UI with geospatial visualization

## Key Technical Decisions
1. **Parallel multi-agent orchestration** — lightweight Python implementation, no heavy frameworks
2. **Synthetic data generator** — self-contained, reproducible demo scenarios
3. **In-memory KG (NetworkX)** — no Neo4j dependency, zero setup
4. **Embedded regulatory docs** — RAG works offline, no API calls needed
5. **Simulated WebSocket updates** — realistic real-time feel without actual IoT hardware
