// Package reconcile decides what evidence is sufficient after an unknown order
// outcome. Absence in one endpoint never authorizes a blind retry.
package reconcile

import (
	"errors"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

type Action string

const (
	ActionAdoptOpen        Action = "adopt_open"
	ActionApplyFill        Action = "apply_fill"
	ActionRetryAllowed     Action = "retry_allowed"
	ActionHoldAndReconcile Action = "hold_and_reconcile"
	ActionManualRequired   Action = "manual_required"
)

type Evidence struct {
	SnapshotFresh             bool
	Authoritative             bool
	ClientOrderLookupComplete bool
	OpenOrder                 *domain.OrderSnapshot
	CumulativeFilled          fixed.Value
	PositionDeltaBase         fixed.Value
}

type Decision struct {
	Action         Action
	Status         domain.OrderStatus
	CumulativeFill fixed.Value
	Reason         string
}

func Decide(intent domain.OrderIntent, evidence Evidence) (Decision, error) {
	if err := intent.Validate(); err != nil {
		return Decision{}, err
	}
	if !evidence.SnapshotFresh || !evidence.Authoritative {
		return Decision{Action: ActionHoldAndReconcile, Reason: "snapshot is stale or incomplete"}, nil
	}
	if evidence.CumulativeFilled.IsNegative() || evidence.CumulativeFilled.Cmp(intent.BaseQuantity) > 0 {
		return Decision{}, errors.New("fill evidence violates order quantity")
	}
	if evidence.OpenOrder != nil {
		if evidence.OpenOrder.TenantID != intent.TenantID ||
			evidence.OpenOrder.AccountID != intent.AccountID ||
			evidence.OpenOrder.Venue != intent.Venue ||
			evidence.OpenOrder.ClientOrderID != intent.ClientOrderID ||
			evidence.OpenOrder.InstrumentID != intent.InstrumentID ||
			evidence.OpenOrder.Side != intent.Side ||
			evidence.OpenOrder.BaseQuantity != intent.BaseQuantity {
			return Decision{Action: ActionManualRequired, Reason: "open order identity mismatch"}, nil
		}
		if !adoptableOpenStatus(evidence.OpenOrder.Status) {
			return Decision{}, errors.New("open order status is not adoptable")
		}
		if evidence.OpenOrder.FilledQuantity.IsNegative() || evidence.OpenOrder.FilledQuantity.Cmp(intent.BaseQuantity) > 0 {
			return Decision{}, errors.New("open order fill violates order quantity")
		}
		if evidence.OpenOrder.FilledQuantity != evidence.CumulativeFilled {
			return Decision{}, errors.New("open order fill contradicts cumulative fill evidence")
		}
		return Decision{Action: ActionAdoptOpen, Status: evidence.OpenOrder.Status, CumulativeFill: evidence.OpenOrder.FilledQuantity}, nil
	}
	if evidence.CumulativeFilled.IsPositive() {
		status := domain.OrderStatusPartial
		if evidence.CumulativeFilled == intent.BaseQuantity {
			status = domain.OrderStatusFilled
		}
		return Decision{Action: ActionApplyFill, Status: status, CumulativeFill: evidence.CumulativeFilled}, nil
	}
	if !evidence.PositionDeltaBase.IsZero() {
		return Decision{Action: ActionManualRequired, Reason: "position changed without attributable order or fill"}, nil
	}
	if !evidence.ClientOrderLookupComplete {
		return Decision{Action: ActionHoldAndReconcile, Reason: "client order lookup is incomplete"}, nil
	}
	return Decision{Action: ActionRetryAllowed, Status: domain.OrderStatusCancelled, Reason: "authoritative lookup found no order, fill, or position delta"}, nil
}

func adoptableOpenStatus(status domain.OrderStatus) bool {
	return status == domain.OrderStatusOpen || status == domain.OrderStatusPartial
}
