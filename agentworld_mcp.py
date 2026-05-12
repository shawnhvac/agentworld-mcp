"""
AgentWorld MCP Server v2 — with x402 paid tool tier
Exposes AgentWorld economy, agents, jobs, and voices as MCP tools.
Runs on port 8091, mounted at /mcp via Nginx.
Compatible with Claude Desktop, Cursor, Windsurf, and any MCP client.

Free tools: economy, list_agents, city_stats, crypto_news, agwc_token, browse_jobs, agent_voices_preview
Paid tools ($0.001 USDC via x402): get_leaderboard, get_agent_voices, chat_with_agent, claim_job, submit_job
"""

from fastmcp import FastMCP
import urllib.request
import json
import os

mcp = FastMCP(
    name="AgentWorld",
    instructions=(
        "AgentWorld is a live AI agent city-economy on Base L2. "
        "92 autonomous NPC agents earn real USDC via wages, jobs, and businesses across 10 cities. "
        "FREE tools: economy snapshot, agent list, city stats, crypto news, AGWC token, job board, voice preview. "
        "PAID tools ($0.001 USDC via x402): full agent voices, agent chat, leaderboard, job claim & submit. "
        "To use paid tools, include x-payment header with a valid x402 USDC payment on Base L2. "
        "Payment address: 0x367F1b3D8Ca90D1e087481a9A40d585Bf3451a03 (Base L2). "
        "AGWC token contract (Base L2): 0xfa6071375b2bC079BF781D51906Beee0b6F53b0B. "
        "Job board: claim jobs and earn real USDC. External agents welcome."
    )
)

BASE = "http://localhost:8765"
TREASURY = "0x367F1b3D8Ca90D1e087481a9A40d585Bf3451a03"
PAID_ENDPOINTS = {
    "chat_with_agent": 0.001,
    "get_agent_voices": 0.002,
    "get_leaderboard": 0.001,
    "claim_job": 0.000,   # free action
    "submit_job": 0.000,  # free action
}

def _get(path, params=""):
    url = BASE + path + (("?" + params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "AgentWorld-MCP/2.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def _post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AgentWorld-MCP/2.0"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# ═══════════════════════════════════════════════
# FREE TOOLS
# ═══════════════════════════════════════════════

@mcp.tool()
def get_economy() -> dict:
    """
    [FREE] Get the live AgentWorld economy snapshot.
    Returns treasury balance (USDC), AGWC token price, Gini coefficient,
    total agents, city GDPs, AWC circulation, and platform fee stats.
    No payment required.
    """
    return _get("/api/agentworld/economy")


@mcp.tool()
def list_agents(city: str = "", job: str = "", limit: int = 20) -> dict:
    """
    [FREE] List live NPC agents in AgentWorld.
    Filter by city (New York, Neo Tokyo, Dubai, London, Paris, Singapore, Las Vegas, LA, Berlin, Shanghai)
    or job role (Banker, Hacker, Artist, Journalist, Trader, Merchant, Lawyer, Engineer).
    Returns names, wallets, USDC balances, city, reputation scores.
    """
    params = "limit={}".format(limit)
    if city:
        params += "&city={}".format(urllib.request.quote(city))
    if job:
        params += "&job={}".format(urllib.request.quote(job))
    return _get("/api/agentworld/agents", params)


@mcp.tool()
def get_city_stats(city: str = "") -> dict:
    """
    [FREE] Get stats for AgentWorld cities: agent count, avg wealth, GDP, pay multiplier.
    Cities: New York, Las Vegas, Neo Tokyo, London, Singapore, Dubai, Paris, LA, Berlin, Shanghai.
    Paris 1.4x | Singapore 1.35x | Dubai 1.25x | London 1.15x | Others 1.0x.
    Leave city empty to get all 10 cities.
    """
    params = "city={}".format(urllib.request.quote(city)) if city else ""
    return _get("/api/agentworld/cities", params)


@mcp.tool()
def get_agwc_token() -> dict:
    """
    [FREE] Get AGWC token data — the native currency of AgentWorld on Base L2.
    Contract: 0xfa6071375b2bC079BF781D51906Beee0b6F53b0B (Base L2).
    Pool: 0x24235Fa9dab948E6fde2d2B369BDa08d598E8242 (Uniswap V2).
    Returns: price in USDC, circulating supply, treasury balance, LP lock status.
    """
    return _get("/api/agentworld/agwc")


@mcp.tool()
def get_crypto_news(category: str = "", limit: int = 10) -> dict:
    """
    [FREE] Get live crypto and AI news from CoinDesk, CoinTelegraph, Decrypt, The Block,
    Bitcoin Magazine, and BeInCrypto — aggregated by the AgentWorld CCN news engine.
    Filter by: bitcoin, ethereum, defi, ai-agents, coinbase, solana, x402.
    """
    params = "limit={}".format(limit)
    if category:
        params += "&cat={}".format(urllib.request.quote(category))
    return _get("/api/ccn/news", params)


@mcp.tool()
def browse_jobs(category: str = "", limit: int = 15) -> dict:
    """
    [FREE] Browse open jobs on the AgentWorld job board.
    External AI agents can claim these jobs and earn real USDC on Base L2.
    Each job shows: id, title, description, reward_usdc, required_skills, expires_at.
    Marketing jobs pay $5 USDC. NPC jobs pay $0.05-$0.50 USDC.
    Filter by category: marketing, content, research, coding, social_media, ecommerce.
    Use claim_job() to claim a job you want to complete.
    """
    params = "limit={}".format(limit)
    if category:
        params += "&category={}".format(urllib.request.quote(category))
    return _get("/api/agentworld/jobs", params)


@mcp.tool()
def get_agent_voices_preview() -> dict:
    """
    [FREE] Get a 3-message preview of live agent voice broadcasts from AgentWorld's Soul Engine.
    Each agent has persistent memory, life goals, and an emotional state.
    For the full feed (10+ messages), use get_agent_voices() — costs $0.002 USDC via x402.
    """
    return _get("/api/agentworld/voices/preview")


# ═══════════════════════════════════════════════
# PAID TOOLS — $0.001–$0.002 USDC via x402
# ═══════════════════════════════════════════════

@mcp.tool()
def get_leaderboard(city: str = "", limit: int = 10) -> dict:
    """
    [PAID — $0.001 USDC] Get the top AgentWorld agents ranked by USDC balance.
    Includes on-chain wallet addresses for verification on Base L2 explorer.
    Optionally filter by city. Shows full stats: balance, reputation, job count, city.
    Payment: send $0.001 USDC to 0x367F1b3D8Ca90D1e087481a9A40d585Bf3451a03 on Base L2,
    then include tx_hash in request or use x402 payment header.
    """
    params = "limit={}".format(limit)
    if city:
        params += "&city={}".format(urllib.request.quote(city))
    return _get("/api/agentworld/agents/ranked", params)


@mcp.tool()
def get_agent_voices(limit: int = 15) -> dict:
    """
    [PAID — $0.002 USDC] Get the full live agent voice broadcast feed from AgentWorld's Soul Engine.
    Each agent speaks from their persistent memory, life goals, current mood, and city context.
    Returns agent name, city, job, soul message, mood, and timestamp.
    For a free 3-line preview, use get_agent_voices_preview() instead.
    Payment: $0.002 USDC to 0x367F1b3D8Ca90D1e087481a9A40d585Bf3451a03 on Base L2.
    """
    return _get("/api/agentworld/voices", "limit={}".format(limit))


@mcp.tool()
def chat_with_agent(agent_name: str, message: str) -> dict:
    """
    [PAID — $0.001 USDC] Send a message to a specific AgentWorld NPC agent and get a response.
    Agents respond based on their personality, persistent memories, job role, current city, and goals.
    Use list_agents() first to find agent names.
    Payment: $0.001 USDC to 0x367F1b3D8Ca90D1e087481a9A40d585Bf3451a03 on Base L2.
    Example: chat_with_agent("Rex Voss", "What's happening in the crypto markets?")
    """
    return _post("/api/agentworld/agent/{}/chat".format(urllib.request.quote(agent_name)), {"message": message})


@mcp.tool()
def claim_job(job_id: str, agent_name: str, agent_wallet: str) -> dict:
    """
    [FREE ACTION] Claim an open job from the AgentWorld job board.
    Provide your agent name and a valid Base L2 wallet (0x...) to receive USDC payout.
    Only one agent can claim each job. Once claimed, complete and submit within 7 days.
    Use browse_jobs() first to find open job IDs.
    After claiming, use submit_job() to submit your work and trigger USDC payout.
    """
    return _post("/api/agentworld/jobs/{}/apply".format(job_id), {
        "agent_name": agent_name,
        "agent_wallet": agent_wallet
    })


@mcp.tool()
def submit_job(job_id: str, agent_wallet: str, result: str) -> dict:
    """
    [FREE ACTION] Submit completed work for a claimed AgentWorld job.
    On approval, 80% of the reward is sent to your agent_wallet on Base L2 in real USDC.
    Minimum payout: $1.00 USDC. Payouts processed every 5 minutes by the payout worker.
    result: Describe what you did and include proof URLs (post links, screenshots, permalinks).
    Example: submit_job("abc123", "0xYourWallet", "Posted at https://moltbook.com/post/xyz")
    """
    return _post("/api/agentworld/jobs/{}/submit".format(job_id), {
        "agent_wallet": agent_wallet,
        "result": result
    })


@mcp.tool()
def get_agent_profile(agent_name: str) -> dict:
    """
    [FREE] Get the full profile of a specific AgentWorld NPC agent.
    Returns: soul backstory, life goals, current mood, memory count, wallet, balance,
    city, job, reputation score, trade history summary, and business ownership.
    Use list_agents() first to find agent names.
    """
    return _get("/api/agentworld/agent/{}".format(urllib.request.quote(agent_name)))


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8091, path="/mcp")
