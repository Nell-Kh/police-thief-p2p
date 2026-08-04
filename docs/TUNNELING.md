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

## What failure looks like (by design)

If the opponent's tunnel is down, the peer does not hang: every request
carries a 30-second deadline and three retries with 5-second backoff, after
which the peer declares a clean technical loss and reports it. Reliability
rules #6/#7 in action - "a missed deadline is a failure, not patience."
