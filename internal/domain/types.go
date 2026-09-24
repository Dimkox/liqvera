package domain

import (
	"errors"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type TenantID string
type UserID string
type AccountID string
type ExecutionID string
type InstrumentID string
type Venue string

const (
	VenueHyperliquid Venue = "hyperliquid"
	VenueLighter     Venue = "lighter"
	VenueVariational Venue = "variational"
)

type Side string

const (
	SideBuy  Side = "buy"
	SideSell Side = "sell"
)

func (s Side) Valid() bool { return s == SideBuy || s == SideSell }

type OrderType string

const (
	OrderTypeLimit  OrderType = "limit"
	OrderTypeMarket OrderType = "market"
)

type TimeInForce string

const (
	TimeInForceGTC      TimeInForce = "gtc"
	TimeInForceIOC      TimeInForce = "ioc"
	TimeInForceFOK      TimeInForce = "fok"
	TimeInForcePostOnly TimeInForce = "post_only"
)

type OrderStatus string

const (
	OrderStatusPending   OrderStatus = "pending"
	OrderStatusSubmitted OrderStatus = "submitted"
	OrderStatusOpen      OrderStatus = "open"
	OrderStatusPartial   OrderStatus = "partial"
	OrderStatusFilled    OrderStatus = "filled"
	OrderStatusCancelled OrderStatus = "cancelled"
	OrderStatusRejected  OrderStatus = "rejected"
	OrderStatusUnknown   OrderStatus = "unknown"
)

func (s OrderStatus) Terminal() bool {
	return s == OrderStatusFilled || s == OrderStatusCancelled || s == OrderStatusRejected
}

type VenueHealth string

const (
	VenueHealthy         VenueHealth = "healthy"
	VenueDegraded        VenueHealth = "degraded"
	VenueReadOnly        VenueHealth = "read_only"
	VenueTradingDisabled VenueHealth = "trading_disabled"
	VenueUnknown         VenueHealth = "unknown"
)

type Instrument struct {
	ID             InstrumentID `json:"id"`
	Venue          Venue        `json:"venue"`
	VenueSymbol    string       `json:"venue_symbol"`
	CanonicalAsset string       `json:"canonical_asset"`
	ContractSize   fixed.Value  `json:"contract_size"`
	TickSize       fixed.Value  `json:"tick_size"`
	StepSize       fixed.Value  `json:"step_size"`
	MaxLeverage    fixed.Value  `json:"max_leverage"`
}

type OrderIntent struct {
	TenantID       TenantID     `json:"tenant_id"`
	AccountID      AccountID    `json:"account_id"`
	ExecutionID    ExecutionID  `json:"execution_id"`
	Venue          Venue        `json:"venue"`
	InstrumentID   InstrumentID `json:"instrument_id"`
	Side           Side         `json:"side"`
	Type           OrderType    `json:"type"`
	TimeInForce    TimeInForce  `json:"time_in_force"`
	BaseQuantity   fixed.Value  `json:"base_quantity"`
	LimitPrice     fixed.Value  `json:"limit_price"`
	ReduceOnly     bool         `json:"reduce_only"`
	ClientOrderID  string       `json:"client_order_id"`
	IdempotencyKey string       `json:"idempotency_key"`
}

func (o OrderIntent) Validate() error {
	if o.TenantID == "" || o.AccountID == "" || o.ExecutionID == "" {
		return errors.New("tenant, account, and execution are required")
	}
	if o.Venue == "" || o.InstrumentID == "" || !o.Side.Valid() {
		return errors.New("venue, instrument, and valid side are required")
	}
	if !o.BaseQuantity.IsPositive() {
		return errors.New("base quantity must be positive")
	}
	if o.Type == OrderTypeLimit && !o.LimitPrice.IsPositive() {
		return errors.New("limit price must be positive")
	}
	if o.IdempotencyKey == "" {
		return errors.New("idempotency key is required")
	}
	return nil
}

type OrderRef struct {
	TenantID      TenantID
	AccountID     AccountID
	Venue         Venue
	InstrumentID  InstrumentID
	VenueOrderID  string
	ClientOrderID string
}

type OrderSnapshot struct {
	OrderRef
	Status         OrderStatus
	Side           Side
	BaseQuantity   fixed.Value
	FilledQuantity fixed.Value
	UpdatedAt      time.Time
}

type Balance struct {
	Asset     string
	Total     fixed.Value
	Available fixed.Value
}

type Position struct {
	InstrumentID InstrumentID
	BaseQuantity fixed.Value
	EntryPrice   fixed.Value
	MarkPrice    fixed.Value
}

type Fill struct {
	Venue             Venue
	VenueFillID       string
	VenueOrderID      string
	ClientOrderID     string
	InstrumentID      InstrumentID
	Side              Side
	BaseQuantity      fixed.Value
	Price             fixed.Value
	Fee               fixed.Value
	FeeAsset          string
	LiquidityRole     string
	ExchangeTimestamp time.Time
	ReceiveTimestamp  time.Time
}

type ReconciliationSnapshot struct {
	AccountID  AccountID
	Venue      Venue
	Balances   []Balance
	Positions  []Position
	OpenOrders []OrderSnapshot
	Fills      []Fill
	ObservedAt time.Time
	Complete   bool
}
