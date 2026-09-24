package httpapi

import (
	"encoding/json"
	"net/http"
)

type BuildInfo struct {
	Mode    string `json:"mode"`
	Version string `json:"version"`
	Commit  string `json:"commit"`
}

type Server struct {
	handler http.Handler
}

func New(info BuildInfo) *Server {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok"})
	})
	mux.HandleFunc("GET /readyz", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ready", "mode": info.Mode})
	})
	mux.HandleFunc("GET /v1/meta", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{
			"build": info,
			"capabilities": map[string]any{
				"market_data":    false,
				"shadow":         true,
				"live_execution": false,
				"withdrawals":    false,
			},
		})
	})
	return &Server{handler: securityHeaders(mux)}
}

func (s *Server) Handler() http.Handler { return s.handler }

func securityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", "default-src 'none'")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Cache-Control", "no-store")
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
