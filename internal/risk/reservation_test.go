package risk

import (
	"testing"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/domain"
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
)

func testLimits() Limits {
	return Limits{
		MaxOrderNotionalUSD: fixed.MustParse("100"),
		MaxGrossExposureUSD: fixed.MustParse("1000"),
		MaxAbsNetDeltaBase:  fixed.MustParse("25"),
		MaxUnhedgedDuration: 2 * time.Second,
		MaxDailyLossUSD:     fixed.MustParse("50"),
		MaxDrawdownUSD:      fixed.MustParse("100"),
		MaxSlippageBPS:      15,
		MinMarginBufferBPS:  3000,
		MaxMarketDataAge:    500 * time.Millisecond,
	}
}

func validRequest() Request {
	return Request{
		TenantID:              "tenant-1",
		AccountID:             "account-1",
		ExecutionID:           "execution-1",
		OrderNotionalUSD:      fixed.MustParse("50"),
		GrossExposureAfterUSD: fixed.MustParse("500"),
		AbsNetDeltaAfterBase:  fixed.MustParse("10"),
		MaxUnhedgedDuration:   time.Second,
		DailyLossUSD:          fixed.MustParse("1"),
		DrawdownUSD:           fixed.MustParse("2"),
		ExpectedSlippageBPS:   5,
		MarginBufferBPS:       4000,
		MarketDataAge:         100 * time.Millisecond,
		LongVenueHealth:       domain.VenueHealthy,
		ShortVenueHealth:      domain.VenueHealthy,
	}
}

func TestEvaluateApprovesBoundedRequest(t *testing.T) {
	r, err := Evaluate(testLimits(), validRequest(), time.Unix(10, 0).UTC())
	if err != nil {
		t.Fatal(err)
	}
	if r.ReservedUSD.String() != "50" || !r.ExpiresAt.After(r.ApprovedAt) {
		t.Fatalf("unexpected reservation: %+v", r)
	}
}

func TestEvaluateFailsClosedOnVenueOrStaleness(t *testing.T) {
	req := validRequest()
	req.ShortVenueHealth = domain.VenueDegraded
	if _, err := Evaluate(testLimits(), req, time.Time{}); err == nil {
		t.Fatal("degraded venue must reject reservation")
	}
	req = validRequest()
	req.MarketDataAge = time.Second
	if _, err := Evaluate(testLimits(), req, time.Time{}); err == nil {
		t.Fatal("stale data must reject reservation")
	}
}
