# Reconstructed algorithms

All pseudocode is a derived description, not a verbatim reproduction of the proprietary bundle.

## 1. Private WebSocket session

Evidence: `index-DHlB7G7_.js:1705-1748`, `2106-2112`.

```text
connectPrivate():
    require app_in_foreground and authenticated_user
    reset online/logged/heartbeat state
    token = Firebase.currentUser.getIdToken()
    server = local_setting("server") or "wss://me.goodcrypto.app"
    ws = WebSocket(server + "?app=2.5.1&len=" + token.length,
                   subprotocol=token)
    attach open/close/error/message handlers

sendAuthenticated(event, payload):
    if user not logged in: return false
    payload.token = current Firebase ID token
    payload.uid = current uid
    payload.id = current uid
    buffer[event] = {event, ...payload}
    flush buffer when socket is OPEN
```

Every second the client sends `{event:"ping", ts:now}`. If a previous ping has not cleared within about nine seconds, it reconnects. On `hello`, it accepts an existing logged session or sends `user-login`, then refreshes balances, keys, orders, positions, accounts, wallets, alerts and portfolio state.

## 2. RSA request signing

Evidence: `index-DHlB7G7_.js:921-985`, `2165-2174`, `3601`.

```text
loadKeys(firebaseRecord):
    publicPem  = base64_decode(firebaseRecord.e)
    privatePem = base64_decode(firebaseRecord.s)
    publicKey  = WebCrypto.import(RSA-OAEP, SHA-256, extractable=true)
    signingKey = WebCrypto.import(PKCS#8, RSA-PSS, SHA-256,
                                  extractable=true, usages=[sign])

canonicalValues(value):
    undefined -> []
    null      -> [""]
    array     -> concatenate canonicalValues(item) in array order
    object    -> sort keys; concatenate canonicalValues(value[key])
                 (field names are not included)
    primitive -> [String(value)]

sign(payload):
    preimage = canonicalValues(payload).join("|")
    signature = RSA-PSS-SHA256(signingKey, preimage, saltLength=20)
    return base64(signature)
```

Sensitive writes normalize numeric fields, add a nonce, sign the normalized object and send `{order|position|strategy, signature, ts}`. `order-new` uses a 90-second callback timeout; most writes use 30 seconds.

## 3. New/modify/cancel order pipeline

```text
newOrder(form):
    validate account, symbol, amount, price/trigger/trailing/leverage and funds
    order = normalizeForm(form)
    order.tag = random base36 client id
    order.nonce = currentNonce
    signature = sign(order)
    mark order[tag] loading
    send "order-new" with order, signature and timestamp
    wait for response keyed by tag
    on success: update local order/status/history
    on timeout/error: clear loading and expose error

modifyOrder(order, diff):
    normalize changed size/price/stop/last-price
    attach nonce; sign; send "order-modify"

modifyMetadata(orderId, meta, execInst):
    payload = {order_id, meta, nonce, exec_inst}
    sign payload; send "order-modify-meta"

cancelOrder(orderId):
    payload = {order_id, nonce}
    sign payload; send "order-cancel"
```

## 4. Grid level generation

Evidence: `index-DHlB7G7_.js:2860-2869`.

```text
if linear:
    step = (high - low) / (N - 1)
    raw[i] = low + i * step
else logarithmic:
    logLow = log10(low)
    logStep = (log10(high) - logLow) / (N - 1)
    raw[i] = 10 ** (logLow + i * logStep)

price[i] = round_down_to_symbol_price_step(raw[i])
pnlRatio[i] = i == 0 ? 0 : (price[i] - price[i-1]) / price[i]
mark first level as low and last level as high
```

Grid setup also carries active-level count, log-scale switch, post-only, initial position, auto-close, stop-low/high, stop-on-zero-position, maximum P&L, activation threshold and drawdown.

## 5. DCA levels and position math

Evidence: `index-DHlB7G7_.js:3059-3103`.

```text
if spot and costMode:
    entry.size = entryCost / lastPrice
    entry.cost = entryCost
else if spot:
    entry.size = entrySize
    entry.cost = entrySize * lastPrice
else:
    convert requested unit through derivative contract specification
```

For side sign `+1` buy and `-1` sell, the first averaging distance is `level1PricePercent`; later levels use `priceK`, and after the second level `priceX` accelerates distance:

```text
if accelerated level:
    if buy:
        distance = priceX * (1 - previousPrice / previousPreviousPrice) * 100
    else:
        distance = priceX * (previousPrice / previousPreviousPrice - 1) * 100

levelPrice = previousPrice - previousPrice * distance/100 * sign
levelPricePercentFromStart = (levelPrice - lastPrice) / lastPrice * 100
```

The first averaging level uses `level1Size`; later levels multiply prior size/cost by `sizeK`. The simulator recomputes cumulative size, cost and VWAP after each fill, then TP price/percent and SL monetary/percentage loss for every partial-fill depth.

## 6. CEX bot creation

Evidence: `index-DHlB7G7_.js:8100-8163`.

```text
submitAlgo(form):
    validate exchange/account/symbol/side/size and derivative settings
    baseOrder = {exchange, account, symbol, side, size/cost, current_price}
    if derivative: add leverage, isolated and position-side values

    switch form.type:
      Infinity:
        params = entryTrail, exitTrail, improveExit, drawdown
      Grid:
        params = low, high, levels, activeLevels, logarithmic,
                 postOnly, initialPosition, autoClose,
                 stopLow, stopHigh, stopZeroPosition,
                 maxPnl, activation, drawdown
        execution = webhook
      DCA:
        params = launchCondition(manual|signals|webhook-tv),
                 entry type/size/limit/trail,
                 averaging count/size/distance multipliers,
                 TP mode/trail/repeat, SL, cooldown, autoClose

    save optimistic local order
    send through signed private order pipeline
    track analytics; reset form; haptic feedback
```

## 7. DEX route/quote guard and order submission

Evidence: `index-DHlB7G7_.js:10727-10839`.

```text
refreshRoute(form):
    require wallet, active account and ready order
    prepared = prepareOrder(form, includeMeta=false, includeRoute=false)
    if form is swap or trailing:
        response = privateCommand("x-route", prepared, sessionId, timeout=60s)
    else:
        response = privateCommand("x-quote", prepared, sessionId, timeout=60s)
    reject response for stale/wrong chain
    store route and routeTimestamp
    update the calculated opposite amount

submit(form):
    if route older than 10 seconds: refreshRoute()
    if refreshed execution price differs by more than 1%:
        stop and require a fresh user confirmation
    prepared = prepareOrder(form, route, connected TP/SL metadata)
    sign/send through wallet or account-abstraction client
    save history, analytics and reset form
```

Route refresh is debounced by 500 ms. A route error can be overridden only through an explicit user confirmation path.

## 8. Connected TP/SL

The DEX order builder permits up to five TP levels, whose percentages may not exceed 100 in total. Connected metadata supports fixed or trailing TP, SL, trigger type/timeout, reduce-only behavior and activation instructions.

## 9. DEX DCA

Evidence: `index-DHlB7G7_.js:10569-10624`.

```text
submitDexDca(form):
    validate assets, entry size, averaging count/multipliers,
             each distance > -100, TP/SL and trailing requirements
    levels = getAllDcaLvls(form)
    simulated = request x-route for the prepared DCA entry
    if price-impact warning and not confirmed: stop for confirmation
    send GC_DCA strategy/order with slippage, broadcast/Jito,
         launch condition, TP/repeat/SL/cooldown/close-position parameters
```

## 10. Filter strategy / Sniper

Evidence: `index-DHlB7G7_.js:10672-10712`.

The form builds either a test `ALERT` strategy or a real `ORDER` strategy. Parameters include filter predicates, spend coin, per-coin maximum, maximum concurrent positions, P&L drawdown/stop, close-position policy, TP/SL and chain execution. The client checks login, wallet readiness, funds and a maximum of ten active test bots before `strategy-new`.

## 11. Service fee and GOOD gating

Evidence: `index-DHlB7G7_.js:10728`, `2180`.

```text
volumeReduction = 0
if tradeVolumeUSD > 10_000:  volumeReduction += 0.5
if tradeVolumeUSD > 100_000: volumeReduction += 0.25
serviceFeePercent = max(1 - totalUserDiscount - volumeReduction, 0)
revenueShareUnlocked = goodHeld >= 10_000
```

Fee values are percentage units, not decimal fractions.
