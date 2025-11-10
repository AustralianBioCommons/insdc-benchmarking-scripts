# INSDC Benchmarking Scripts

Benchmarking tools for measuring **INSDC data download performance** across repositories (**ENA**, **SRA**, **DDBJ**) using multiple transfer protocols.

---

## 🚀 Installation

```bash

pip install insdc-benchmarking-scripts
```
⚙️ Quick Start

Copy and edit the example config:

```bash
cp config.yaml.example config.yaml
```
Run an HTTP benchmark:

```bash
benchmark-http --dataset SRR000001 --repository ENA --site nci
```
Run an FTP benchmark:

```bash
benchmark-ftp --dataset SRR000001 --repository ENA --site nci
```
🧠 Features

-   HTTP/HTTPS and FTP benchmarking

-   Automatic CPU, memory, and disk metrics

-   Network latency baselines (ping/traceroute)

-   JSON output aligned with INSDC Benchmarking Schema v1.2

-   Optional API submission via secure HTTP POST

📊 Example Output

```json

{

  "timestamp": "2025-11-06T06:21:33Z",

  "protocol": "http",

  "repository": "SRA",

  "dataset_id": "DRR000001",

  "duration_sec": 92.3,

  "average_speed_mbps": 51.6,

  "status": "success"

}
```
📚 Documentation

Full documentation and examples are available at:

👉 https://github.com/AustralianBioCommons/insdc-benchmarking-scripts

Maintained by: Australian BioCommons

📍 University of Melbourne

🪪 Licensed under Apache 2.0
