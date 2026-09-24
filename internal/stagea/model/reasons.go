package model

type ReasonCode string

const (
	MappingUnverified       ReasonCode = "INSTRUMENT_MAPPING_UNVERIFIED"
	ContractUnverified      ReasonCode = "CONTRACT_EQUIVALENCE_UNVERIFIED"
	PrimaryBookMissing      ReasonCode = "PRIMARY_BOOK_MISSING"
	BookStale               ReasonCode = "BOOK_STALE"
	CrossVenueSkewExceeded  ReasonCode = "CROSS_VENUE_SKEW_EXCEEDED"
	SequenceGapOpen         ReasonCode = "SEQUENCE_GAP_OPEN"
	BookInvalid             ReasonCode = "BOOK_INVALID"
	DepthInsufficient       ReasonCode = "DEPTH_INSUFFICIENT"
	QuantityMismatch        ReasonCode = "QUANTITY_MISMATCH_EXCEEDED"
	VenueMinimumNotMet      ReasonCode = "VENUE_MINIMUM_NOT_MET"
	CapitalUnsupported      ReasonCode = "CAPITAL_NOTIONAL_UNSUPPORTED"
	ZeroMarginHeadroom      ReasonCode = "ZERO_MARGIN_HEADROOM"
	FeeModelIncomplete      ReasonCode = "FEE_MODEL_INCOMPLETE"
	EntryBelowFloor         ReasonCode = "ENTRY_DIVERGENCE_BELOW_FLOOR"
	ExitEvidenceMissing     ReasonCode = "EXIT_EVIDENCE_MISSING"
	StressNonPositive       ReasonCode = "STRESS_CHANGE_NON_POSITIVE"
	LifecycleNotIndependent ReasonCode = "LIFECYCLE_NOT_INDEPENDENT"
)
