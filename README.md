# 🛡️ Astraea Agent

The **Astraea Agent** is a lightweight, high-performance Python utility designed to automate server maintenance and patch management. While it functions as a standalone automation tool, it is designed to integrate seamlessly with the [Astraea Webserver](https://github.com/DefOnslaught/Astraea-Webserver).

---

## 🏗️ Overview

The agent monitors your Linux environment, executes patch cycles, and logs system telemetry, providing a secure, automated way to keep your infrastructure up to date across a wide range of distributed Linux environments.

---

## 📋 Requirements

Ensure your host meets the following prerequisites:

| Component | Minimum Requirement |
| :--- | :--- |
| **Python** | **3.10+** (Required) |
| **Tools** | `python3-venv`, `python3-pip`, `curl` |
| **Supported OS** | Ubuntu 22.04+, Debian, Fedora, CentOS Stream, RHEL 8+ |

---

## ⚙️ Installation

### Option A: Webserver-Managed (Recommended)

Generate the installation script directly from your [Astraea Webserver](https://github.com/DefOnslaught/Astraea-Webserver) dashboard. This script automatically handles API keys, environment variables, and scheduling.

### Option B: Manual Standalone Installation

If you are setting up the agent manually, follow these steps:

1. **Clone or Download** the repository to `/opt/Astraea-Agent`.
2. **Install System Dependencies:**
   - Ensure `python3` (3.10+) and `python3-venv` are installed via your package manager (`apt` or `dnf`).
3. **Configure Environment:**
   - Copy the configuration: `cp .env_example .env`
   - Edit the `.env` file to define your `API_KEY`, `BASE_URL`, and scheduling preferences.

> **Environment Setup Tips:**
>
> - **Webserver Integration:** Fill in `API_KEY` and `BASE_URL` to enable remote reporting and centralized patching control.
> - **Standalone Mode:** Leave `API_KEY` and `BASE_URL` blank to run the agent locally without external synchronization.
> - **Core Settings:** The settings in `core/settings.py` are pre-configured for standard operations and do not require manual modification.

---

## 🚀 Usage

### Standalone Execution

If you are running the agent manually without the Astraea Webserver orchestration, execute:

```bash
sudo /usr/bin/python3 /opt/Astraea-Agent/core/initialize.py
```

### Logging

The agent maintains activity records in the `logs/` directory for troubleshooting and auditing:

- `initialize.log`: Deployment and setup events.
- `patching.log`: Real-time execution logs for patching cycles.

---

## 📂 File Structure

- `/core/settings.py`: Internal configuration constants.
- `/logs/`: Directory containing `initialize.log` and `patching.log`.
- `.env`: Sensitive environment variables (API keys, URLs).

---

*For centralized fleet management, please refer to the [Astraea Webserver Repository](https://github.com/DefOnslaught/Astraea-Webserver).*
