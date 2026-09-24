package reconcile

import (
	"testing"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

func reconcileIntent() domain.OrderIntent {
	return domain.OrderIntent{
		TenantID: "t", AccountID: "a", ExecutionID: "e", Venue: domain.VenueLighter,
		InstrumentID: "DOGE-PERP", Side: domain.SideSell, Type: domain.OrderTypeLimit,
		TimeInForce: domain.TimeInForceIOC, BaseQuantity: fixed.MustParse("100"), LimitPrice: fixed.MustParse("0.2"),
		ClientOrderID: "stable-id", IdempotencyKey: "idem",
	}
}

func reconcileOpenOrder() domain.OrderSnapshot {
	intent := reconcileIntent()
	return domain.OrderSnapshot{
		OrderRef: domain.OrderRef{
			TenantID:      intent.TenantID,
			AccountID:     intent.AccountID,
			Venue:         intent.Venue,
			InstrumentID:  intent.InstrumentID,
			ClientOrderID: intent.ClientOrderID,
			VenueOrderID:  "venue-order",
		},
		Status:         domain.OrderStatusOpen,
		Side:           intent.Side,
		BaseQuantity:   intent.BaseQuantity,
		FilledQuantity: fixed.MustParse("25"),
	}
}

func TestRetryNeedsCompleteAuthoritativeEvidence(t *testing.T) {
	decision, err := Decide(reconcileIntent(), Evidence{SnapshotFresh: true, Authoritative: true, ClientOrderLookupComplete: true})
	if err != nil || decision.Action != ActionRetryAllowed {
		t.Fatalf("expected retry, got %+v err=%v", decision, err)
	}
	decision, err = Decide(reconcileIntent(), Evidence{SnapshotFresh: true, Authoritative: true})
	if err != nil || decision.Action != ActionHoldAndReconcile {
		t.Fatalf("incomplete lookup must hold, got %+v err=%v", decision, err)
	}
}

func TestUnattributedPositionDeltaRequiresManualAction(t *testing.T) {
	decision, err := Decide(reconcileIntent(), Evidence{
		SnapshotFresh: true, Authoritative: true, ClientOrderLookupComplete: true, PositionDeltaBase: fixed.MustParse("5"),
	})
	if err != nil || decision.Action != ActionManualRequired {
		t.Fatalf("expected manual action, got %+v err=%v", decision, err)
	}
}

func TestAdoptOpenOrderRequiresCompleteIdentity(t *testing.T) {
	cases := []struct {
		name   string
		mutate func(*domain.OrderSnapshot)
	}{
		{name: "foreign tenant", mutate: func(order *domain.OrderSnapshot) { order.TenantID = "foreign" }},
		{name: "foreign account", mutate: func(order *domain.OrderSnapshot) { order.AccountID = "foreign" }},
		{name: "foreign venue", mutate: func(order *domain.OrderSnapshot) { order.Venue = domain.VenueHyperliquid }},
		{name: "foreign client order", mutate: func(order *domain.OrderSnapshot) { order.ClientOrderID = "foreign" }},
		{name: "foreign instrument", mutate: func(order *domain.OrderSnapshot) { order.InstrumentID = "BTC-PERP" }},
		{name: "wrong side", mutate: func(order *domain.OrderSnapshot) { order.Side = domain.SideBuy }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			order := reconcileOpenOrder()
			tc.mutate(&order)
			decision, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: order.FilledQuantity,
			})
			if err != nil {
				t.Fatal(err)
			}
			if decision.Action != ActionManualRequired {
				t.Fatalf("identity mismatch must require manual action, got %+v", decision)
			}
		})
	}
}

func TestAdoptOpenOrderRequiresAdoptableStatus(t *testing.T) {
	for _, status := range []domain.OrderStatus{
		domain.OrderStatusPending,
		domain.OrderStatusSubmitted,
		domain.OrderStatusFilled,
		domain.OrderStatusCancelled,
		domain.OrderStatusRejected,
		domain.OrderStatusUnknown,
		domain.OrderStatus("invalid"),
	} {
		t.Run(string(status), func(t *testing.T) {
			order := reconcileOpenOrder()
			order.Status = status
			if _, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: order.FilledQuantity,
			}); err == nil {
				t.Fatalf("status %q must not be adopted as open", status)
			}
		})
	}
	for _, status := range []domain.OrderStatus{domain.OrderStatusOpen, domain.OrderStatusPartial} {
		t.Run("adopt_"+string(status), func(t *testing.T) {
			order := reconcileOpenOrder()
			order.Status = status
			decision, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: order.FilledQuantity,
			})
			if err != nil || decision.Action != ActionAdoptOpen || decision.Status != status {
				t.Fatalf("expected status %q to be adopted, got %+v err=%v", status, decision, err)
			}
		})
	}
}

func TestAdoptOpenOrderValidatesFilledQuantity(t *testing.T) {
	for _, fill := range []string{"-1", "101"} {
		t.Run(fill, func(t *testing.T) {
			order := reconcileOpenOrder()
			order.FilledQuantity = fixed.MustParse(fill)
			if _, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: fixed.Zero(),
			}); err == nil {
				t.Fatalf("open-order fill %s must fail closed", fill)
			}
		})
	}
}

func TestAdoptOpenOrderRejectsContradictoryFillEvidence(t *testing.T) {
	for _, cumulative := range []string{"20", "30"} {
		t.Run(cumulative, func(t *testing.T) {
			order := reconcileOpenOrder()
			if _, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: fixed.MustParse(cumulative),
			}); err == nil {
				t.Fatalf("open fill %s and cumulative fill %s must fail closed", order.FilledQuantity, cumulative)
			}
		})
	}
}

func TestAdoptOpenOrderRequiresExactBaseQuantity(t *testing.T) {
	for _, quantity := range []string{"99", "101"} {
		t.Run(quantity, func(t *testing.T) {
			order := reconcileOpenOrder()
			order.BaseQuantity = fixed.MustParse(quantity)
			decision, err := Decide(reconcileIntent(), Evidence{
				SnapshotFresh:    true,
				Authoritative:    true,
				OpenOrder:        &order,
				CumulativeFilled: order.FilledQuantity,
			})
			if err != nil {
				t.Fatal(err)
			}
			if decision.Action != ActionManualRequired {
				t.Fatalf("quantity mismatch must freeze for manual action, got %+v", decision)
			}
			if decision.Action == ActionAdoptOpen {
				t.Fatal("quantity mismatch must never adopt the open order")
			}
		})
	}
}
