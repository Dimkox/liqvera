// Package exchange defines capability-specific venue contracts. RFQ venues do
// not impersonate order books, and market-data access does not imply trading.
package exchange

import (
	"context"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type Capabilities struct {
	HasCLOB               bool
	HasRFQ                bool
	HasPublicWS           bool
	HasPrivateWS          bool
	SupportsIOC           bool
	SupportsFOK           bool
	SupportsPostOnly      bool
	SupportsReduceOnly    bool
	SupportsBatchOrders   bool
	SupportsClientOrderID bool
	SupportsPartnerFee    bool
	SupportsSubaccounts   bool
}

type MarketEvent struct {
	Venue             domain.Venue
	InstrumentID      domain.InstrumentID
	Kind              string
	Sequence          int64
	ExchangeTimestamp time.Time
	ReceiveTimestamp  time.Time
	Payload           any
}

type MarketDataReader interface {
	Venue() domain.Venue
	Capabilities(context.Context) (Capabilities, error)
	ListInstruments(context.Context) ([]domain.Instrument, error)
	SubscribeMarketData(context.Context, []domain.InstrumentID) (<-chan MarketEvent, error)
}

type OrderAck struct {
	VenueOrderID  string
	ClientOrderID string
	AcceptedAt    time.Time
	// Accepted is only transport/sequencer acceptance. It never means filled.
	Accepted bool
}

type TradingExecutor interface {
	Venue() domain.Venue
	Capabilities(context.Context) (Capabilities, error)
	GetBalances(context.Context, domain.AccountID) ([]domain.Balance, error)
	GetPositions(context.Context, domain.AccountID) ([]domain.Position, error)
	GetOpenOrders(context.Context, domain.AccountID) ([]domain.OrderSnapshot, error)
	PlaceOrder(context.Context, domain.OrderIntent) (OrderAck, error)
	CancelOwnedOrder(context.Context, domain.OrderRef) error
	Reconcile(context.Context, domain.AccountID) (domain.ReconciliationSnapshot, error)
}

type RFQRequest struct {
	TenantID     domain.TenantID
	AccountID    domain.AccountID
	InstrumentID domain.InstrumentID
	Side         domain.Side
	BaseQuantity fixed.Value
	ValidFor     time.Duration
}

type RFQQuote struct {
	QuoteID      string
	Venue        domain.Venue
	InstrumentID domain.InstrumentID
	Side         domain.Side
	BaseQuantity fixed.Value
	Price        fixed.Value
	Fee          fixed.Value
	ExpiresAt    time.Time
}

type RFQClient interface {
	Venue() domain.Venue
	RequestQuote(context.Context, RFQRequest) (RFQQuote, error)
	AcceptQuote(context.Context, domain.AccountID, RFQQuote, string) (OrderAck, error)
}
