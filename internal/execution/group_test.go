package execution

import (
	"encoding/json"
	"reflect"
	"testing"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

func intent(venue domain.Venue, side domain.Side) domain.OrderIntent {
	return domain.OrderIntent{
		TenantID:       "tenant-1",
		AccountID:      "account-1",
		ExecutionID:    "execution-1",
		Venue:          venue,
		InstrumentID:   "DOGE-PERP",
		Side:           side,
		Type:           domain.OrderTypeLimit,
		TimeInForce:    domain.TimeInForceIOC,
		BaseQuantity:   fixed.MustParse("100"),
		LimitPrice:     fixed.MustParse("0.2"),
		IdempotencyKey: string(venue) + "-entry",
	}
}

func preparedGroup(t *testing.T) Group {
	t.Helper()
	g, err := NewGroup("execution-1", "paired-entry-1", intent(domain.VenueHyperliquid, domain.SideBuy), intent(domain.VenueLighter, domain.SideSell), time.Unix(1, 0).UTC())
	if err != nil {
		t.Fatal(err)
	}
	for _, event := range []Event{
		{Kind: EventPreflightPassed},
		{Kind: EventRiskReserved, RiskReservation: fixed.MustParse("50")},
	} {
		g, err = Transition(g, event)
		if err != nil {
			t.Fatal(err)
		}
	}
	return g
}

func TestResidualHedgeWaitsForAuthoritativeTerminalLegs(t *testing.T) {
	g := preparedGroup(t)
	var err error
	for _, event := range []Event{
		{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a"},
		{Kind: EventLegSubmitted, LegIndex: 1, ClientOrderID: "engine-b"},
		{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-a"},
		{Kind: EventLegAcknowledged, LegIndex: 1, ClientOrderID: "engine-b", VenueOrderID: "venue-b"},
		{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("100")},
		{Kind: EventLegFillObserved, LegIndex: 1, CumulativeFill: fixed.MustParse("70")},
	} {
		g, err = Transition(g, event)
		if err != nil {
			t.Fatal(err)
		}
	}
	if g.ResidualDelta.String() != "30" || g.Status != StatusPartiallyFilled {
		t.Fatalf("unexpected partial state: status=%s residual=%s", g.Status, g.ResidualDelta)
	}
	if _, err = Transition(g, Event{Kind: EventHedgeStarted}); err == nil {
		t.Fatal("hedge must wait until the still-open short leg is terminal")
	}
	g, err = Transition(g, Event{Kind: EventLegCancelled, LegIndex: 1})
	if err != nil {
		t.Fatal(err)
	}
	if !g.ReadyForResidualHedge() {
		t.Fatal("expected authoritative residual to be hedgeable")
	}
	g, err = Transition(g, Event{Kind: EventHedgeStarted})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventHedgeCompleted, HedgeDelta: fixed.MustParse("-30")})
	if err != nil {
		t.Fatal(err)
	}
	if g.Status != StatusOpen || !g.ResidualDelta.IsZero() {
		t.Fatalf("expected neutral open state, got status=%s residual=%s", g.Status, g.ResidualDelta)
	}
}

func TestUnknownBlocksRetryUntilReconciliation(t *testing.T) {
	g := preparedGroup(t)
	var err error
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "stable-client-id"})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventLegUnknown, LegIndex: 0})
	if err != nil {
		t.Fatal(err)
	}
	if g.CanSubmitLeg(1) {
		t.Fatal("unknown outcome must freeze new submissions")
	}
	if _, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "different-id"}); err == nil {
		t.Fatal("blind retry must be rejected")
	}
	g, err = Transition(g, Event{Kind: EventLegReconciled, LegIndex: 0, ReconciledStatus: domain.OrderStatusFilled, CumulativeFill: fixed.MustParse("100"), VenueOrderID: "found-order"})
	if err != nil {
		t.Fatal(err)
	}
	if !g.CanSubmitLeg(1) {
		t.Fatal("second leg may submit only after authoritative reconciliation")
	}
}

func TestCumulativeFillIsIdempotentAndMonotonic(t *testing.T) {
	g := preparedGroup(t)
	var err error
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")})
	if err != nil {
		t.Fatal(err)
	}
	version := g.Version
	g, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")})
	if err != nil || g.Version != version {
		t.Fatalf("duplicate cumulative fill must be a no-op: version=%d err=%v", g.Version, err)
	}
	if _, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("24")}); err == nil {
		t.Fatal("fill regression must be rejected")
	}
}

func TestSecondLegSubmitPreservesPartiallyFilled(t *testing.T) {
	g := preparedGroup(t)
	var err error
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a"})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 1, ClientOrderID: "engine-b"})
	if err != nil {
		t.Fatal(err)
	}
	if g.Status != StatusPartiallyFilled {
		t.Fatalf("second-leg submit regressed aggregate status to %s", g.Status)
	}
	if g.Legs[1].Status != domain.OrderStatusSubmitted {
		t.Fatalf("expected submitted second leg, got %s", g.Legs[1].Status)
	}
}

func TestCumulativeFillDuplicatePolicy(t *testing.T) {
	type setupFunc func(*testing.T) Group
	apply := func(t *testing.T, events ...Event) Group {
		t.Helper()
		g := preparedGroup(t)
		var err error
		for _, event := range events {
			g, err = Transition(g, event)
			if err != nil {
				t.Fatal(err)
			}
		}
		return g
	}
	cases := []struct {
		name    string
		setup   setupFunc
		fill    string
		wantErr bool
	}{
		{
			name: "active partial replay",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")},
				)
			},
			fill: "25",
		},
		{
			name: "active reconciled open replay",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegUnknown, LegIndex: 0},
					Event{Kind: EventLegReconciled, LegIndex: 0, VenueOrderID: "venue-a", ReconciledStatus: domain.OrderStatusOpen, CumulativeFill: fixed.MustParse("25")},
				)
			},
			fill: "25",
		},
		{
			name: "terminal filled replay",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("100")},
				)
			},
			fill: "100",
		},
		{
			name: "partial cancel replay",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")},
					Event{Kind: EventLegCancelled, LegIndex: 0},
				)
			},
			fill: "25",
		},
		{
			name:    "pending zero is not evidence",
			setup:   preparedGroup,
			fill:    "0",
			wantErr: true,
		},
		{
			name: "submitted zero is not evidence",
			setup: func(t *testing.T) Group {
				return apply(t, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"})
			},
			fill:    "0",
			wantErr: true,
		},
		{
			name: "rejected before fill",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegRejected, LegIndex: 0},
				)
			},
			fill:    "0",
			wantErr: true,
		},
		{
			name: "rejected cannot receive first positive fill",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegRejected, LegIndex: 0},
				)
			},
			fill:    "25",
			wantErr: true,
		},
		{
			name: "unknown before fill",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegUnknown, LegIndex: 0},
				)
			},
			fill:    "0",
			wantErr: true,
		},
		{
			name: "unknown cannot receive first positive fill",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegUnknown, LegIndex: 0},
				)
			},
			fill:    "25",
			wantErr: true,
		},
		{
			name: "rejected equal positive is wrong state",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")},
					Event{Kind: EventLegRejected, LegIndex: 0},
				)
			},
			fill:    "25",
			wantErr: true,
		},
		{
			name: "unknown equal positive is wrong state",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")},
					Event{Kind: EventLegUnknown, LegIndex: 0},
				)
			},
			fill:    "25",
			wantErr: true,
		},
		{
			name: "lower cumulative fill",
			setup: func(t *testing.T) Group {
				return apply(t,
					Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"},
					Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("25")},
				)
			},
			fill:    "24",
			wantErr: true,
		},
		{
			name: "overfill",
			setup: func(t *testing.T) Group {
				return apply(t, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"})
			},
			fill:    "101",
			wantErr: true,
		},
		{
			name: "negative fill",
			setup: func(t *testing.T) Group {
				return apply(t, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "a"})
			},
			fill:    "-1",
			wantErr: true,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			before := tc.setup(t)
			after, err := Transition(before, Event{
				Kind:           EventLegFillObserved,
				LegIndex:       0,
				CumulativeFill: fixed.MustParse(tc.fill),
				At:             time.Unix(99, 0).UTC(),
			})
			if tc.wantErr {
				if err == nil {
					t.Fatal("expected contradictory fill evidence to fail closed")
				}
				if !reflect.DeepEqual(after, before) {
					t.Fatal("rejected fill event mutated group")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(after, before) {
				t.Fatalf("duplicate fill changed group:\nbefore=%+v\nafter=%+v", before, after)
			}
		})
	}
}

func TestAcknowledgementAfterEarlyFillRequiresClientOrderCorrelation(t *testing.T) {
	for _, fill := range []string{"25", "100"} {
		t.Run(fill, func(t *testing.T) {
			g := preparedGroup(t)
			var err error
			g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a"})
			if err != nil {
				t.Fatal(err)
			}
			g, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse(fill)})
			if err != nil {
				t.Fatal(err)
			}
			before := g
			if _, err = Transition(g, Event{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "foreign-client", VenueOrderID: "venue-a"}); err == nil {
				t.Fatal("ack with foreign client order id must fail closed")
			}
			if !reflect.DeepEqual(g, before) {
				t.Fatal("input group mutated after rejected ack")
			}
			g, err = Transition(g, Event{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-a"})
			if err != nil {
				t.Fatal(err)
			}
			if g.Legs[0].VenueOrderID != "venue-a" {
				t.Fatal("matching late ack did not attach venue order id")
			}
			wantStatus := domain.OrderStatusPartial
			if fill == "100" {
				wantStatus = domain.OrderStatusFilled
			}
			if g.Legs[0].Status != wantStatus {
				t.Fatalf("late ack changed fill-derived status to %s", g.Legs[0].Status)
			}
			version := g.Version
			g, err = Transition(g, Event{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-a"})
			if err != nil || g.Version != version {
				t.Fatalf("exact duplicate ack must be a no-op: version=%d err=%v", g.Version, err)
			}
			if _, err = Transition(g, Event{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-b"}); err == nil {
				t.Fatal("conflicting venue order id must fail closed")
			}
		})
	}
}

func TestRestartReplayIsDeterministicAtDomainBoundary(t *testing.T) {
	g := preparedGroup(t)
	var err error
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a", At: time.Unix(10, 0).UTC()})
	if err != nil {
		t.Fatal(err)
	}
	g, err = Transition(g, Event{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("100"), At: time.Unix(11, 0).UTC()})
	if err != nil {
		t.Fatal(err)
	}

	encoded, err := json.Marshal(g)
	if err != nil {
		t.Fatal(err)
	}
	var restored Group
	if err = json.Unmarshal(encoded, &restored); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(restored, g) {
		t.Fatalf("JSON restore changed group:\nbefore=%+v\nafter=%+v", g, restored)
	}

	baseline := restored
	for _, replay := range []Event{
		{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a", At: time.Unix(12, 0).UTC()},
		{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("100"), At: time.Unix(13, 0).UTC()},
	} {
		restored, err = Transition(restored, replay)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(restored, baseline) {
			t.Fatalf("duplicate replay changed restored state: %+v", restored)
		}
	}

	restored, err = Transition(restored, Event{
		Kind:          EventLegAcknowledged,
		LegIndex:      0,
		ClientOrderID: "engine-a",
		VenueOrderID:  "venue-a",
		At:            time.Unix(14, 0).UTC(),
	})
	if err != nil {
		t.Fatal(err)
	}
	acknowledged := restored
	if acknowledged.Version != baseline.Version+1 ||
		acknowledged.Legs[0].VenueOrderID != "venue-a" ||
		acknowledged.Legs[0].FilledQuantity != fixed.MustParse("100") ||
		acknowledged.Legs[0].Status != domain.OrderStatusFilled {
		t.Fatalf("unexpected acknowledged state after restart: %+v", acknowledged)
	}

	for _, replay := range []Event{
		{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-a", At: time.Unix(15, 0).UTC()},
		{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("100"), At: time.Unix(16, 0).UTC()},
	} {
		restored, err = Transition(restored, replay)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(restored, acknowledged) {
			t.Fatalf("post-restart duplicate changed state: %+v", restored)
		}
	}

	for _, contradiction := range []Event{
		{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "engine-a", VenueOrderID: "venue-conflict"},
		{Kind: EventLegAcknowledged, LegIndex: 0, ClientOrderID: "foreign-client", VenueOrderID: "venue-a"},
		{Kind: EventLegFillObserved, LegIndex: 0, CumulativeFill: fixed.MustParse("99")},
	} {
		after, transitionErr := Transition(restored, contradiction)
		if transitionErr == nil {
			t.Fatalf("contradiction %+v did not fail closed", contradiction)
		}
		if !reflect.DeepEqual(after, acknowledged) {
			t.Fatalf("contradiction %+v mutated state", contradiction)
		}
	}
}

func TestRestoredSubmittedLegWithPositiveFillFailsClosed(t *testing.T) {
	g := preparedGroup(t)
	var err error
	g, err = Transition(g, Event{Kind: EventLegSubmitted, LegIndex: 0, ClientOrderID: "engine-a"})
	if err != nil {
		t.Fatal(err)
	}
	g.Legs[0].FilledQuantity = fixed.MustParse("25")

	encoded, err := json.Marshal(g)
	if err != nil {
		t.Fatal(err)
	}
	var restored Group
	if err = json.Unmarshal(encoded, &restored); err != nil {
		t.Fatal(err)
	}
	if restored.Legs[0].Status != domain.OrderStatusSubmitted {
		t.Fatalf("fixture must restore submitted status, got %s", restored.Legs[0].Status)
	}
	before := restored
	after, err := Transition(restored, Event{
		Kind:           EventLegFillObserved,
		LegIndex:       0,
		CumulativeFill: fixed.MustParse("25"),
		At:             time.Unix(99, 0).UTC(),
	})
	if err == nil {
		t.Fatal("submitted leg with positive stored fill must fail closed")
	}
	if !reflect.DeepEqual(after, before) || after.Version != before.Version {
		t.Fatalf("rejected restored fill mutated group:\nbefore=%+v\nafter=%+v", before, after)
	}
}
