// Liqvera builds the standard upstream Caddy modules with patched dependencies.
package main

import (
    caddycmd "github.com/caddyserver/caddy/v2/cmd"
    _ "github.com/caddyserver/caddy/v2/modules/standard"
)

func main() { caddycmd.Main() }
