package config_test

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Dimkox/multi-exchange-engine/internal/stagea/config"
	"github.com/Dimkox/multi-exchange-engine/internal/stagea/model"
)

func TestLoadAcceptsOnlyThePublicStageAEnvironmentContract(t *testing.T) {
	clearStageAEnvironment(t)

	t.Setenv("UNRELATED_OS_SETTING", "ignored")
	t.Setenv("DATABASE_URL", "postgres://stage-a@db/stage_a?sslmode=disable")
	t.Setenv("HTTP_ADDR", ":8090")
	t.Setenv("STAGE_A_HYPERLIQUID_WS_URL", "wss://api.hyperliquid.xyz/ws")
	t.Setenv("STAGE_A_LIGHTER_WS_URL", "wss://mainnet.zklighter.elliot.ai/stream")
	t.Setenv("STAGE_A_VARIATIONAL_HTTP_URL", "https://api.variational.io")
	t.Setenv("STAGE_A_INSTRUMENT_MANIFEST", "config/stage-a-instruments.json")
	t.Setenv("STAGE_A_RAW_RETENTION_DAYS", "9")
	t.Setenv("STAGE_A_EVIDENCE_RETENTION_DAYS", "31")
	t.Setenv("STAGE_A_HL_MAX_AGE_MS", "751")
	t.Setenv("STAGE_A_LIGHTER_MAX_AGE_MS", "201")
	t.Setenv("STAGE_A_MAX_SKEW_MS", "251")
	t.Setenv("STAGE_A_MAX_CLOCK_ERROR_MS", "26")

	cfg, err := config.Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if got, want := cfg.RawRetentionDays, 9; got != want {
		t.Errorf("RawRetentionDays = %d, want %d", got, want)
	}
	if got, want := cfg.EvidenceRetentionDays, 31; got != want {
		t.Errorf("EvidenceRetentionDays = %d, want %d", got, want)
	}
	if got, want := cfg.HyperliquidMaxAge, 751*time.Millisecond; got != want {
		t.Errorf("HyperliquidMaxAge = %s, want %s", got, want)
	}
	if got, want := cfg.LighterMaxAge, 201*time.Millisecond; got != want {
		t.Errorf("LighterMaxAge = %s, want %s", got, want)
	}
	if got, want := cfg.MaxSkew, 251*time.Millisecond; got != want {
		t.Errorf("MaxSkew = %s, want %s", got, want)
	}
	if got, want := cfg.MaxClockError, 26*time.Millisecond; got != want {
		t.Errorf("MaxClockError = %s, want %s", got, want)
	}
}

func TestLoadUsesDocumentedPublicDefaults(t *testing.T) {
	clearStageAEnvironment(t)

	cfg, err := config.Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if got, want := cfg.RawRetentionDays, 7; got != want {
		t.Errorf("RawRetentionDays = %d, want %d", got, want)
	}
	if got, want := cfg.EvidenceRetentionDays, 30; got != want {
		t.Errorf("EvidenceRetentionDays = %d, want %d", got, want)
	}
	if got, want := cfg.HyperliquidMaxAge, 750*time.Millisecond; got != want {
		t.Errorf("HyperliquidMaxAge = %s, want %s", got, want)
	}
	if got, want := cfg.LighterMaxAge, 200*time.Millisecond; got != want {
		t.Errorf("LighterMaxAge = %s, want %s", got, want)
	}
	if got, want := cfg.MaxSkew, 250*time.Millisecond; got != want {
		t.Errorf("MaxSkew = %s, want %s", got, want)
	}
	if got, want := cfg.MaxClockError, 25*time.Millisecond; got != want {
		t.Errorf("MaxClockError = %s, want %s", got, want)
	}
}

func TestLoadRejectsForbiddenCredentialVariables(t *testing.T) {
	for _, name := range []string{
		"PRIVATE_KEY", "SECRET", "API_KEY", "TOKEN", "WALLET", "MNEMONIC", "ACCOUNT_INDEX",
	} {
		t.Run(name, func(t *testing.T) {
			clearStageAEnvironment(t)
			t.Setenv(name, "must-not-be-accepted")

			_, err := config.Load()
			if !errors.Is(err, config.ErrCredentialContract) {
				t.Fatalf("Load() error = %v, want credential contract violation", err)
			}
		})
	}
}

func TestLoadRejectsUnknownStageAEnvironment(t *testing.T) {
	for _, value := range []string{"", "1"} {
		t.Run("value_"+value, func(t *testing.T) {
			clearStageAEnvironment(t)
			t.Setenv("STAGE_A_UNDOCUMENTED_SETTING", value)

			_, err := config.Load()
			if !errors.Is(err, config.ErrUnknownStageASetting) {
				t.Fatalf("Load() error = %v, want unknown Stage A setting violation", err)
			}
		})
	}
}

func TestStageAInstrumentManifestIsOnlyProvisionalPUMPAndDOGE(t *testing.T) {
	manifest := filepath.Join("..", "..", "..", "config", "stage-a-instruments.json")
	contracts, err := config.LoadManifest(manifest)
	if err != nil {
		t.Fatalf("LoadManifest(%q) error = %v", manifest, err)
	}

	if got, want := len(contracts), 4; got != want {
		t.Fatalf("contract count = %d, want %d", got, want)
	}
	seen := make(map[string]model.Contract, len(contracts))
	for _, contract := range contracts {
		if contract.MappingState != model.MappingProvisional {
			t.Errorf("%s/%s MappingState = %q, want provisional", contract.Venue, contract.VenueSymbol, contract.MappingState)
		}
		if contract.MarketID == "" || contract.VenueSymbol == "" || contract.CanonicalID == "" ||
			contract.BaseUnit == "" || contract.QuoteUnit == "" {
			t.Errorf("%s has incomplete identity: %+v", contract.VenueSymbol, contract)
		}
		if !contract.ContractMultiplier.IsPositive() || !contract.TickSize.IsPositive() ||
			!contract.LotSize.IsPositive() || !contract.MinBase.IsPositive() || !contract.MinQuoteUSD.IsPositive() {
			t.Errorf("%s/%s has non-positive units or minimums", contract.Venue, contract.VenueSymbol)
		}
		if contract.EvidenceHash != "" {
			t.Errorf("%s/%s EvidenceHash = %q, want empty before verification", contract.Venue, contract.VenueSymbol, contract.EvidenceHash)
		}
		seen[string(contract.Venue)+"/"+contract.VenueSymbol] = contract
	}
	for _, want := range []string{"hyperliquid/PUMP", "lighter/PUMP", "hyperliquid/DOGE", "lighter/DOGE"} {
		if _, ok := seen[want]; !ok {
			t.Errorf("manifest missing %s", want)
		}
	}
}

func TestEmptyMappingEvidenceBlocksLifecycleAdmission(t *testing.T) {
	manifest := filepath.Join("..", "..", "..", "config", "stage-a-instruments.json")
	contracts, err := config.LoadManifest(manifest)
	if err != nil {
		t.Fatalf("LoadManifest(%q) error = %v", manifest, err)
	}

	for _, contract := range contracts {
		admission := model.AdmitLifecycle(contract)
		if admission.Allowed {
			t.Errorf("%s/%s admitted with empty evidence", contract.Venue, contract.VenueSymbol)
		}
		if !contains(admission.Codes, model.MappingUnverified) || !contains(admission.Codes, model.ContractUnverified) {
			t.Errorf("%s/%s admission codes = %v, want mapping and contract unverified", contract.Venue, contract.VenueSymbol, admission.Codes)
		}
	}
}

func clearStageAEnvironment(t *testing.T) {
	t.Helper()
	for _, entry := range os.Environ() {
		name, _, ok := strings.Cut(entry, "=")
		if ok && strings.HasPrefix(name, "STAGE_A_") {
			t.Setenv(name, "")
		}
	}
	for _, name := range []string{
		"DATABASE_URL", "HTTP_ADDR", "PRIVATE_KEY", "SECRET", "API_KEY", "TOKEN", "WALLET", "MNEMONIC", "ACCOUNT_INDEX",
	} {
		t.Setenv(name, "")
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
