## 🛠️ Prerequisites

Before running the agent, ensure you have the following installed and configured:

* **Python 3.11+**: Required for Google ADK compatibility.
* **Google Cloud Project**:
    * Enable **Vertex AI API**.
    * Generate a **Gemini 2.0 API Key**.
* **Google Agent Development Kit (ADK)**:
    * Follow the [ADK installation guide](https://google.github.io/adk-docs/).
* **Hardware (Optional)**:
    * Microphone & Camera (for audio/vision threat detection).
    * GPS-enabled device (for location tracking).

---

## 🏗️ Architecture

The system follows a 7-agent architecture orchestrated by a central decision engine.

![AI Guardian Architecture](https://drive.google.com/file/d/1aldhUkiT3WUCxFHAU8WDx5ehZUgkIWd3/view?usp=sharing)

**Workflow Overview:**
1.  [cite_start]**Ingestion**: Fuses inputs from Voice, Text, and Sensors.
2.  [cite_start]**Analysis**: The **LLM Agent** and **Danger Classifier** assess intent and risk.
3.  [cite_start]**Decision**: The **Agent Selector** activates specific tools (e.g., `trigger_emergency_alert`).
4.  [cite_start]**Action**: Outputs include encrypted incident logs and emergency notifications.
