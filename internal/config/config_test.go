package config

import "testing"

func TestLoadIsShadowOnly(t *testing.T) {
	t.Setenv("ENGINE_MODE", "shadow")
	t.Setenv("LIVE_EXECUTION_ENABLED", "false")
	cfg, err := Load()
	if err != nil || cfg.Mode != ShadowMode {
		t.Fatalf("unexpected config: %+v err=%v", cfg, err)
	}
	t.Setenv("LIVE_EXECUTION_ENABLED", "true")
	if _, err := Load(); err == nil {
		t.Fatal("live flag must fail closed")
	}
}
