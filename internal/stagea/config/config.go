// Package config loads the credential-free Stage A public-data contract.
package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/stagea/model"
)

var (
	ErrCredentialContract   = errors.New("credential environment variable violates Stage A contract")
	ErrUnknownStageASetting = errors.New("unknown Stage A environment setting")
)

type Config struct {
	DatabaseURL           string
	HTTPAddr              string
	HyperliquidWSURL      string
	LighterWSURL          string
	VariationalHTTPURL    string
	InstrumentManifest    string
	RawRetentionDays      int
	EvidenceRetentionDays int
	HyperliquidMaxAge     time.Duration
	LighterMaxAge         time.Duration
	MaxSkew               time.Duration
	MaxClockError         time.Duration
}

func Load() (Config, error) {
	if err := validateEnvironment(); err != nil {
		return Config{}, err
	}

	rawRetentionDays, err := days("STAGE_A_RAW_RETENTION_DAYS", 7)
	if err != nil {
		return Config{}, err
	}
	evidenceRetentionDays, err := days("STAGE_A_EVIDENCE_RETENTION_DAYS", 30)
	if err != nil {
		return Config{}, err
	}
	hyperliquidMaxAge, err := milliseconds("STAGE_A_HL_MAX_AGE_MS", 750)
	if err != nil {
		return Config{}, err
	}
	lighterMaxAge, err := milliseconds("STAGE_A_LIGHTER_MAX_AGE_MS", 200)
	if err != nil {
		return Config{}, err
	}
	maxSkew, err := milliseconds("STAGE_A_MAX_SKEW_MS", 250)
	if err != nil {
		return Config{}, err
	}
	maxClockError, err := milliseconds("STAGE_A_MAX_CLOCK_ERROR_MS", 25)
	if err != nil {
		return Config{}, err
	}

	return Config{
		DatabaseURL:           value("DATABASE_URL", ""),
		HTTPAddr:              value("HTTP_ADDR", ":8080"),
		HyperliquidWSURL:      value("STAGE_A_HYPERLIQUID_WS_URL", "wss://api.hyperliquid.xyz/ws"),
		LighterWSURL:          value("STAGE_A_LIGHTER_WS_URL", "wss://mainnet.zklighter.elliot.ai/stream"),
		VariationalHTTPURL:    value("STAGE_A_VARIATIONAL_HTTP_URL", "https://api.variational.io"),
		InstrumentManifest:    value("STAGE_A_INSTRUMENT_MANIFEST", "config/stage-a-instruments.json"),
		RawRetentionDays:      rawRetentionDays,
		EvidenceRetentionDays: evidenceRetentionDays,
		HyperliquidMaxAge:     hyperliquidMaxAge,
		LighterMaxAge:         lighterMaxAge,
		MaxSkew:               maxSkew,
		MaxClockError:         maxClockError,
	}, nil
}

func LoadManifest(path string) ([]model.Contract, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open instrument manifest: %w", err)
	}
	defer file.Close()

	var contracts []model.Contract
	decoder := json.NewDecoder(file)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&contracts); err != nil {
		return nil, fmt.Errorf("decode instrument manifest: %w", err)
	}
	if len(contracts) == 0 {
		return nil, errors.New("instrument manifest is empty")
	}
	return contracts, nil
}

func validateEnvironment() error {
	for _, name := range []string{"PRIVATE_KEY", "SECRET", "API_KEY", "TOKEN", "WALLET", "MNEMONIC", "ACCOUNT_INDEX"} {
		if strings.TrimSpace(os.Getenv(name)) != "" {
			return fmt.Errorf("%w: %s", ErrCredentialContract, name)
		}
	}
	allowed := map[string]struct{}{
		"STAGE_A_HYPERLIQUID_WS_URL": {}, "STAGE_A_LIGHTER_WS_URL": {},
		"STAGE_A_VARIATIONAL_HTTP_URL": {}, "STAGE_A_INSTRUMENT_MANIFEST": {},
		"STAGE_A_RAW_RETENTION_DAYS": {}, "STAGE_A_EVIDENCE_RETENTION_DAYS": {},
		"STAGE_A_HL_MAX_AGE_MS": {}, "STAGE_A_LIGHTER_MAX_AGE_MS": {},
		"STAGE_A_MAX_SKEW_MS": {}, "STAGE_A_MAX_CLOCK_ERROR_MS": {},
	}
	for _, entry := range os.Environ() {
		name, _, ok := strings.Cut(entry, "=")
		if ok && strings.HasPrefix(name, "STAGE_A_") {
			if _, ok := allowed[name]; !ok {
				return fmt.Errorf("%w: %s", ErrUnknownStageASetting, name)
			}
		}
	}
	return nil
}

func value(name, fallback string) string {
	if current := strings.TrimSpace(os.Getenv(name)); current != "" {
		return current
	}
	return fallback
}

func days(name string, fallback int) (int, error) {
	return positiveInt(name, fallback)
}

func milliseconds(name string, fallback int) (time.Duration, error) {
	amount, err := positiveInt(name, fallback)
	if err != nil {
		return 0, err
	}
	return time.Duration(amount) * time.Millisecond, nil
}

func positiveInt(name string, fallback int) (int, error) {
	raw := strings.TrimSpace(os.Getenv(name))
	if raw == "" {
		return fallback, nil
	}
	value, err := strconv.Atoi(raw)
	if err != nil || value <= 0 {
		return 0, fmt.Errorf("%s must be a positive integer", name)
	}
	return value, nil
}
