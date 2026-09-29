"""Stable acceptance inventory from LIQVERA_FACTORY_TZ.md section 15."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    title: str
    assertion: str
    execution_class: str = "local"
    local_omission: str | None = None

    @property
    def required_claims(self) -> tuple[str, ...]:
        return (self.assertion,)


CASES: dict[str, Case] = {
    "A01": Case("Baseline and modified tree checked separately", "before_after_checks", local_omission="BASELINE_ASSERTION_PLAN_NOT_PROVIDED"),
    "A02": Case("BUY exact reference vector", "buy_exact_values", local_omission="VECTOR_ASSERTION_NOT_SPLIT"),
    "A03": Case("SELL and decimal boundary vectors", "sell_exact_values", local_omission="VECTOR_ASSERTION_NOT_SPLIT"),
    "A04": Case("Invalid quantity and insufficient depth rejection", "invalid_input_rejected", local_omission="NEGATIVE_VECTOR_ASSERTION_NOT_SPLIT"),
    "A05": Case("Time, book, instrument, and metadata rejection", "invalid_snapshot_rejected", local_omission="SNAPSHOT_NEGATIVE_ASSERTION_NOT_SPLIT"),
    "A06": Case("Fictitious mapping and wrong units rejected", "identity_rejected", local_omission="IDENTITY_NEGATIVE_ASSERTION_NOT_SPLIT"),
    "A07": Case("Unavailable live source never falls back to fixture", "source_unavailable", "public_read"),
    "A08": Case("Corrupted and unsafe bundles rejected", "bundle_tamper_rejected", local_omission="BUNDLE_ASSERTION_PLAN_NOT_PROVIDED"),
    "A09": Case("Clean-machine offline replay has exact digest", "offline_replay_exact", local_omission="INSTALLED_ASSERTION_PLAN_NOT_PROVIDED"),
    "A10": Case("Unpaid retrieval returns 402 without paid body", "unpaid_402", local_omission="HTTP_402_ASSERTION_NOT_PACKAGED"),
    "A11": Case("Invalid authorizations never entitle", "bad_authorizations_rejected", local_omission="AUTHORIZATION_MATRIX_NOT_PACKAGED"),
    "A12": Case("MUSD amount is exact in every layer", "atomic_amount_exact", local_omission="CROSS_LAYER_AMOUNT_ASSERTION_NOT_PACKAGED"),
    "A13": Case("Distinct buyer and merchant confirmed testnet transfer", "confirmed_transfer", "testnet_write"),
    "A14": Case("Paid repeat access without another settlement", "repeat_access_no_charge", "testnet_write"),
    "A15": Case("Concurrent retries create one quote and at most one charge", "concurrent_idempotency", local_omission="CONCURRENCY_REQUIRES_APPROVED_POSTGRES_PROFILE"),
    "A16": Case("Idempotency key conflict returns 409", "body_conflict_409", local_omission="HTTP_CONFLICT_ASSERTION_NOT_PACKAGED"),
    "A17": Case("Crash windows recover uncertain payment safely", "crash_recovery", local_omission="CRASH_MATRIX_ASSERTION_NOT_PACKAGED"),
    "A18": Case("Lost response recovers access without another payment", "lost_response_recovery", local_omission="RECOVERY_HTTP_ASSERTION_NOT_PACKAGED"),
    "A19": Case("Ambiguous transfer is not falsely confirmed", "ambiguous_transfer_blocked", local_omission="AMBIGUOUS_TRANSFER_ASSERTION_NOT_PACKAGED"),
    "A20": Case("Expiry during settlement retains original report", "expiry_during_settlement", local_omission="EXPIRY_ASSERTION_NOT_PACKAGED"),
    "A21": Case("Foreign scope and guessed identifiers cannot access", "scope_isolation", local_omission="SCOPE_HTTP_ASSERTION_NOT_PACKAGED"),
    "A22": Case("Missing or corrupt artifacts fail safely", "artifact_failure_recovery", local_omission="ARTIFACT_RECOVERY_ASSERTION_NOT_PACKAGED"),
    "A23": Case("Wrong chain, token, and mainnet disable payment", "wrong_network_rejected", local_omission="NETWORK_MATRIX_ASSERTION_NOT_PACKAGED"),
    "A24": Case("Failed or unknown settlement withholds paid body", "settlement_unknown_withheld", local_omission="SETTLEMENT_MATRIX_ASSERTION_NOT_PACKAGED"),
    "A25": Case("Canary secrets absent from logs and bundle", "canary_redaction", local_omission="CANARY_SCAN_ASSERTION_NOT_PACKAGED"),
    "A26": Case("Container and network isolation checked", "network_isolation", local_omission="CONTAINER_RUNTIME_NOT_AUTHORIZED"),
    "A27": Case("Stage A verdict and fixture suite unchanged", "stage_a_regression", local_omission="STAGE_A_ASSERTION_PLAN_NOT_PROVIDED"),
    "A28": Case("Clean README install, build, and offline demo", "clean_install_demo", local_omission="CLEAN_MACHINE_HARNESS_NOT_PACKAGED"),
    "A29": Case("Anonymous clone and provenance comparison", "anonymous_clone_provenance", "public_read"),
    "A30": Case("Wallet cancel, switch, reload, wrong chain", "wallet_recovery", "local", "WALLET_ASSERTION_PLAN_NOT_PROVIDED"),
}
