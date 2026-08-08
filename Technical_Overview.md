# FireVolt Green — Technical Overview

*A detailed walkthrough of how the prototype works, the engineering decisions behind it, and the skills it demonstrates.*

This document is written for anyone evaluating the project from a technical or hiring perspective — it goes beyond the README to explain **why** the system is built the way it is, not just **what** it contains.

---

## 1. Problem Framing

Every harvest season in North India, farmers burn leftover crop stubble in open fields to quickly clear land for the next planting cycle. This is fast and free for the farmer, but it comes at a steep external cost: seasonal air pollution across entire regions, loss of soil nutrients, and a completely wasted biomass resource.

Any viable alternative has to satisfy three constraints simultaneously, or farmers simply won't adopt it:

1. **It must be at least as fast/cheap as burning**, or come with a clear financial upside.
2. **It must not require large upfront infrastructure** most small/marginal farmers can't afford.
3. **It must produce something farmers can use or sell**, not just "be better for the environment."

FireVolt Green's design directly targets these three constraints: the vehicle mobile-processes stubble in the field, generates electricity as a byproduct (usable for on-farm charging or resale), and produces soot that can be sold as an ink feedstock — converting a disposal problem into a small revenue stream.

---

## 2. System Architecture at a Glance

```
                     ┌─────────────────────────┐
   Crop Stubble ───► │  Combustion Chamber      │
                     │  (controlled burn)       │
                     └───────────┬─────────────┘
                                 │ heat
                                 ▼
                     ┌─────────────────────────┐
                     │  TEG Array (12–16 units) │──► Buck Converter ──► Usable DC Power
                     └───────────┬─────────────┘
                                 │ exhaust + soot
                                 ▼
                     ┌─────────────────────────┐
                     │  Filtration Stage        │
                     │  HEPA + Activated Carbon │──► Clean exhaust
                     │  (relay-controlled fan)  │──► Captured soot → Ink feedstock
                     └─────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │  ESP32 Control Unit                          │
   │  - Drives 2× L298N → 4× DC motors (movement) │
   │  - Reads sensors, streams telemetry          │
   │  - Powered by Li-ion battery (+ TEG output)  │
   └─────────────────────────────────────────────┘
                     │
                     ▼
        Streamlit Dashboard (Python, Plotly, Pandas)
        Real-time monitoring of power output, system
        status, and combustion telemetry
```

The system is deliberately split into three loosely-coupled subsystems (motion, power generation, filtration) tied together by a single ESP32 control unit and a web-based dashboard. This separation of concerns mirrors real embedded-systems practice: each subsystem can be tested, debugged, and iterated on independently before integration.

---

## 3. Subsystem Deep Dive

### 3.1 Car Motion Subsystem

**Components:** ESP32, 2× L298N motor drivers, 4× DC motors, Li-ion battery pack

- The ESP32 acts as the central controller, issuing PWM signals to two L298N H-bridge driver boards, each of which independently drives a pair of DC motors — giving the vehicle differential-drive style steering (turn by varying left/right wheel speed).
- Power is drawn from an onboard Li-ion battery pack, which is supplemented by electricity recovered from the TEG array during operation — so the vehicle is, at least partially, self-charging while it works.
- The ESP32 also handles sensor telemetry (e.g., combustion chamber temperature, power output) and streams this data to the dashboard, making motion control and monitoring part of the same firmware loop rather than two disconnected systems.

**Why this matters technically:** driving 4 DC motors from a single low-power microcontroller requires careful current budgeting (H-bridges + motors can exceed what an ESP32's GPIOs can safely source directly), so the L298N boards handle the high-current switching while the ESP32 only handles low-current logic-level control signals.

### 3.2 Heat-to-Electricity Subsystem

**Components:** Combustion chamber, 12–16 TEG modules, custom buck converter

- Crop stubble is burned in an enclosed combustion chamber rather than in the open — this is the core design choice that makes the whole system viable, since it turns an uncontrolled pollution source into a controllable heat source.
- TEG (thermoelectric generator) modules are mounted against the chamber to exploit the **Seebeck effect** — when one side of a TEG is hot (chamber wall) and the other is cool (ambient/heat-sink side), it generates a small DC voltage. Using 12–16 modules in combination scales this up to a usable power level.
- Raw TEG output is low-voltage and unregulated, so a **custom buck converter** steps it down/regulates it into a stable DC rail suitable for charging the Li-ion pack or powering onboard electronics.

**Why this matters technically:** TEG output is highly non-linear and depends on the instantaneous temperature differential across the module, so converting raw TEG output into stable, usable power (rather than just measuring it) is the harder half of the problem — this is where the custom buck converter design work happened, as opposed to using an off-the-shelf regulator.

### 3.3 Filtration & Recovery Subsystem

**Components:** HEPA filter (Ø21 cm), activated carbon filter, relay-controlled exhaust fan

- Combustion exhaust is drawn through a two-stage filter: a HEPA stage to capture particulate matter, followed by an activated carbon stage to adsorb gaseous pollutants/odors.
- A relay-controlled fan actively pulls exhaust through the filtration stack rather than relying on passive airflow, giving the system control over filtration throughput relative to combustion intensity.
- Captured carbon soot — rather than being discarded as filter waste — is collected separately as feedstock for **ink production**, closing the loop from "pollutant" to "product."

**Why this matters technically:** this subsystem is what separates FireVolt Green from a simple biomass burner — the filtration stage isn't just an environmental afterthought, it's a second product-recovery pipeline (soot → ink) layered on top of an emissions-control system.

---

## 4. Software: The Monitoring Dashboard

The dashboard is built with **Streamlit**, chosen for fast iteration on a data-heavy UI without needing a separate frontend framework — appropriate for a hardware-first prototype where the priority is visibility into system state, not a polished consumer-facing product.

- **Plotly** renders real-time graphs of sensor data (e.g., temperature, power output over time), giving an at-a-glance view of combustion and generation performance.
- **Pandas** handles the underlying telemetry data — buffering, transforming, and preparing it for visualization.
- The dashboard consumes telemetry streamed from the ESP32, decoupling "what the hardware is doing" from "how it's displayed" — this means the dashboard can also run in a simulation/demo mode against sample data when hardware isn't connected, which is useful for demos, testing, and portfolio presentation.

---

## 5. Engineering Challenges & Trade-offs

| Challenge | Approach Taken |
|---|---|
| TEG output is low and highly variable | Custom buck converter to regulate and stabilize output before it reaches the battery/electronics |
| High-current motor control from a low-power MCU | Offloaded to L298N H-bridge drivers; ESP32 only sends logic-level control signals |
| Combustion produces both particulates and gases | Two-stage filtration (HEPA + activated carbon) rather than a single filter type |
| Soot is normally filtration waste | Redesigned collection path to treat soot as a recoverable byproduct instead of discarding it |
| Need real-time visibility without a full web stack | Streamlit + Plotly for rapid dashboard development directly in Python |

---

## 6. Skills Demonstrated

This project spans the full stack of a hardware-software product, which is unusual for a single prototype:

- **Embedded systems / firmware:** ESP32-based control of motor drivers and sensor telemetry
- **Power electronics:** Custom buck converter design to condition TEG output
- **Applied physics:** Practical use of the Seebeck effect for waste-heat energy recovery
- **Mechanical/systems integration:** Combining combustion, thermoelectric, and filtration subsystems into one coherent vehicle
- **Data & visualization software:** Python-based real-time dashboard using Streamlit, Plotly, and Pandas
- **Product thinking:** Designing for a specific user (farmers) and economic constraint, not just technical feasibility
- **Sustainability-driven engineering:** Turning a pollution source into a three-part value chain (power, clean air, ink feedstock)

---

## 7. Current Limitations & Future Work

- Stubble feeding into the combustion chamber is currently manual; automating this is the next major mechanical milestone.
- TEG-based power generation is supplementary rather than sufficient for full off-grid operation — battery sizing and TEG array scaling are ongoing considerations.
- The vehicle currently supports remote/manual navigation; autonomous field navigation (e.g., GPS waypoints) is a planned extension.
- Soot-to-ink conversion is currently a collection step rather than an in-vehicle processing pipeline — ink production happens downstream of the vehicle today.

---

## 8. Summary

FireVolt Green demonstrates a working prototype that connects three distinct engineering domains — combustion/thermoelectrics, embedded motor control, and real-time software monitoring — around a single, well-defined problem: turning a harmful agricultural practice into a source of clean(er) power and revenue. The project reflects both hands-on hardware capability and the software skills needed to make that hardware observable and usable.
