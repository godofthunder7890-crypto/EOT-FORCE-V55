import asyncio
import time
import httpx
from fastapi import APIRouter

router = APIRouter(tags=["threats"])

_cache = {
    "threats": [],
    "last_updated": 0,
    "update_count": 0,
    "power_level": 1.0,
}

THREAT_SOURCES = [
    "https://cve.circl.lu/api/last/10",
]

STATIC_THREATS = [
    {"id": "SQL-INJECT-001", "name": "SQL Injection", "severity": "CRITICAL",
     "description": "Attacker inserts malicious SQL into input fields to access or destroy database.",
     "protection": "Use parameterized queries, never trust raw input, use ORM like SQLAlchemy."},
    {"id": "XSS-002", "name": "Cross-Site Scripting (XSS)", "severity": "HIGH",
     "description": "Malicious scripts injected into web pages viewed by other users.",
     "protection": "Sanitize all user input, use Content-Security-Policy headers, escape HTML output."},
    {"id": "BRUTE-003", "name": "Brute Force Attack", "severity": "HIGH",
     "description": "Automated repeated attempts to guess passwords or API keys.",
     "protection": "Rate limiting, account lockout, strong passwords, 2FA."},
    {"id": "DDOS-004", "name": "DDoS Attack", "severity": "CRITICAL",
     "description": "Flooding server with traffic to make it unavailable.",
     "protection": "Rate limiting, CDN, IP blacklisting, Cloudflare protection."},
    {"id": "MITM-005", "name": "Man-in-the-Middle", "severity": "HIGH",
     "description": "Attacker secretly intercepts communication between two parties.",
     "protection": "Use HTTPS/TLS everywhere, certificate pinning, HSTS headers."},
    {"id": "CSRF-006", "name": "CSRF Attack", "severity": "MEDIUM",
     "description": "Tricks users into performing unwanted actions on authenticated sites.",
     "protection": "CSRF tokens, SameSite cookies, verify Origin header."},
    {"id": "PATH-007", "name": "Path Traversal", "severity": "HIGH",
     "description": "Access files/directories outside the web root folder.",
     "protection": "Validate & sanitize file paths, use allowlists, never trust user-supplied paths."},
    {"id": "IDOR-008", "name": "Insecure Direct Object Reference", "severity": "HIGH",
     "description": "Access unauthorized data by manipulating IDs in requests.",
     "protection": "Verify ownership on every request, use UUIDs instead of sequential IDs."},
    {"id": "SSRF-009", "name": "Server-Side Request Forgery", "severity": "CRITICAL",
     "description": "Attacker makes server send requests to internal/unintended targets.",
     "protection": "Whitelist allowed URLs, block internal IP ranges, validate all URLs."},
    {"id": "RATELIMIT-010", "name": "API Abuse / Scraping", "severity": "MEDIUM",
     "description": "Automated bots scraping or abusing API endpoints without limits.",
     "protection": "Rate limiting per IP, API keys, CAPTCHA, request throttling."},
]


async def _fetch_live_threats():
    live = []
    async with httpx.AsyncClient(timeout=10) as client:
        for url in THREAT_SOURCES:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        for item in data[:5]:
                            live.append({
                                "id": item.get("id", "CVE-UNKNOWN"),
                                "name": item.get("id", "Unknown CVE"),
                                "severity": "HIGH",
                                "description": (item.get("summary") or "No description")[:200],
                                "protection": "Apply latest security patches. Check vendor advisories.",
                                "source": "live",
                                "published": item.get("Published", ""),
                            })
            except Exception:
                pass
    return live


async def refresh_threats():
    live = await _fetch_live_threats()
    combined = STATIC_THREATS + live
    _cache["threats"] = combined
    _cache["last_updated"] = time.time()
    _cache["update_count"] += 1
    _cache["power_level"] = round(1.0 + (_cache["update_count"] * 0.05), 2)


async def auto_update_loop():
    while True:
        try:
            await refresh_threats()
        except Exception:
            pass
        await asyncio.sleep(3600)


@router.get("/threats")
async def get_threats():
    if not _cache["threats"]:
        await refresh_threats()
    age = int(time.time() - _cache["last_updated"])
    return {
        "total": len(_cache["threats"]),
        "update_count": _cache["update_count"],
        "power_level": _cache["power_level"],
        "last_updated_seconds_ago": age,
        "threats": _cache["threats"],
    }


@router.post("/threats/refresh")
async def force_refresh():
    await refresh_threats()
    return {
        "status": "refreshed",
        "total": len(_cache["threats"]),
        "power_level": _cache["power_level"],
    }


def get_cache():
    return _cache
