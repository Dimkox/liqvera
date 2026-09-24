package feasibility_test

import (
	"testing"

	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
	"github.com/Dimkox/multi-exchange-engine/internal/stagea/feasibility"
	"github.com/Dimkox/multi-exchange-engine/internal/stagea/model"
)

func TestEvaluateTenDollarLegHasNoMarginHeadroomWhenAnyReserveIsPositive(t *testing.T) {
	profile := feasibility.Profile{
		TotalCapitalUSD:    fixed.MustParse("10"),
		PerVenueCapitalUSD: fixed.MustParse("5"),
		Leverage:           fixed.MustParse("2"),
		PerLegNotionalUSD:  fixed.MustParse("10"),
	}

	for _, reserve := range []feasibility.CostReserve{
		{EntryFeeUSD: fixed.MustParse("0.00000001")},
		{ExitFeeUSD: fixed.MustParse("0.00000001")},
		{StressReserveUSD: fixed.MustParse("0.00000001")},
	} {
		assessment := feasibility.Evaluate(profile, reserve)
		if assessment.CapitalSupported {
			t.Errorf("Evaluate(%+v) unexpectedly supports the boundary profile", reserve)
		}
		if !contains(assessment.Codes, model.ZeroMarginHeadroom) {
			t.Errorf("Evaluate(%+v) codes = %v, want %s", reserve, assessment.Codes, model.ZeroMarginHeadroom)
		}
		if got, want := assessment.RequiredMarginUSD, fixed.MustParse("5"); got != want {
			t.Errorf("RequiredMarginUSD = %s, want %s", got, want)
		}
	}
}

func TestEvaluateDiagnosticNotionalsAreCapitalUnsupportedAtTwoTimesLeverage(t *testing.T) {
	for _, perLegNotional := range []string{"25", "50"} {
		t.Run("per_leg_"+perLegNotional, func(t *testing.T) {
			assessment := feasibility.Evaluate(feasibility.Profile{
				TotalCapitalUSD:    fixed.MustParse("10"),
				PerVenueCapitalUSD: fixed.MustParse("5"),
				Leverage:           fixed.MustParse("2"),
				PerLegNotionalUSD:  fixed.MustParse(perLegNotional),
			}, feasibility.CostReserve{})

			if assessment.CapitalSupported {
				t.Fatalf("$%s per leg unexpectedly supported", perLegNotional)
			}
			if !contains(assessment.Codes, model.CapitalUnsupported) {
				t.Errorf("codes = %v, want %s", assessment.Codes, model.CapitalUnsupported)
			}
		})
	}
}

func TestEvaluateUsesTheRequestedLeverageWithoutIncreasingIt(t *testing.T) {
	profile := feasibility.Profile{
		TotalCapitalUSD:    fixed.MustParse("10"),
		PerVenueCapitalUSD: fixed.MustParse("5"),
		Leverage:           fixed.MustParse("2"),
		PerLegNotionalUSD:  fixed.MustParse("10"),
	}

	assessment := feasibility.Evaluate(profile, feasibility.CostReserve{})
	if got, want := assessment.RequiredMarginUSD, fixed.MustParse("5"); got != want {
		t.Fatalf("RequiredMarginUSD = %s, want %s; evaluator must not increase leverage", got, want)
	}
	if assessment.CapitalSupported {
		t.Fatalf("zero-reserve boundary assessment = %+v, want boundary-unproven", assessment)
	}
	if !contains(assessment.Codes, model.ZeroMarginHeadroom) {
		t.Fatalf("zero-reserve boundary codes = %v, want %s", assessment.Codes, model.ZeroMarginHeadroom)
	}
}

func TestEvaluateRejectsTotalCapitalBelowTwoVenueAllocations(t *testing.T) {
	assessment := feasibility.Evaluate(feasibility.Profile{
		TotalCapitalUSD:    fixed.MustParse("1"),
		PerVenueCapitalUSD: fixed.MustParse("5"),
		Leverage:           fixed.MustParse("2"),
		PerLegNotionalUSD:  fixed.MustParse("10"),
	}, feasibility.CostReserve{})

	if assessment.CapitalSupported {
		t.Fatalf("assessment = %+v, want total-capital rejection", assessment)
	}
	if !contains(assessment.Codes, model.CapitalUnsupported) {
		t.Fatalf("codes = %v, want %s", assessment.Codes, model.CapitalUnsupported)
	}
}

func TestEvaluateRejectsNegativeCostReserve(t *testing.T) {
	for _, reserve := range []feasibility.CostReserve{
		{EntryFeeUSD: fixed.MustParse("-0.00000001")},
		{ExitFeeUSD: fixed.MustParse("-0.00000001")},
		{StressReserveUSD: fixed.MustParse("-0.00000001")},
	} {
		assessment := feasibility.Evaluate(feasibility.Profile{
			TotalCapitalUSD:    fixed.MustParse("10"),
			PerVenueCapitalUSD: fixed.MustParse("5"),
			Leverage:           fixed.MustParse("2"),
			PerLegNotionalUSD:  fixed.MustParse("10"),
		}, reserve)

		if assessment.CapitalSupported {
			t.Errorf("Evaluate(%+v) accepted a negative reserve", reserve)
		}
		if !contains(assessment.Codes, model.CapitalUnsupported) {
			t.Errorf("Evaluate(%+v) codes = %v, want %s", reserve, assessment.Codes, model.CapitalUnsupported)
		}
	}
}

func contains(codes []model.ReasonCode, want model.ReasonCode) bool {
	for _, code := range codes {
		if code == want {
			return true
		}
	}
	return false
}
