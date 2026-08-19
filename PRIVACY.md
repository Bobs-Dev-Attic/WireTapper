# Privacy & Acceptable Use

WireTapper is an **OSINT (open-source intelligence)** tool. It is intended for
**lawful, authorized use only** — security research, testing networks you own or
are authorized to assess, and education. This document explains what data the
tool touches and the rules for using it. It is guidance for operators and
contributors, **not** legal advice.

## What WireTapper does — and does not — do

- It **queries public third-party databases** (Wigle, OpenCellID/UnwiredLabs,
  Shodan, wpa-sec) and plots the results on a map.
- It **does not** intercept live radio/Wi-Fi/Bluetooth traffic, capture packets,
  crack keys, or harvest credentials. The "WPA-SEC LEAKED" flag reflects data
  **already public** in the wpa-sec database, surfaced via a privacy-preserving
  k-anonymity query (only a 4-character hash prefix leaves the client).

## Personal data

Wireless identifiers (BSSIDs, SSIDs) and precise locations can constitute
**personal data** under laws such as the GDPR and CCPA. If you deploy WireTapper
in a way that processes such data about identifiable people, you are the data
controller and are responsible for having a lawful basis, honoring data-subject
rights, and meeting retention/security obligations. Do not use WireTapper to
profile, track, or surveil individuals.

## Data the app itself stores

- **No server-side user tracking.** The client-side activity beacon that used to
  send a username cookie, click text, and dwell time was **removed**.
- **Local only:** a one-time "authorized & lawful use" acknowledgement is stored
  in your browser's `localStorage` (`wiretapper_consent_v1`). Nothing is sent to
  a server.
- **API keys** are read from the environment / `.env` (git-ignored). Never commit
  real keys; rotate any key that was ever committed.

## Third-party terms

Your use of the integrated services is governed by **their** terms — see
[`docs/LEGAL.md`](docs/LEGAL.md). Respect their rate limits, attribution, and
redistribution rules.

## Reporting

Security issues: see [`SECURITY.md`](SECURITY.md). Misuse concerns can be raised
via the repository's contact channels.

---

**By using WireTapper you confirm your use is lawful and authorized.**
Unauthorized surveillance or interception is prohibited (and in this build,
technically out of scope — the tool only reads public databases).
