// Package fixed provides decimal fixed-point values for money, price, and size.
// JSON values are always encoded as strings so floating-point input cannot cross
// an API or persistence boundary unnoticed.
package fixed

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"strconv"
	"strings"
)

const (
	Decimals = 8
	Scale    = int64(100_000_000)
)

var (
	ErrInvalid      = errors.New("invalid fixed-point value")
	ErrPrecision    = errors.New("fixed-point precision exceeds 8 decimal places")
	ErrOverflow     = errors.New("fixed-point overflow")
	ErrDivisionZero = errors.New("fixed-point division by zero")
)

// Value stores a signed decimal scaled by 1e8.
type Value int64

func Zero() Value { return 0 }

func FromScaled(v int64) Value { return Value(v) }

func Parse(raw string) (Value, error) {
	if raw == "" || strings.TrimSpace(raw) != raw {
		return 0, fmt.Errorf("%w: %q", ErrInvalid, raw)
	}

	sign := int64(1)
	switch raw[0] {
	case '-':
		sign = -1
		raw = raw[1:]
	case '+':
		raw = raw[1:]
	}
	if raw == "" || strings.ContainsAny(raw, "eE") {
		return 0, fmt.Errorf("%w: exponent or empty value", ErrInvalid)
	}

	parts := strings.Split(raw, ".")
	if len(parts) > 2 || parts[0] == "" {
		return 0, fmt.Errorf("%w: malformed decimal", ErrInvalid)
	}
	if len(parts) == 2 && parts[1] == "" {
		return 0, fmt.Errorf("%w: empty fractional part", ErrInvalid)
	}
	if len(parts) == 2 && len(parts[1]) > Decimals {
		return 0, ErrPrecision
	}
	if !digits(parts[0]) || (len(parts) == 2 && !digits(parts[1])) {
		return 0, fmt.Errorf("%w: non-digit character", ErrInvalid)
	}

	whole := new(big.Int)
	if _, ok := whole.SetString(parts[0], 10); !ok {
		return 0, ErrInvalid
	}
	whole.Mul(whole, big.NewInt(Scale))

	if len(parts) == 2 {
		fractionText := parts[1] + strings.Repeat("0", Decimals-len(parts[1]))
		fraction := new(big.Int)
		fraction.SetString(fractionText, 10)
		whole.Add(whole, fraction)
	}
	if sign < 0 {
		whole.Neg(whole)
	}
	return fromBig(whole)
}

func MustParse(raw string) Value {
	v, err := Parse(raw)
	if err != nil {
		panic(err)
	}
	return v
}

func digits(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return true
}

func fromBig(v *big.Int) (Value, error) {
	if !v.IsInt64() {
		return 0, ErrOverflow
	}
	return Value(v.Int64()), nil
}

func (v Value) Scaled() int64 { return int64(v) }

func (v Value) String() string {
	n := big.NewInt(int64(v))
	sign := ""
	if n.Sign() < 0 {
		sign = "-"
		n.Abs(n)
	}
	whole, fraction := new(big.Int), new(big.Int)
	whole.QuoRem(n, big.NewInt(Scale), fraction)
	if fraction.Sign() == 0 {
		return sign + whole.String()
	}
	frac := fmt.Sprintf("%08d", fraction.Int64())
	frac = strings.TrimRight(frac, "0")
	return sign + whole.String() + "." + frac
}

func (v Value) IsZero() bool     { return v == 0 }
func (v Value) IsPositive() bool { return v > 0 }
func (v Value) IsNegative() bool { return v < 0 }
func (v Value) Cmp(other Value) int {
	switch {
	case v < other:
		return -1
	case v > other:
		return 1
	default:
		return 0
	}
}

func (v Value) Neg() (Value, error) {
	return fromBig(new(big.Int).Neg(big.NewInt(int64(v))))
}

func (v Value) Abs() (Value, error) {
	return fromBig(new(big.Int).Abs(big.NewInt(int64(v))))
}

func (v Value) Add(other Value) (Value, error) {
	return fromBig(new(big.Int).Add(big.NewInt(int64(v)), big.NewInt(int64(other))))
}

func (v Value) Sub(other Value) (Value, error) {
	return fromBig(new(big.Int).Sub(big.NewInt(int64(v)), big.NewInt(int64(other))))
}

func (v Value) Mul(other Value) (Value, error) {
	n := new(big.Int).Mul(big.NewInt(int64(v)), big.NewInt(int64(other)))
	n.Quo(n, big.NewInt(Scale))
	return fromBig(n)
}

func (v Value) Div(other Value) (Value, error) {
	if other == 0 {
		return 0, ErrDivisionZero
	}
	n := new(big.Int).Mul(big.NewInt(int64(v)), big.NewInt(Scale))
	n.Quo(n, big.NewInt(int64(other)))
	return fromBig(n)
}

func (v Value) MarshalJSON() ([]byte, error) {
	return json.Marshal(v.String())
}

func (v *Value) UnmarshalJSON(data []byte) error {
	data = bytes.TrimSpace(data)
	if len(data) == 0 || data[0] != '"' {
		return errors.New("fixed-point JSON value must be a string")
	}
	var raw string
	if err := json.Unmarshal(data, &raw); err != nil {
		return err
	}
	parsed, err := Parse(raw)
	if err != nil {
		return err
	}
	*v = parsed
	return nil
}

func (v Value) GoString() string {
	return "fixed.MustParse(" + strconv.Quote(v.String()) + ")"
}
