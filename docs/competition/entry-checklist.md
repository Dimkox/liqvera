# Liqvera Buildathon entry — October 13, 2026

**Track 2: Access and Distribution for MUSD/MEZO.** The submission story is spending test MUSD on independently verifiable digital information. Author: [Dimkox](https://github.com/Dimkox), as confirmed by the owner.

## Deliverables

| Item | Current result |
| --- | --- |
| Live project | [liqvera.site](https://liqvera.site), Mezo Testnet 31611; merchant checkout enabled |
| Public source | [Dimkox/liqvera](https://github.com/Dimkox/liqvera) |
| Application text | [Ready-to-paste fields](submission.md) |
| Product deck | [Seven-page PDF](presentation.pdf) and [editable HTML](presentation.html) |
| Two-minute video | [Captioned MP4](pitch.mp4), [public download](https://raw.githubusercontent.com/Dimkox/liqvera/main/docs/competition/pitch.mp4), [script](pitch-script.md), [captions](pitch.srt) |
| Functional proof | [Public endpoints](2026-10-13-public-checks.json), [fresh unsigned browser quote](2026-10-13-browser-results.json), [offline preview reproduction](2026-10-13-verification.json) |
| Security | [Exact deployed-image checks](../security/2026-10-12-testnet.md); no new scan is claimed for these media/documentation changes |
| Baseline | `607fa0d7578dfbcd406ca9a1e8b59fb1eaf3cb63`, prepared before Wave 1 |

[Media verification](2026-10-13-media-verification.json) records the exact 120-second H.264 file, seven-page PDF, hashes and healthy runtime images.

The video is a **silent, captioned preparation cut**, with screenshots of the real service and an actual preview-verifier result. Its wallet provider is a non-signing test stub, explicitly labelled in the frames. It is not a recording of a completed new purchase or work completed during Wave 1.

## Follow-up after the owner-confirmed submission

1. As a separate post-update regression check, record the owner-authorized 0.01 test-MUSD purchase with a real wallet. Preserve the transaction hash, canonical receipt and confirmed report/ZIP delivery; reproduce the downloaded paid bundle. The supplied wallet received test MEZO, which is not the report-payment asset. Its address alone does not provide a signer.
2. During Wave 1, implement and document a useful new extension against the baseline. Proposed scope: reduce Testnet funding friction and improve purchase/recovery guidance; validate report completion and independent reproduction with prospective users. These are proposals, not shipped features or demonstrated demand.
3. Replace the pending-payment video segment with real paid evidence and describe the actual in-event changes. The current MP4 is downloadable; verify the final video URL in the AKINDO form and use supported video hosting if required.
4. The owner confirms the entry is already submitted. Do not repeat registration or submission. This session has not accessed the account and cannot establish which attachment versions were submitted. Any future update should preserve the existing entry; private registration details belong in that account, not this repository.

## Opportunity and schedule

The official event offers a total **$7,000 equivalent in MEZO**: $2,000 in Wave 1 and $5,000 in Wave 2, allocated proportionally to judging points. It offers access to the core team, feedback between waves and a demo session for top teams. Awards require selection and KYB; test tokens are not a reward claim. Mezo integration and product/business viability each carry 30% of the score. [Official event](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

The API sets Wave 1 at **October 15, 15:00 UTC → October 26, 15:00 UTC**; the event overview labels the opening October 16. The kickoff workshop is **October 13, 13:00 UTC**. Wave 2 is November 2–15, with results November 23. [Checked event facts](2026-10-13-event-facts.json), [public API](https://api.akindo.io/public/wave-hacks/OVOO0gdrVU8379D10), [workshop](https://luma.com/mezo-buildathon).

Do not present pre-event preparation as in-event development. Neither this checklist nor publication to GitHub is an AKINDO submission.
