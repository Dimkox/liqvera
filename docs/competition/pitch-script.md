# Liqvera — two-minute pitch script

Recording draft, 2026-10-12. Use the seven-slide [deck](presentation.html). Approximately 280 spoken words; rehearse at 140 words per minute and trim pauses to fit two minutes. The timeline is a recording target, not an existing video.

| Time | Visual | Narration |
| --- | --- | --- |
| 0:00–0:15 | Slide 1: identity | Liqvera makes market reports you can verify. We connect reproducible public-market evidence with test-MUSD payments on Mezo Testnet, giving a digital report a useful payment path and an independent way to check its results. |
| 0:15–0:30 | Slide 2: problem | A headline price cannot tell you what a hypothetical order would fill at. Screenshots are difficult to reproduce. Analysts and developers need the underlying depth, clear assumptions, and calculations they can inspect after the report is delivered. |
| 0:30–0:50 | Slide 3: flow | Liqvera captures a public Hyperliquid BTC order-book snapshot. It computes available depth, filled quantity, average execution price, and price impact with exact arithmetic. The report travels with an evidence ZIP. Our offline verifier checks the bundle and recomputes the results without contacting our server. |
| 0:50–1:10 | Slide 4: MUSD | MUSD is the access-payment asset. Our x402 gateway binds delivery to exact report hashes and checks confirmed settlement on Mezo Testnet. Historical paid delivery exists. Today, new payments remain disabled until valid payment authority is restored; the public historical preview works without a wallet. |
| 1:10–1:30 | Slide 5: demo | In the historical preview, inspect the capture timestamp, quantity, and depth results. Download the preserved evidence and use its matching verifier. This shows what can be independently checked. The report describes a snapshot; it does not trade, predict profits, or prove exchange authenticity. |
| 1:30–1:45 | Slide 6: evidence | The complete product includes a browser, gateway, capture service, report builder, and offline verifier. Our documented local validation and independent vulnerability checks support the implementation. We distinguish those results from live acceptance and publish the remaining limitations. |
| 1:45–2:00 | Slide 7: next steps | Liqvera enters as an existing project in Access and Distribution. During the buildathon, we propose improving the MUSD access flow, testing usability with prospective users, and showing measurable progress between waves. Explore the public source and historical demo at liqvera dot site. |

## Recording checklist

- Show the real historical preview and its timestamp; do not present it as a new capture.
- Use the verifier matching the historical artifact, or explicitly label a separate current local demonstration.
- Never expose wallet signatures, bearer links, grants, credentials or private account views.
- Do not click through a fresh payment or describe it as available while authority is blocked.
- Before recording the final entry, update the narration to the then-current demonstrated state and actual in-event changes.
