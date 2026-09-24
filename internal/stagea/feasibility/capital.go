// Package feasibility evaluates Stage A research-profile capital gates.
package feasibility

import (
	"github.com/Dimkox/multi-exchange-engine/internal/fixed"
	"github.com/Dimkox/multi-exchange-engine/internal/stagea/model"
)

type Profile struct {
	TotalCapitalUSD    fixed.Value
	PerVenueCapitalUSD fixed.Value
	Leverage           fixed.Value
	PerLegNotionalUSD  fixed.Value
}

type CostReserve struct {
	EntryFeeUSD      fixed.Value
	ExitFeeUSD       fixed.Value
	StressReserveUSD fixed.Value
}

type Assessment struct {
	RequiredMarginUSD fixed.Value
	MarginHeadroomUSD fixed.Value
	CapitalSupported  bool
	Codes             []model.ReasonCode
}

func Evaluate(profile Profile, reserve CostReserve) Assessment {
	if !profile.Leverage.IsPositive() || !profile.PerVenueCapitalUSD.IsPositive() || !profile.PerLegNotionalUSD.IsPositive() {
		return Assessment{Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	allocatedCapital, err := profile.PerVenueCapitalUSD.Add(profile.PerVenueCapitalUSD)
	if err != nil || profile.TotalCapitalUSD.Cmp(allocatedCapital) < 0 {
		return Assessment{Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	if reserve.EntryFeeUSD.IsNegative() || reserve.ExitFeeUSD.IsNegative() || reserve.StressReserveUSD.IsNegative() {
		return Assessment{Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}

	requiredMargin, err := profile.PerLegNotionalUSD.Div(profile.Leverage)
	if err != nil {
		return Assessment{Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	costs, err := reserve.EntryFeeUSD.Add(reserve.ExitFeeUSD)
	if err != nil {
		return Assessment{RequiredMarginUSD: requiredMargin, Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	costs, err = costs.Add(reserve.StressReserveUSD)
	if err != nil {
		return Assessment{RequiredMarginUSD: requiredMargin, Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	headroom, err := profile.PerVenueCapitalUSD.Sub(requiredMargin)
	if err != nil {
		return Assessment{RequiredMarginUSD: requiredMargin, Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}
	headroom, err = headroom.Sub(costs)
	if err != nil {
		return Assessment{RequiredMarginUSD: requiredMargin, Codes: []model.ReasonCode{model.CapitalUnsupported}}
	}

	assessment := Assessment{RequiredMarginUSD: requiredMargin, MarginHeadroomUSD: headroom}
	if requiredMargin == profile.PerVenueCapitalUSD || headroom.IsZero() {
		assessment.Codes = []model.ReasonCode{model.ZeroMarginHeadroom}
		return assessment
	}
	if headroom.IsNegative() {
		assessment.Codes = []model.ReasonCode{model.CapitalUnsupported}
		return assessment
	}
	assessment.CapitalSupported = true
	return assessment
}
