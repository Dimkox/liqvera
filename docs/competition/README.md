# Liqvera at the Mezo Buildathon

October 23 deployed update: the same Testnet product now includes Mezo DEX comparison and borrower Trove risk, with fixed-block raw calls and offline-reproducible ZIPs. Public native preparation and the unpaid x402 boundary are verified; historical MUSD transfers remain the payment proof. [Deployment record](../security/2026-10-23-mezo-trove-deployment.md), [DEX evidence](../mezo-integration.md) and [Trove verification](../mezo-trove-risk.md). The [rechecked official deadline](2026-10-23-event-facts.json) is October 26 at **15:00 UTC**; internal target 11:00 UTC, code freeze 08:00 UTC.


**Spend test MUSD on market reports you can independently verify.**

Liqvera provides public BTC market-depth reports, downloadable evidence and offline recalculation. Its Mezo Testnet integration demonstrates an MUSD payment use case for digital information. Public attribution: [Dimkox](https://github.com/Dimkox).

## Competition package

- [Application fields and official requirements](submission.md)
- [Final-entry checklist, benefits and deadlines](entry-checklist.md)
- [Eight-slide deck](presentation.pdf) · [editable source](presentation.html)
- [Two-minute captioned preparation video](pitch.mp4) · [public download](https://raw.githubusercontent.com/Dimkox/liqvera/main/docs/competition/pitch.mp4)
- [Video source](pitch.html) · [script](pitch-script.md) · [captions](pitch.srt)
- [Live demonstration procedure](demo-script.md)
- [Historical acceptance runner and evidence](acceptance-evidence.md)

The public demo includes the deployed Mezo DEX comparison and Trove risk reports. Current preview downloads reproduce offline. The video is a silent preparation cut and explicitly labels its non-signing wallet stub; the owner chose historical payment evidence for this update. The project predates Wave 1 and must show actual in-event progress. No AKINDO entry has been submitted by this session.

## October 23 Trove product update

The same [Testnet application](https://liqvera.site) now includes **Trove risk**:
borrower debt/collateral, exact ICR, theoretical MCR crossing, price scenarios and a
proven redemption position. The borrower defaults to the connected wallet address.
Open **Trove risk → Show sealed Trove example** for a wallet-free historical native
snapshot, or prepare a fresh borrower report through the existing 0.01 MUSD x402 flow.

A public native request reached READY at block 16324977; unchanged replay, input and
access boundaries, and the unpaid 402 response were verified. Its own operator-exported
ZIP reproduces offline. No fresh wallet signature or paid Trove settlement is claimed.
The owner selected the three already verified historical payment transactions.

[Deployment and scoped evidence](../security/2026-10-23-mezo-trove-deployment.md) records
main CI with 1101 Python tests + 85 subtests, 98 gateway tests without database skips
and 130 browser tests. [Published mobile/desktop views](2026-10-23-mezo-trove/published/result.json)
show the new panel without overflow. Mainnet, borrowing/redemption and a registry
contract are outside this update. The October 13 video remains a dated preparation
cut; the current screenshots and deck document the new features. This update does
not assert a new Akindo account submission.
