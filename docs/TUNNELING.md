# Exposing a Peer to the Public Internet

Localhost is permitted only during early development; for league play every
team **must** expose its FastMCP server through a tunnel (rulebook ch. 2.4).
Nothing in the code changes between the two - only the URLs in the private
TOML files.

## With ngrok

```bash
# 1. Start your peer (it serves on the port from [network] my_port)
uv run python -m police_thief peer --role police

# 2. In another terminal, open the tunnel to that port
ngrok http 8801
# ngrok prints something like: https://a1b2c3.ngrok-free.app
```

Give the printed URL (with the `/mcp` suffix) to the opposing team; put their
URL in your own private TOML:

```toml
[network]
my_port = 8801
opponent_url = "https://THEIR-TUNNEL.ngrok-free.app/mcp"
```

## With Localtonet

Same flow: run `localtonet http 8801`, exchange the generated URL, update
`opponent_url` on both sides.

## Starting order does not matter

Two teams cannot start their processes on the same second, so the opening
handshake is a **rendezvous**, not a single shot: whichever peer starts first
keeps re-offering its terms while the other is still booting, printing

```
[police] opponent not up yet - waiting for it to start...
```

and, once its own handshake lands, lingers a few seconds still serving so the
slower side's call also completes. Defaults are 120s of waiting and 15s of
lingering; tune with `--wait` / `--linger` on `peer`, and `--wait` on
`scripts/friendly_series.py`.

This applies **only** to the opening handshake. Mid-match the short budget
below is what governs, and that asymmetry is deliberate: a peer that has not
started yet is not the same event as a peer that has gone dark mid-game.

## What failure looks like (by design)

Once a match is under way, the peer does not hang: every request carries a
30-second deadline and three retries with 5-second backoff, after which the
peer declares a clean technical loss and reports it. Reliability rules #6/#7
in action - "a missed deadline is a failure, not patience."

A **refusal** is not a silence. If the opponent answers but rejects the terms
(a contract digest or scent-model mismatch), that is reported verbatim and
never retried - no amount of waiting fixes a mismatch. If you can hear them but
they cannot hear you, the peer names `[network].opponent_url` as the likely
cause.

## Proving the tunnel before you name a start time

The league kit ships a network checker; a bare "is it up?" probe cannot tell a
healthy idle tunnel from one with no ingress rules, because both answer `502`
forever. Prove your own receiving path with its loopback mode:

```bash
python tools/netcheck.py https://THEIR-TUNNEL/mcp        # probe the opponent
python tools/netcheck.py --loopback 8801 https://YOUR-TUNNEL   # prove your own
```
