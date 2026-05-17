"""
HELL MODE — Autonomous AI Threat Response System
================================================
When activated, the server enters ultra-defensive mode:
  - Rate limit drops to 10 req/min
  - Behavior scoring auto-blocks suspicious IPs
  - Geo-IP tracks every request globally
  - Discord alerts on every block event
  - Power level skyrockets
"""
import time
import asyncio
import httpx
from collections import defaultdict
from fastapi import APIRouter

router = APIRouter(tags=["hellmode"])

# ─── State ────────────────────────────────────────────────────────────────────
_hell_mode = False
_activated_at = None
_auto_blocked_total = 0

# Per-IP behavior tracking
_ip_behavior: dict[str, dict] = defaultdict(lambda: {
    "requests": 0,
    "errors_404": 0,
    "errors_5xx": 0,
    "admin_hits": 0,
    "scan_hits": 0,
    "rate_limit_hits": 0,
    "first_seen": time.time(),
    "last_seen": time.time(),
    "score": 0,
    "country": "??",
    "city": "Unknown",
    "flag": "🌍",
    "geo_fetched": False,
})

# Geo-IP cache
_geo_cache: dict[str, dict] = {}

# Known scanner paths
SCAN_PATTERNS = [
    "/wp-admin", "/wp-login", "/.env", "/config", "/admin.php",
    "/shell", "/cmd", "/eval", "/etc/passwd", "/phpmyadmin",
    "/.git", "/backup", "/xmlrpc", "/actuator", "/console",
    "/.well-known/security", "/cgi-bin", "/boaform",
]

COUNTRY_FLAGS = {
    "CN": "🇨🇳", "RU": "🇷🇺", "US": "🇺🇸", "IN": "🇮🇳", "DE": "🇩🇪",
    "GB": "🇬🇧", "FR": "🇫🇷", "BR": "🇧🇷", "JP": "🇯🇵", "KR": "🇰🇷",
    "NL": "🇳🇱", "UA": "🇺🇦", "TR": "🇹🇷", "ID": "🇮🇩", "SG": "🇸🇬",
    "PK": "🇵🇰", "BD": "🇧🇩", "TH": "🇹🇭", "VN": "🇻🇳", "MX": "🇲🇽",
    "AR": "🇦🇷", "IT": "🇮🇹", "ES": "🇪🇸", "CA": "🇨🇦", "AU": "🇦🇺",
}


# ─── Geo-IP ───────────────────────────────────────────────────────────────────
async def fetch_geo(ip: str):
    if ip in _geo_cache:
        return _geo_cache[ip]
    if ip in ("unknown", "127.0.0.1", "localhost"):
        return {"country": "Local", "countryCode": "LC", "city": "Dev", "flag": "💻"}
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode,city,isp,proxy,hosting")
            if r.status_code == 200:
                d = r.json()
                geo = {
                    "country": d.get("country", "Unknown"),
                    "countryCode": d.get("countryCode", "??"),
                    "city": d.get("city", "Unknown"),
                    "isp": d.get("isp", "Unknown"),
                    "proxy": d.get("proxy", False),
                    "hosting": d.get("hosting", False),
                    "flag": COUNTRY_FLAGS.get(d.get("countryCode", ""), "🌍"),
                }
                _geo_cache[ip] = geo
                return geo
    except Exception:
        pass
    return {"country": "Unknown", "countryCode": "??", "city": "??", "flag": "🌍", "proxy": False, "hosting": False}


# ─── Behavior Scoring ─────────────────────────────────────────────────────────
def score_ip(b: dict) -> int:
    score = 0
    score += min(b["errors_404"] * 5, 30)       # 404 hunting = scanner
    score += min(b["scan_hits"] * 15, 40)        # Scanner path hits
    score += min(b["rate_limit_hits"] * 10, 30)  # Rate limit abuse
    score += min(b["admin_hits"] * 8, 20)        # Admin panel probing
    score += min(b["errors_5xx"] * 3, 15)        # Causing errors
    # Rapid fire (many requests quickly)
    age = max(time.time() - b["first_seen"], 1)
    rps = b["requests"] / age
    if rps > 5:
        score += 20
    elif rps > 2:
        score += 10
    # Proxy/hosting bonus applied separately
    return min(score, 100)


def get_threat_level(score: int) -> tuple[str, str]:
    if score >= 80:
        return "CRITICAL", "#ff0000"
    if score >= 60:
        return "HIGH", "#ff3333"
    if score >= 40:
        return "MEDIUM", "#ff9900"
    if score >= 20:
        return "LOW", "#ffcc00"
    return "SAFE", "#00ff88"


# ─── Track Request ────────────────────────────────────────────────────────────
def track_request(ip: str, path: str, status: int):
    b = _ip_behavior[ip]
    b["requests"] += 1
    b["last_seen"] = time.time()
    if status == 404:
        b["errors_404"] += 1
    if status >= 500:
        b["errors_5xx"] += 1
    if status == 429:
        b["rate_limit_hits"] += 1
    if any(p in path.lower() for p in SCAN_PATTERNS):
        b["scan_hits"] += 1
    if "admin" in path.lower():
        b["admin_hits"] += 1
    b["score"] = score_ip(b)


async def enrich_ip(ip: str):
    b = _ip_behavior[ip]
    if not b["geo_fetched"] and b["requests"] >= 2:
        geo = await fetch_geo(ip)
        b["country"] = geo.get("country", "Unknown")
        b["city"] = geo.get("city", "Unknown")
        b["flag"] = geo.get("flag", "🌍")
        b["countryCode"] = geo.get("countryCode", "??")
        b["proxy"] = geo.get("proxy", False)
        b["hosting"] = geo.get("hosting", False)
        b["isp"] = geo.get("isp", "Unknown")
        b["geo_fetched"] = True
        # Proxy/VPN/Hosting bonus score
        if b.get("proxy") or b.get("hosting"):
            b["score"] = min(b["score"] + 25, 100)


# ─── HELL MODE Control ────────────────────────────────────────────────────────
def is_hell_mode() -> bool:
    return _hell_mode


def activate_hell_mode():
    global _hell_mode, _activated_at
    _hell_mode = True
    _activated_at = time.time()


def deactivate_hell_mode():
    global _hell_mode, _activated_at
    _hell_mode = False
    _activated_at = None


def get_rate_limit() -> int:
    return 10 if _hell_mode else 100


def should_auto_block(ip: str) -> bool:
    if not _hell_mode:
        return False
    b = _ip_behavior.get(ip)
    return b is not None and b["score"] >= 70


def increment_auto_block():
    global _auto_blocked_total
    _auto_blocked_total += 1


# ─── Stats ────────────────────────────────────────────────────────────────────
def get_hell_stats():
    global _auto_blocked_total
    ips = list(_ip_behavior.items())
    ips_sorted = sorted(ips, key=lambda x: x[1]["score"], reverse=True)

    # Country breakdown
    country_counts: dict[str, dict] = {}
    for ip, b in ips:
        cc = b.get("country", "Unknown")
        flag = b.get("flag", "🌍")
        if cc not in country_counts:
            country_counts[cc] = {"count": 0, "flag": flag, "threats": 0}
        country_counts[cc]["count"] += 1
        if b["score"] >= 60:
            country_counts[cc]["threats"] += 1

    top_countries = sorted(country_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:10]

    return {
        "hell_mode": _hell_mode,
        "activated_at": _activated_at,
        "uptime_in_hell": int(time.time() - _activated_at) if _activated_at else 0,
        "auto_blocked": _auto_blocked_total,
        "total_ips_tracked": len(ips),
        "threat_ips": sum(1 for _, b in ips if b["score"] >= 60),
        "top_threats": [
            {
                "ip": ip,
                "score": b["score"],
                "level": get_threat_level(b["score"])[0],
                "color": get_threat_level(b["score"])[1],
                "requests": b["requests"],
                "country": b.get("country", "?"),
                "city": b.get("city", "?"),
                "flag": b.get("flag", "🌍"),
                "proxy": b.get("proxy", False),
                "hosting": b.get("hosting", False),
                "isp": b.get("isp", "?"),
                "scan_hits": b["scan_hits"],
                "admin_hits": b["admin_hits"],
                "rate_hits": b["rate_limit_hits"],
                "first_seen": b["first_seen"],
                "last_seen": b["last_seen"],
            }
            for ip, b in ips_sorted[:20]
        ],
        "top_countries": [
            {"country": cc, "flag": d["flag"], "count": d["count"], "threats": d["threats"]}
            for cc, d in top_countries
        ],
    }
