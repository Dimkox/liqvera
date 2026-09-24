package httpapi

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestMetaIsExplicitlyShadowOnly(t *testing.T) {
	s := New(BuildInfo{Mode: "shadow", Version: "dev", Commit: "test"})
	r := httptest.NewRequest(http.MethodGet, "/v1/meta", nil)
	w := httptest.NewRecorder()
	s.Handler().ServeHTTP(w, r)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d", w.Code)
	}
	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	capabilities := body["capabilities"].(map[string]any)
	if capabilities["live_execution"].(bool) {
		t.Fatal("live execution must remain disabled")
	}
	if got := w.Header().Get("Cache-Control"); got != "no-store" {
		t.Fatalf("unexpected cache header %q", got)
	}
}
