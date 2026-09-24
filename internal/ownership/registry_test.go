package ownership

import (
	"testing"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
)

func TestCancellableReturnsOnlyExactOwnedOrders(t *testing.T) {
	r := NewRegistry()
	if err := r.Claim(Record{Key: Key{TenantID: "t", AccountID: "a", Venue: domain.VenueHyperliquid, ClientOrderID: "engine-1"}, ExecutionID: "e", VenueOrderID: "venue-1"}); err != nil {
		t.Fatal(err)
	}
	orders := []domain.OrderSnapshot{
		{OrderRef: domain.OrderRef{TenantID: "t", AccountID: "a", Venue: domain.VenueHyperliquid, ClientOrderID: "engine-1", VenueOrderID: "venue-1"}, Status: domain.OrderStatusOpen},
		{OrderRef: domain.OrderRef{TenantID: "t", AccountID: "a", Venue: domain.VenueHyperliquid, ClientOrderID: "manual-1", VenueOrderID: "venue-2"}, Status: domain.OrderStatusOpen},
		{OrderRef: domain.OrderRef{TenantID: "other-tenant", AccountID: "a", Venue: domain.VenueHyperliquid, ClientOrderID: "engine-1", VenueOrderID: "venue-1"}, Status: domain.OrderStatusOpen},
	}
	got := r.Cancellable(orders)
	if len(got) != 1 || got[0].ClientOrderID != "engine-1" {
		t.Fatalf("expected only exact owned order, got %+v", got)
	}
}

func TestOwnershipConflictFailsClosed(t *testing.T) {
	r := NewRegistry()
	key := Key{TenantID: "t", AccountID: "a", Venue: domain.VenueLighter, ClientOrderID: "same"}
	if err := r.Claim(Record{Key: key, ExecutionID: "e1"}); err != nil {
		t.Fatal(err)
	}
	if err := r.Claim(Record{Key: key, ExecutionID: "e2"}); err == nil {
		t.Fatal("conflicting ownership must be rejected")
	}
}
