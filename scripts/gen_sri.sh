#!/usr/bin/env bash
# SEC-09: generate Subresource Integrity (SRI) hashes for the CDN assets used by
# templates/wifi-search.html. Run this on a machine WITH network access, then
# paste each printed integrity="sha384-..." (plus crossorigin="anonymous") onto
# the matching <link>/<script> tag. Google Fonts stylesheets are intentionally
# omitted — their content is request-dependent and cannot carry a stable SRI.
#
# Usage: bash scripts/gen_sri.sh
set -euo pipefail

urls=(
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
  "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
  "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
  "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"
  "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css"
)

for u in "${urls[@]}"; do
  hash="$(curl -sSf "$u" | openssl dgst -sha384 -binary | openssl base64 -A)"
  printf '%s\n  integrity="sha384-%s" crossorigin="anonymous"\n\n' "$u" "$hash"
done
