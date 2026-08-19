# 📡 WireTapper 

<p align="center">
  <img src="https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/WireTapper.png" alt="WireTapper" />
</p>

> [!NOTE]
> **Wireless OSINT & Signal Intelligence Platform**

WireTapper is a wireless **OSINT aggregator**: it maps and correlates wireless
devices by querying **public third-party databases** — [Wigle](https://wigle.net),
[OpenCellID](https://opencellid.org)/UnwiredLabs, [Shodan](https://www.shodan.io),
and [wpa-sec](https://wpa-sec.stanev.org) — and plotting the results on an
interactive map for investigators, researchers, and security analysts.

WireTapper also surfaces Wi-Fi networks whose credentials are already public in
wpa-sec, using a privacy-preserving **k-anonymity** query (only a short hash
prefix leaves your machine).

> **How it works (and what it is not).** WireTapper reads **historical, public
> database records** — it does **not** perform live RF/SDR capture, packet
> interception, or credential cracking, and device "type" (camera, vehicle, TV,
> …) is *inferred from network names*, not from a dedicated sensor. Use it for
> **lawful, authorized purposes only** — see [`PRIVACY.md`](PRIVACY.md) and
> [`docs/LEGAL.md`](docs/LEGAL.md). Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md).

<p align="center">
  🔗 <strong>Website:</strong>
  <a href="https://haybnz.web.app?utm_source=github.com">https://haybnz.web.app</a>
</p>

<p align="center">
  🔗 <strong>Blog on WireTapper:</strong>
  <a href="https://medium.com/@h9z/wire-tapper-wireless-osint-signal-intelligence-platform-e5104659a1cb?utm_source=github.com">
    Read on Medium
  </a>
</p>

<p align="center">
  <a href="https://github.com/sponsors/h9zdev">
    <img src="https://img.shields.io/badge/Make%20a%20Difference-Sponser%20My%20Work-6A1B9A?style=for-the-badge&logo=github&logoColor=white" alt="Support My Work" />
  </a>
</p>
<p align="center">
  <a href="https://github.com/h9zdev/WireTapper">
    <img src="https://img.shields.io/static/v1?label=Python&message=WireTapper&color=2A3E87&labelColor=6A7DA8&style=for-the-badge&logo=python&logoColor=white" />
  </a>
  <a href="https://github.com/h9zdev/WireTapper/issues">
    <img src="https://img.shields.io/github/issues/h9zdev/WireTapper?style=for-the-badge&color=8B0000&logo=github" />
  </a>
  <a href="https://github.com/h9zdev/WireTapper/network/members">
    <img src="https://img.shields.io/github/forks/h9zdev/WireTapper?style=for-the-badge&color=455A64&logo=github" />
  </a>
  <a href="https://github.com/h9zdev/WireTapper/stargazers">
    <img src="https://img.shields.io/github/stars/h9zdev/WireTapper?style=for-the-badge&color=FFD700&logo=github" />
  </a>
</p>

> [!Note]
> ## 🛰️ SocioSential — Social Media OSINT
> [![GitHub](https://img.shields.io/badge/GitHub-h9zdev%2FSocioSential-blue?logo=github&style=flat-square)](https://github.com/h9zdev/SocioSential)
> ## 📡 EthiFi — WiFi Deauther *(New Version)*
> [![GitHub](https://img.shields.io/badge/GitHub-h9zdev%2FEthiFi-green?logo=github&style=flat-square)](https://github.com/h9zdev/EthiFi)

<br>
## 📶 Device Categories

WireTapper plots records from the databases above and **categorizes** them from
network names / banners (heuristic classification, not dedicated sensing):

*   **Wi-Fi** access points & clients (+ public credential-leak flag from wpa-sec)
*   **Bluetooth & BLE** devices (via Wigle's Bluetooth dataset)
*   **CCTV / IP cameras**, **dashcams**
*   **Vehicles** (names matching infotainment/telematics brands)
*   **Headphones, wearables**, and smart audio
*   **Smart TVs & IoT** appliances
*   **Cell towers** & mobile network beacons

> These are labels applied to third-party data, not independent RF sensors — see
> the "How it works" note above.


## 🔑 API Services

WireTapper integrates with several external services to provide intelligence. You will need to obtain API keys from the following:

*   **[Wigle.net](https://wigle.net/)** – Wireless network mapping and discovery.
*   **[wpa-sec](https://wpa-sec.stanev.org)** – Distributed WPA-PSK auditor database.
*   **[OpenCellID](https://opencellid.org/)** – Open-source database of cell towers.
*   **[Shodan](https://www.shodan.io/)** – Search engine for Internet-connected devices.
    *   **Note:** A **Premium account** is required to use Shodan's API with this tool.


## 🚀 Installation

Follow these steps to get WireTapper up and running:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/h9zdev/WireTapper.git
   cd WireTapper
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys and Run:**

   Choose one of the following methods to configure your API keys and run the application:

   Keys come from **environment variables** (never hardcode secrets in source —
   see [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md)). Copy `.env.example`
   to `.env` and fill it in — `app.py` auto-loads `.env` via `python-dotenv`.
   Alternatively, export the variables in your shell:
   ```bash
   export WIGLE_API_NAME="your_wigle_api_name"
   export WIGLE_API_TOKEN="your_wigle_api_token"
   export OPENCELLID_API_KEY="your_opencellid_api_key"
   export SHODAN_API_KEY="your_shodan_api_key"
   ```

   Then start the server (`app.py` is the single backend; `app-env.py` is a
   backwards-compatible alias that imports it):
   ```bash
   python app.py           # dev only (localhost, debugger off)
   ```
   For anything beyond local use, run behind a production WSGI server:
   ```bash
   gunicorn -w 2 -b 127.0.0.1:8080 app:app
   ```

   > **Server defaults (SEC-01):** binds `127.0.0.1:8080` with the debugger
   > **off**. For local development only you may opt in via `FLASK_HOST`,
   > `FLASK_PORT`, and `FLASK_DEBUG=1`. Never expose the Flask dev server
   > publicly — put it behind gunicorn/uvicorn + a reverse proxy.
   >
   > **Access control (SEC-03):** set `WIRETAPPER_ACCESS_TOKEN` to require an
   > `X-API-Key` header on the data endpoints, and tune `RATE_LIMIT_DEFAULT`.
   > All outbound calls have timeouts. See `.env.example` for every knob.

   The application will be available at `http://localhost:8080/map-w`.

## 🧪 Development

Requires **Python 3.10+** (Flask-Limiter 4.x dropped 3.9).

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .        # lint (config in pyproject.toml)
pytest -q           # test suite (outbound HTTP stubbed — no keys needed)
```

CI (GitHub Actions, `.github/workflows/ci.yml`) runs ruff + pytest on Python
3.10 and 3.12 for every push to `main` and every pull request.

### Deploying

WireTapper ships with Vercel config (`vercel.json` + `api/index.py`) and runs as
a Python serverless function, or under gunicorn on any WSGI host
(`gunicorn -w 2 -b 127.0.0.1:8080 app:app`). See
[`docs/DEPLOY.md`](docs/DEPLOY.md) — **read §3 (rate-limit store) and §5
(function timeout) before exposing it publicly.** See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the system map and
[`TODO.md`](TODO.md) for the remaining roadmap.

## 📷 Screenshots

![WireTapper Image 1](https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/Wiretapper11.png)  
![WireTapper Image 2](https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/Wiretapper34.png)  
![WireTapper Image 3](https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/Wiretapper354.png)  
![WireTapper Image 4](https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/Wiretapper55.png)  
![WireTapper Image 5](https://raw.githubusercontent.com/h9zdev/WireTapper/main/images/Wiretapper568.png)


## 📜 License

This project is licensed under the **Non-Commercial Open Source License (NCOSL)** —
use, copy, modify, and distribute for **non-commercial purposes only**, with
attribution. Commercial use requires explicit permission. See the
[LICENSE](LICENSE) file for the authoritative terms.

**Unauthorized and unlawful use is strictly prohibited.** See
[`PRIVACY.md`](PRIVACY.md) for acceptable use and [`docs/LEGAL.md`](docs/LEGAL.md)
for third-party data-source terms.

📧 Contact: singularat@protn.me

## ☕ Support

Donate via Monero: `45PU6txuLxtFFcVP95qT2xXdg7eZzPsqFfbtZp5HTjLbPquDAugBKNSh1bJ76qmAWNGMBCKk4R1UCYqXxYwYfP2wTggZNhq`

## 👥 Contributors and Developers

[<img src="https://avatars.githubusercontent.com/u/67865621?s=64&v=4" width="64" height="64" alt="haybnzz">](https://github.com/h9zdev)
 [<img src="https://avatars.githubusercontent.com/u/108749445?s=64&v=4"  width="64" height="64" alt="VaradScript">](https://github.com/varadScript)
## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=h9zdev/WireTapper&type=timeline&legend=bottom-right)](https://www.star-history.com/#h9zdev/WireTapper&type=timeline&legend=bottom-right)
