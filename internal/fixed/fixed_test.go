package fixed

import (
	"encoding/json"
	"math"
	"testing"
)

func TestParseRoundTrip(t *testing.T) {
	cases := []string{"0", "1", "-1", "0.00000001", "456.78", "-92233720368.54775808"}
	for _, tc := range cases {
		v, err := Parse(tc)
		if err != nil {
			t.Fatalf("Parse(%q): %v", tc, err)
		}
		if got := v.String(); got != tc {
			t.Fatalf("round trip %q: got %q", tc, got)
		}
	}
}

func TestRejectsFloatShapedJSONNumber(t *testing.T) {
	var v Value
	if err := json.Unmarshal([]byte(`1.25`), &v); err == nil {
		t.Fatal("expected numeric JSON to be rejected")
	}
	if err := json.Unmarshal([]byte(`"1.25"`), &v); err != nil {
		t.Fatalf("string JSON: %v", err)
	}
	if err := v.UnmarshalJSON([]byte("  \"2.5\"  ")); err != nil || v.String() != "2.5" {
		t.Fatalf("whitespace-padded string JSON: value=%v err=%v", v, err)
	}
}

func TestPrecisionAndOverflow(t *testing.T) {
	if _, err := Parse("0.000000001"); err != ErrPrecision {
		t.Fatalf("expected ErrPrecision, got %v", err)
	}
	max := FromScaled(math.MaxInt64)
	if _, err := max.Add(MustParse("0.00000001")); err != ErrOverflow {
		t.Fatalf("expected ErrOverflow, got %v", err)
	}
}

func TestMulDiv(t *testing.T) {
	v, err := MustParse("12.5").Mul(MustParse("2"))
	if err != nil || v.String() != "25" {
		t.Fatalf("mul: %v %v", v, err)
	}
	v, err = v.Div(MustParse("4"))
	if err != nil || v.String() != "6.25" {
		t.Fatalf("div: %v %v", v, err)
	}
}
