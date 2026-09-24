package model

import (
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type Venue string

const (
	VenueHyperliquid Venue = "hyperliquid"
	VenueLighter     Venue = "lighter"
)

const MappingProvisional = "provisional"

type Instrument struct {
	CanonicalID string
	Contracts   []Contract
}

type ResearchProfile struct {
	Name              string
	PerLegNotionalUSD fixed.Value
}

type Rejection struct {
	CanonicalID string
	Codes       []ReasonCode
}

type Contract struct {
	Venue              Venue       `json:"venue"`
	MarketID           string      `json:"market_id"`
	VenueSymbol        string      `json:"venue_symbol"`
	CanonicalID        string      `json:"canonical_id"`
	BaseUnit           string      `json:"base_unit"`
	QuoteUnit          string      `json:"quote_unit"`
	ContractMultiplier fixed.Value `json:"contract_multiplier"`
	TickSize           fixed.Value `json:"tick_size"`
	LotSize            fixed.Value `json:"lot_size"`
	MinBase            fixed.Value `json:"min_base"`
	MinQuoteUSD        fixed.Value `json:"min_quote_usd"`
	MappingState       string      `json:"mapping_state"`
	EvidenceHash       string      `json:"evidence_hash"`
}

type Run struct {
	ID, ConfigHash, FormulaHash string
	StartedAt, PlannedEndAt     time.Time
	State                       string
}

type ProfileEvidence struct {
	PerLegNotionalUSD, Quantity, BuyNotionalUSD, SellNotionalUSD fixed.Value
	BuyVWAP, SellVWAP, RawDivergenceBPS, ModeledNetCaptureUSD    fixed.Value
	CapitalSupported                                             bool
	Codes                                                        []ReasonCode
}

type EvaluationSample struct {
	ID, RunID, CanonicalID, BootID, LeftBatchID, RightBatchID string
	EvaluatedAt                                               time.Time
	Profiles                                                  []ProfileEvidence
	QualityCodes                                              []ReasonCode
}

type LifecycleEvidence struct {
	ID, RunID, CanonicalID, Direction, IndependenceGroupID string
	OpenedAt, ClosedAt                                     time.Time
	Entry, Delayed, Stress, Exit                           EvaluationSample
	StandardNetCaptureUSD, PremiumNetCaptureUSD            fixed.Value
	Codes                                                  []ReasonCode
}

type ReferenceSample struct {
	ID, RunID, CanonicalID, SourceSymbol, PayloadHash string
	SourceUpdatedAt, ObservedAt                       time.Time
	Bid, Ask, Volume24HUSD, OpenInterestUSD           *fixed.Value
	Stale                                             bool
}

type StageDecision struct {
	ID, RunID, Decision, ReportHash, DataHash string
	DecidedAt                                 time.Time
	Codes                                     []ReasonCode
}

type LifecycleEvent struct {
	Type     string
	Evidence LifecycleEvidence
}

type LifecycleAdmission struct {
	Allowed bool
	Codes   []ReasonCode
}

func AdmitLifecycle(contract Contract) LifecycleAdmission {
	codes := make([]ReasonCode, 0, 2)
	if contract.MappingState != "verified" {
		codes = append(codes, MappingUnverified)
	}
	if contract.EvidenceHash == "" {
		codes = append(codes, ContractUnverified)
	}
	return LifecycleAdmission{Allowed: len(codes) == 0, Codes: codes}
}
