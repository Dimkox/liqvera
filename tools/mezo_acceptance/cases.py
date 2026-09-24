"""Stable acceptance inventory from LIQVERA_FACTORY_TZ.md section 15."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    title: str
    assertion: str
    live: bool = False


CASES: dict[str, Case] = {
    "A01": Case("Baseline and modified tree checked separately", "before_after_checks"),
    "A02": Case("BUY exact reference vector", "buy_exact_values"),
    "A03": Case("SELL and decimal boundary vectors", "sell_exact_values"),
    "A04": Case("Invalid quantity and insufficient depth rejection", "invalid_input_rejected"),
    "A05": Case("Time, book, instrument, and metadata rejection", "invalid_snapshot_rejected"),
    "A06": Case("Fictitious mapping and wrong units rejected", "identity_rejected"),
    "A07": Case("Unavailable live source never falls back to fixture", "source_unavailable", True),
    "A08": Case("Corrupted and unsafe bundles rejected", "bundle_tamper_rejected"),
    "A09": Case("Clean-machine offline replay has exact digest", "offline_replay_exact"),
    "A10": Case("Unpaid retrieval returns 402 without paid body", "unpaid_402"),
    "A11": Case("Invalid authorizations never entitle", "bad_authorizations_rejected"),
    "A12": Case("MUSD amount is exact in every layer", "atomic_amount_exact"),
    "A13": Case("Distinct buyer and merchant confirmed testnet transfer", "confirmed_transfer", True),
    "A14": Case("Paid repeat access without another settlement", "repeat_access_no_charge", True),
    "A15": Case("Concurrent retries create one quote and at most one charge", "concurrent_idempotency"),
    "A16": Case("Idempotency key conflict returns 409", "body_conflict_409"),
    "A17": Case("Crash windows recover uncertain payment safely", "crash_recovery"),
    "A18": Case("Lost response recovers access without another payment", "lost_response_recovery"),
    "A19": Case("Ambiguous transfer is not falsely confirmed", "ambiguous_transfer_blocked"),
    "A20": Case("Expiry during settlement retains original report", "expiry_during_settlement"),
    "A21": Case("Foreign scope and guessed identifiers cannot access", "scope_isolation"),
    "A22": Case("Missing or corrupt artifacts fail safely", "artifact_failure_recovery"),
    "A23": Case("Wrong chain, token, and mainnet disable payment", "wrong_network_rejected"),
    "A24": Case("Failed or unknown settlement withholds paid body", "settlement_unknown_withheld"),
    "A25": Case("Canary secrets absent from logs and bundle", "canary_redaction"),
    "A26": Case("Container and network isolation checked", "network_isolation"),
    "A27": Case("Stage A verdict and fixture suite unchanged", "stage_a_regression"),
    "A28": Case("Clean README install, build, and offline demo", "clean_install_demo"),
    "A29": Case("Anonymous clone and provenance comparison", "anonymous_clone_provenance", True),
    "A30": Case("Wallet cancel, switch, reload, wrong chain", "wallet_recovery", True),
}
