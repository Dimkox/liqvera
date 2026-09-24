// Package risk performs deterministic preflight validation. Every amount has
// an explicit unit in its field name to prevent the ambiguous limits found in
// the original RFC examples.
package risk

import (
	"errors"
	"fmt"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type Limits struct {
	MaxOrderNotionalUSD fixed.Value
	MaxGrossExposureUSD fixed.Value
	MaxAbsNetDeltaBase  fixed.Value
	MaxUnhedgedDuration time.Duration
	MaxDailyLossUSD     fixed.Value
	MaxDrawdownUSD      fixed.Value
	MaxSlippageBPS      int64
	MinMarginBufferBPS  int64
	MaxMarketDataAge    time.Duration
}

func (l Limits) Validate() error {
	if !l.MaxOrderNotionalUSD.IsPositive() || !l.MaxGrossExposureUSD.IsPositive() || !l.MaxAbsNetDeltaBase.IsPositive() {
		return errors.New("positive notional, gross exposure, and net delta limits are required")
	}
	if l.MaxUnhedgedDuration <= 0 || l.MaxMarketDataAge <= 0 {
		return errors.New("positive duration limits are required")
	}
	if l.MaxSlippageBPS < 0 || l.MinMarginBufferBPS < 0 {
		return errors.New("basis-point limits cannot be negative")
	}
	return nil
}

type Request struct {
	TenantID              domain.TenantID
	AccountID             domain.AccountID
	ExecutionID           domain.ExecutionID
	OrderNotionalUSD      fixed.Value
	GrossExposureAfterUSD fixed.Value
	AbsNetDeltaAfterBase  fixed.Value
	MaxUnhedgedDuration   time.Duration
	DailyLossUSD          fixed.Value
	DrawdownUSD           fixed.Value
	ExpectedSlippageBPS   int64
	MarginBufferBPS       int64
	MarketDataAge         time.Duration
	LongVenueHealth       domain.VenueHealth
	ShortVenueHealth      domain.VenueHealth
}

type Reservation struct {
	TenantID    domain.TenantID
	AccountID   domain.AccountID
	ExecutionID domain.ExecutionID
	ReservedUSD fixed.Value
	ApprovedAt  time.Time
	ExpiresAt   time.Time
}

func Evaluate(limits Limits, req Request, now time.Time) (Reservation, error) {
	if err := limits.Validate(); err != nil {
		return Reservation{}, fmt.Errorf("limits: %w", err)
	}
	if req.TenantID == "" || req.AccountID == "" || req.ExecutionID == "" {
		return Reservation{}, errors.New("tenant, account, and execution are required")
	}
	if req.LongVenueHealth != domain.VenueHealthy || req.ShortVenueHealth != domain.VenueHealthy {
		return Reservation{}, errors.New("both venues must be healthy")
	}
	if !req.OrderNotionalUSD.IsPositive() || req.OrderNotionalUSD.Cmp(limits.MaxOrderNotionalUSD) > 0 {
		return Reservation{}, errors.New("order notional exceeds limit")
	}
	if req.GrossExposureAfterUSD.Cmp(limits.MaxGrossExposureUSD) > 0 {
		return Reservation{}, errors.New("gross exposure exceeds limit")
	}
	if req.AbsNetDeltaAfterBase.Cmp(limits.MaxAbsNetDeltaBase) > 0 {
		return Reservation{}, errors.New("net delta exceeds limit")
	}
	if req.MaxUnhedgedDuration > limits.MaxUnhedgedDuration {
		return Reservation{}, errors.New("unhedged duration exceeds limit")
	}
	if req.DailyLossUSD.Cmp(limits.MaxDailyLossUSD) > 0 {
		return Reservation{}, errors.New("daily loss exceeds limit")
	}
	if req.DrawdownUSD.Cmp(limits.MaxDrawdownUSD) > 0 {
		return Reservation{}, errors.New("drawdown exceeds limit")
	}
	if req.ExpectedSlippageBPS > limits.MaxSlippageBPS {
		return Reservation{}, errors.New("expected slippage exceeds limit")
	}
	if req.MarginBufferBPS < limits.MinMarginBufferBPS {
		return Reservation{}, errors.New("margin buffer below limit")
	}
	if req.MarketDataAge < 0 || req.MarketDataAge > limits.MaxMarketDataAge {
		return Reservation{}, errors.New("market data is stale")
	}
	if now.IsZero() {
		now = time.Now().UTC()
	}
	return Reservation{
		TenantID:    req.TenantID,
		AccountID:   req.AccountID,
		ExecutionID: req.ExecutionID,
		ReservedUSD: req.OrderNotionalUSD,
		ApprovedAt:  now,
		ExpiresAt:   now.Add(limits.MaxMarketDataAge),
	}, nil
}
