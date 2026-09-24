// Package ownership keeps exact system-order ownership. It deliberately has no
// symbol-prefix or "cancel all" fallback.
package ownership

import (
	"errors"
	"sort"
	"sync"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
)

type Key struct {
	TenantID      domain.TenantID
	AccountID     domain.AccountID
	Venue         domain.Venue
	ClientOrderID string
}

type Record struct {
	Key
	ExecutionID  domain.ExecutionID
	VenueOrderID string
}

type Registry struct {
	mu      sync.RWMutex
	records map[Key]Record
}

func NewRegistry() *Registry {
	return &Registry{records: make(map[Key]Record)}
}

func (r *Registry) Claim(record Record) error {
	if record.TenantID == "" || record.AccountID == "" || record.Venue == "" || record.ClientOrderID == "" || record.ExecutionID == "" {
		return errors.New("complete ownership identity is required")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if existing, ok := r.records[record.Key]; ok && existing.ExecutionID != record.ExecutionID {
		return errors.New("client order id already belongs to another execution")
	}
	r.records[record.Key] = record
	return nil
}

func (r *Registry) Owns(order domain.OrderSnapshot) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	record, ok := r.records[Key{
		TenantID: order.TenantID, AccountID: order.AccountID, Venue: order.Venue, ClientOrderID: order.ClientOrderID,
	}]
	if !ok {
		return false
	}
	return record.VenueOrderID == "" || order.VenueOrderID == "" || record.VenueOrderID == order.VenueOrderID
}

func (r *Registry) Cancellable(orders []domain.OrderSnapshot) []domain.OrderRef {
	result := make([]domain.OrderRef, 0, len(orders))
	for _, order := range orders {
		if (order.Status == domain.OrderStatusOpen || order.Status == domain.OrderStatusPartial || order.Status == domain.OrderStatusSubmitted) && r.Owns(order) {
			result = append(result, order.OrderRef)
		}
	}
	sort.Slice(result, func(i, j int) bool {
		if result[i].Venue == result[j].Venue {
			return result[i].ClientOrderID < result[j].ClientOrderID
		}
		return result[i].Venue < result[j].Venue
	})
	return result
}
