// Package execution contains the pure paired-execution reducer used by live,
// shadow, replay, and recovery paths.
package execution

import (
	"errors"
	"fmt"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type Status string

const (
	StatusCreated            Status = "created"
	StatusPreflightOK        Status = "preflight_ok"
	StatusReserved           Status = "reserved"
	StatusSubmitting         Status = "submitting"
	StatusPartiallyFilled    Status = "partially_filled"
	StatusReconciling        Status = "reconciling"
	StatusHedging            Status = "hedging"
	StatusOpen               Status = "open"
	StatusClosing            Status = "closing"
	StatusClosed             Status = "closed"
	StatusFailed             Status = "failed"
	StatusManualIntervention Status = "manual_intervention"
)

type Leg struct {
	Intent         domain.OrderIntent `json:"intent"`
	VenueOrderID   string             `json:"venue_order_id,omitempty"`
	ClientOrderID  string             `json:"client_order_id,omitempty"`
	Status         domain.OrderStatus `json:"status"`
	FilledQuantity fixed.Value        `json:"filled_quantity"`
}

type Group struct {
	ID              domain.ExecutionID `json:"id"`
	TenantID        domain.TenantID    `json:"tenant_id"`
	AccountID       domain.AccountID   `json:"account_id"`
	IdempotencyKey  string             `json:"idempotency_key"`
	Status          Status             `json:"status"`
	Legs            [2]Leg             `json:"legs"`
	RiskReservation fixed.Value        `json:"risk_reservation"`
	PrimaryDelta    fixed.Value        `json:"primary_delta"`
	HedgeDelta      fixed.Value        `json:"hedge_delta"`
	ResidualDelta   fixed.Value        `json:"residual_delta"`
	FailureReason   string             `json:"failure_reason,omitempty"`
	Version         int64              `json:"version"`
	CreatedAt       time.Time          `json:"created_at"`
	UpdatedAt       time.Time          `json:"updated_at"`
}

func NewGroup(id domain.ExecutionID, idempotencyKey string, first, second domain.OrderIntent, now time.Time) (Group, error) {
	if id == "" || idempotencyKey == "" {
		return Group{}, errors.New("execution id and idempotency key are required")
	}
	if err := first.Validate(); err != nil {
		return Group{}, fmt.Errorf("first leg: %w", err)
	}
	if err := second.Validate(); err != nil {
		return Group{}, fmt.Errorf("second leg: %w", err)
	}
	if first.ExecutionID != id || second.ExecutionID != id {
		return Group{}, errors.New("leg execution ids must match group id")
	}
	if first.TenantID != second.TenantID || first.AccountID != second.AccountID {
		return Group{}, errors.New("legs must share tenant and account")
	}
	if first.InstrumentID != second.InstrumentID {
		return Group{}, errors.New("legs must use the same canonical instrument")
	}
	if first.Venue == second.Venue {
		return Group{}, errors.New("paired legs must use different venues")
	}
	if first.Side == second.Side {
		return Group{}, errors.New("paired legs must use opposite sides")
	}
	if first.BaseQuantity != second.BaseQuantity {
		return Group{}, errors.New("initial paired quantities must match")
	}
	if now.IsZero() {
		now = time.Now().UTC()
	}
	return Group{
		ID:             id,
		TenantID:       first.TenantID,
		AccountID:      first.AccountID,
		IdempotencyKey: idempotencyKey,
		Status:         StatusCreated,
		Legs: [2]Leg{
			{Intent: first, Status: domain.OrderStatusPending},
			{Intent: second, Status: domain.OrderStatusPending},
		},
		CreatedAt: now,
		UpdatedAt: now,
	}, nil
}

type EventKind string

const (
	EventPreflightPassed EventKind = "preflight_passed"
	EventRiskReserved    EventKind = "risk_reserved"
	EventLegSubmitted    EventKind = "leg_submitted"
	EventLegAcknowledged EventKind = "leg_acknowledged"
	EventLegFillObserved EventKind = "leg_fill_observed"
	EventLegCancelled    EventKind = "leg_cancelled"
	EventLegRejected     EventKind = "leg_rejected"
	EventLegUnknown      EventKind = "leg_unknown"
	EventLegReconciled   EventKind = "leg_reconciled"
	EventHedgeStarted    EventKind = "hedge_started"
	EventHedgeCompleted  EventKind = "hedge_completed"
	EventCloseStarted    EventKind = "close_started"
	EventClosed          EventKind = "closed"
	EventFailed          EventKind = "failed"
	EventManualRequired  EventKind = "manual_required"
)

type Event struct {
	Kind             EventKind
	LegIndex         int
	ClientOrderID    string
	VenueOrderID     string
	CumulativeFill   fixed.Value
	ReconciledStatus domain.OrderStatus
	RiskReservation  fixed.Value
	HedgeDelta       fixed.Value
	Reason           string
	At               time.Time
}

// Transition applies one event without mutating current, so replay and live
// execution can share exactly the same reducer.
func Transition(current Group, event Event) (Group, error) {
	next := current
	changed := true

	switch event.Kind {
	case EventPreflightPassed:
		if current.Status != StatusCreated {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Status = StatusPreflightOK

	case EventRiskReserved:
		if current.Status != StatusPreflightOK || !event.RiskReservation.IsPositive() {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.RiskReservation = event.RiskReservation
		next.Status = StatusReserved

	case EventLegSubmitted:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if leg.Status != domain.OrderStatusPending {
			if leg.ClientOrderID == event.ClientOrderID && event.ClientOrderID != "" {
				changed = false
				break
			}
			return current, errors.New("leg already submitted; blind retry forbidden")
		}
		if !current.CanSubmitLeg(event.LegIndex) || event.ClientOrderID == "" {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Legs[event.LegIndex].ClientOrderID = event.ClientOrderID
		next.Legs[event.LegIndex].Status = domain.OrderStatusSubmitted
		if current.Status == StatusReserved {
			next.Status = StatusSubmitting
		}

	case EventLegAcknowledged:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if event.ClientOrderID == "" || event.ClientOrderID != leg.ClientOrderID || event.VenueOrderID == "" {
			return current, errors.New("acknowledgement identity does not match submitted leg")
		}
		if leg.VenueOrderID != "" {
			if leg.VenueOrderID != event.VenueOrderID {
				return current, errors.New("acknowledgement conflicts with recorded venue order id")
			}
			changed = false
			break
		}
		if !acknowledgeableOrder(leg.Status) {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Legs[event.LegIndex].VenueOrderID = event.VenueOrderID
		if leg.Status == domain.OrderStatusSubmitted {
			next.Legs[event.LegIndex].Status = domain.OrderStatusOpen
		}

	case EventLegFillObserved:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if event.CumulativeFill.Cmp(leg.FilledQuantity) < 0 || event.CumulativeFill.Cmp(leg.Intent.BaseQuantity) > 0 {
			return current, errors.New("cumulative fill must be monotonic and not exceed intent")
		}
		if event.CumulativeFill == leg.FilledQuantity {
			if !duplicateCumulativeFillRecorded(leg, event.CumulativeFill) {
				return current, errors.New("equal cumulative fill is not valid evidence for leg state")
			}
			changed = false
			break
		}
		if !activeOrder(leg.Status) {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Legs[event.LegIndex].FilledQuantity = event.CumulativeFill
		if event.CumulativeFill == leg.Intent.BaseQuantity {
			next.Legs[event.LegIndex].Status = domain.OrderStatusFilled
		} else {
			next.Legs[event.LegIndex].Status = domain.OrderStatusPartial
		}
		if err := next.recomputePrimaryState(); err != nil {
			return current, err
		}

	case EventLegCancelled, EventLegRejected:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if !activeOrder(leg.Status) {
			return current, invalidTransition(current.Status, event.Kind)
		}
		if event.Kind == EventLegCancelled {
			next.Legs[event.LegIndex].Status = domain.OrderStatusCancelled
		} else {
			next.Legs[event.LegIndex].Status = domain.OrderStatusRejected
		}
		if err := next.recomputePrimaryState(); err != nil {
			return current, err
		}

	case EventLegUnknown:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if !activeOrder(leg.Status) {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Legs[event.LegIndex].Status = domain.OrderStatusUnknown
		next.Status = StatusReconciling

	case EventLegReconciled:
		leg, err := current.leg(event.LegIndex)
		if err != nil {
			return current, err
		}
		if leg.Status != domain.OrderStatusUnknown || !reconciledStatus(event.ReconciledStatus) {
			return current, invalidTransition(current.Status, event.Kind)
		}
		if event.CumulativeFill.Cmp(leg.FilledQuantity) < 0 || event.CumulativeFill.Cmp(leg.Intent.BaseQuantity) > 0 {
			return current, errors.New("invalid reconciled cumulative fill")
		}
		next.Legs[event.LegIndex].Status = event.ReconciledStatus
		next.Legs[event.LegIndex].FilledQuantity = event.CumulativeFill
		if event.VenueOrderID != "" {
			next.Legs[event.LegIndex].VenueOrderID = event.VenueOrderID
		}
		if err := next.recomputePrimaryState(); err != nil {
			return current, err
		}

	case EventHedgeStarted:
		if !current.ReadyForResidualHedge() {
			return current, errors.New("residual hedge requires authoritative terminal state for both primary legs")
		}
		next.Status = StatusHedging

	case EventHedgeCompleted:
		if current.Status != StatusHedging {
			return current, invalidTransition(current.Status, event.Kind)
		}
		expected, err := current.ResidualDelta.Neg()
		if err != nil || event.HedgeDelta != expected {
			return current, errors.New("hedge delta must exactly neutralize authoritative residual")
		}
		next.HedgeDelta, err = current.HedgeDelta.Add(event.HedgeDelta)
		if err != nil {
			return current, err
		}
		if err := next.recomputeDelta(); err != nil {
			return current, err
		}
		next.Status = StatusOpen

	case EventCloseStarted:
		if current.Status != StatusOpen {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Status = StatusClosing

	case EventClosed:
		if current.Status != StatusClosing {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Status = StatusClosed

	case EventFailed:
		if current.Status == StatusClosed {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Status = StatusFailed
		next.FailureReason = event.Reason

	case EventManualRequired:
		if current.Status == StatusClosed {
			return current, invalidTransition(current.Status, event.Kind)
		}
		next.Status = StatusManualIntervention
		next.FailureReason = event.Reason

	default:
		return current, fmt.Errorf("unknown execution event %q", event.Kind)
	}

	if !changed {
		return current, nil
	}
	if event.At.IsZero() {
		event.At = time.Now().UTC()
	}
	next.UpdatedAt = event.At
	next.Version++
	if err := next.validate(); err != nil {
		return current, err
	}
	return next, nil
}

func (g Group) CanSubmitLeg(index int) bool {
	leg, err := g.leg(index)
	if err != nil || leg.Status != domain.OrderStatusPending || g.hasUnknown() {
		return false
	}
	return g.Status == StatusReserved || g.Status == StatusSubmitting || g.Status == StatusPartiallyFilled
}

func (g Group) ReadyForResidualHedge() bool {
	return g.Legs[0].Status.Terminal() && g.Legs[1].Status.Terminal() && !g.ResidualDelta.IsZero()
}

func (g Group) leg(index int) (Leg, error) {
	if index < 0 || index >= len(g.Legs) {
		return Leg{}, errors.New("leg index out of range")
	}
	return g.Legs[index], nil
}

func (g Group) hasUnknown() bool {
	return g.Legs[0].Status == domain.OrderStatusUnknown || g.Legs[1].Status == domain.OrderStatusUnknown
}

func (g *Group) recomputeDelta() error {
	delta := fixed.Zero()
	for _, leg := range g.Legs {
		quantity := leg.FilledQuantity
		if leg.Intent.Side == domain.SideSell {
			var err error
			quantity, err = quantity.Neg()
			if err != nil {
				return fmt.Errorf("negate filled quantity: %w", err)
			}
		}
		var err error
		delta, err = delta.Add(quantity)
		if err != nil {
			return fmt.Errorf("sum primary delta: %w", err)
		}
	}
	g.PrimaryDelta = delta
	var err error
	g.ResidualDelta, err = delta.Add(g.HedgeDelta)
	if err != nil {
		return fmt.Errorf("sum residual delta: %w", err)
	}
	return nil
}

func (g *Group) recomputePrimaryState() error {
	if err := g.recomputeDelta(); err != nil {
		return err
	}
	if g.hasUnknown() {
		g.Status = StatusReconciling
		return nil
	}
	if g.Status == StatusHedging || g.Status == StatusClosing || g.Status == StatusClosed || g.Status == StatusManualIntervention {
		return nil
	}
	allTerminal := g.Legs[0].Status.Terminal() && g.Legs[1].Status.Terminal()
	anyFill := !g.Legs[0].FilledQuantity.IsZero() || !g.Legs[1].FilledQuantity.IsZero()
	if allTerminal && g.ResidualDelta.IsZero() && anyFill {
		g.Status = StatusOpen
		return nil
	}
	if anyFill {
		g.Status = StatusPartiallyFilled
		return nil
	}
	if allTerminal {
		g.Status = StatusFailed
		g.FailureReason = "both primary legs ended without a fill"
		return nil
	}
	g.Status = StatusSubmitting
	return nil
}

func (g Group) validate() error {
	if g.TenantID == "" || g.AccountID == "" || g.ID == "" || g.IdempotencyKey == "" {
		return errors.New("execution identity invariant violated")
	}
	for i, leg := range g.Legs {
		if leg.FilledQuantity.IsNegative() || leg.FilledQuantity.Cmp(leg.Intent.BaseQuantity) > 0 {
			return fmt.Errorf("leg %d fill invariant violated", i)
		}
	}
	if g.Status == StatusOpen && !g.ResidualDelta.IsZero() {
		return errors.New("open execution must be delta neutral")
	}
	return nil
}

func activeOrder(status domain.OrderStatus) bool {
	return status == domain.OrderStatusSubmitted || status == domain.OrderStatusOpen || status == domain.OrderStatusPartial
}

func acknowledgeableOrder(status domain.OrderStatus) bool {
	return activeOrder(status) || status == domain.OrderStatusFilled
}

func duplicateCumulativeFillRecorded(leg Leg, cumulative fixed.Value) bool {
	if !cumulative.IsPositive() || cumulative != leg.FilledQuantity {
		return false
	}
	switch leg.Status {
	case domain.OrderStatusOpen, domain.OrderStatusPartial, domain.OrderStatusCancelled:
		return cumulative.Cmp(leg.Intent.BaseQuantity) < 0
	case domain.OrderStatusFilled:
		return cumulative == leg.Intent.BaseQuantity
	default:
		return false
	}
}

func reconciledStatus(status domain.OrderStatus) bool {
	return status == domain.OrderStatusOpen || status == domain.OrderStatusPartial || status.Terminal()
}

func invalidTransition(status Status, event EventKind) error {
	return fmt.Errorf("event %s is invalid from status %s", event, status)
}
