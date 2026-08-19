# Third-Party Data Sources — Terms & Compliance

WireTapper is a client for several external OSINT services. Each has its own
terms of service, rate limits, and redistribution rules. This is a **pointer +
summary** for operators; always read the current upstream terms — they change.
Nothing here is legal advice.

| Service | What we use | Key obligations (verify upstream) |
|---|---|---|
| **Wigle** (`api.wigle.net`) | Wi-Fi / Bluetooth network search | Requires an account + API token. Daily query quotas. Redistribution of the underlying observation data is restricted — do not re-publish bulk Wigle data through a public endpoint. Attribution expected. |
| **OpenCellID / UnwiredLabs** (`unwiredlabs.com`, `opencellid.org`) | Cell geolocation & towers | API key required. OpenCellID data is under a share-alike style license; UnwiredLabs has commercial terms and quotas. Respect per-key limits. |
| **Shodan** (`api.shodan.io`) | Internet-exposed host search | **Paid/premium** API required for search. Results describe third-party hosts — do not use to attack or access them. Query quotas + credit costs apply per search. |
| **wpa-sec** (`wpa-sec.stanev.org`) | Leaked WPA handshake database (k-anonymity) | Community project. Only a 4-char hash prefix is sent (privacy-preserving). Use responsibly; the "leaked" status reflects already-public data. |

## Operator responsibilities

1. **Authorization.** Only query for networks/areas you are authorized to assess.
2. **Rate limits & cost.** WireTapper caps some queries (`MAX_QUERY_LEN`, Shodan
   result limits) and rate-limits its own endpoints, but you remain responsible
   for staying within each provider's quota and, for Shodan, its credit costs.
   Enable the access-token gate (`WIRETAPPER_ACCESS_TOKEN`) before exposing the
   app so anonymous users can't spend your paid keys.
3. **Redistribution.** Re-serving upstream data through a public WireTapper
   instance may violate a provider's terms. Keep instances private/authorized.
4. **Attribution.** Preserve map tile and data-source attributions in the UI.

## Map tiles

The UI can use OpenStreetMap, Esri World Imagery, and Google tiles. Each tile
provider has its own usage policy (OSM tile usage policy; Esri/Google terms).
For production, use an appropriate tile plan/provider rather than the public
demo tile servers.

## License

WireTapper itself is licensed **CC BY-NC 4.0-style / NCOSL** — see
[`LICENSE`](../LICENSE). Non-commercial, attribution required.
