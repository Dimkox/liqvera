package config

import (
	"errors"
	"os"
	"strings"
)

const ShadowMode = "shadow"

type Config struct {
	HTTPAddr    string
	Mode        string
	DatabaseURL string
}

func Load() (Config, error) {
	mode := strings.ToLower(strings.TrimSpace(env("ENGINE_MODE", ShadowMode)))
	if mode != ShadowMode {
		return Config{}, errors.New("only ENGINE_MODE=shadow is supported in this release")
	}
	if truthy(os.Getenv("LIVE_EXECUTION_ENABLED")) {
		return Config{}, errors.New("live execution is intentionally unavailable")
	}
	return Config{
		HTTPAddr:    env("HTTP_ADDR", ":8080"),
		Mode:        mode,
		DatabaseURL: strings.TrimSpace(os.Getenv("DATABASE_URL")),
	}, nil
}

func env(name, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(name)); value != "" {
		return value
	}
	return fallback
}

func truthy(value string) bool {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "1", "true", "yes", "on":
		return true
	default:
		return false
	}
}
