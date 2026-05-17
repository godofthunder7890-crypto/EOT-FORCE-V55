"""
GOD MODE — Owner-Only Supreme Control System
=============================================
Secret: Click H52 logo 5x rapidly after login → enter GOD KEY
GOD KEY is set via GOD_MODE_KEY env var (default: HELL52-GOD-ULTRA-9999)

Powers:
  - Nuclear Option: block ALL IPs except whitelist
  - Country Blacklist: ban entire nations
  - IP Whitelist: bypass ALL security
  - Custom Response Injector: specific IP gets custom JSON
  - Time Bomb: schedule HELL MODE at exact time
  - God Bypass Token: one token that bypasses EVERYTHING
  - Live Wire: real-time request interception
  - Kill Switch: bring server to emergency lockdown
  - Data Forge: inject fake threat data to scare hackers
  - Resurrection: instantly clear all blocks
"""
import os
import time
import json
from fastapi import APIRouter

router = APIRouter(tags=["godmode"])

GOD_KEY = os.environ.get("GOD_MODE_KEY", "HELL52-GOD-ULTRA-9999")
GOD_BYPASS_TOKEN = os.environ.get("GOD_BYPASS_TOKEN", "GOD52-BYPASS-ALL-9999")

# ─── State ────────────────────────────────────────────────────────────────────
_god_active = False
_god_activated_at = None
_god_log = []
_country_blacklist: set[str] = set()
_ip_whitelist: set[str] = set()
_custom_responses: dict[str, dict] = {}
_timebomb: dict = {"active": False, "trigger_at": None, "action": None}
_nuclear_active = False
_kill_switch = False
_total_god_actions = 0


def log_god_action(action: str, detail: str = ""):
    global _total_god_actions
    _total_god_actions += 1
    _god_log.insert(0, {
        "action": action,
        "detail": detail,
        "time": time.strftime("%H:%M:%S"),
        "timestamp": time.time(),
    })
    if len(_god_log) > 100:
        _god_log.pop()


# ─── Auth ─────────────────────────────────────────────────────────────────────
def verify_god_key(key: str) -> bool:
    return key == GOD_KEY


def is_god_bypass(token: str) -> bool:
    return token == GOD_BYPASS_TOKEN


def is_god_active() -> bool:
    return _god_active


def is_whitelisted(ip: str) -> bool:
    return ip in _ip_whitelist


def is_country_blocked(country_code: str) -> bool:
    return country_code.upper() in _country_blacklist


def is_kill_switch() -> bool:
    return _kill_switch


def get_custom_response(ip: str):
    return _custom_responses.get(ip)


# ─── Timebomb checker ─────────────────────────────────────────────────────────
def check_timebomb():
    if not _timebomb["active"]:
        return None
    if time.time() >= _timebomb["trigger_at"]:
        action = _timebomb["action"]
        _timebomb["active"] = False
        _timebomb["trigger_at"] = None
        _timebomb["action"] = None
        log_god_action("💣 TIMEBOMB TRIGGERED", f"Action: {action}")
        return action
    return None


# ─── God Stats ────────────────────────────────────────────────────────────────
def get_god_stats():
    tb_remaining = 0
    if _timebomb["active"] and _timebomb["trigger_at"]:
        tb_remaining = max(0, int(_timebomb["trigger_at"] - time.time()))

    return {
        "god_active": _god_active,
        "activated_at": _god_activated_at,
        "uptime": int(time.time() - _god_activated_at) if _god_activated_at else 0,
        "nuclear_active": _nuclear_active,
        "kill_switch": _kill_switch,
        "country_blacklist": list(_country_blacklist),
        "ip_whitelist": list(_ip_whitelist),
        "custom_responses": list(_custom_responses.keys()),
        "timebomb": {
            "active": _timebomb["active"],
            "trigger_in": tb_remaining,
            "action": _timebomb["action"],
        },
        "total_actions": _total_god_actions,
        "god_log": _god_log[:30],
    }


# ─── God Powers ───────────────────────────────────────────────────────────────
def activate_god(key: str) -> bool:
    global _god_active, _god_activated_at
    if not verify_god_key(key):
        return False
    _god_active = True
    _god_activated_at = time.time()
    log_god_action("👑 GOD MODE ACTIVATED", "Supreme control engaged")
    return True


def deactivate_god():
    global _god_active, _god_activated_at, _nuclear_active, _kill_switch
    _god_active = False
    _god_activated_at = None
    _nuclear_active = False
    _kill_switch = False
    log_god_action("💤 GOD MODE DEACTIVATED", "Returned to mortal state")


def activate_nuclear():
    global _nuclear_active
    _nuclear_active = True
    log_god_action("☢️ NUCLEAR OPTION", "All non-whitelisted IPs blocked")


def deactivate_nuclear():
    global _nuclear_active
    _nuclear_active = False
    log_god_action("✅ Nuclear deactivated")


def set_kill_switch(state: bool):
    global _kill_switch
    _kill_switch = state
    log_god_action("🔴 KILL SWITCH" if state else "🟢 Kill switch OFF")


def blacklist_country(code: str):
    _country_blacklist.add(code.upper())
    log_god_action("🌍 Country blocked", code.upper())


def unblacklist_country(code: str):
    _country_blacklist.discard(code.upper())
    log_god_action("✅ Country unblocked", code.upper())


def whitelist_ip(ip: str):
    _ip_whitelist.add(ip)
    log_god_action("⭐ IP Whitelisted", ip)


def unwhitelist_ip(ip: str):
    _ip_whitelist.discard(ip)
    log_god_action("❌ IP Removed from whitelist", ip)


def set_custom_response(ip: str, data: dict):
    _custom_responses[ip] = data
    log_god_action("🎭 Custom response set", f"IP: {ip}")


def clear_custom_response(ip: str):
    _custom_responses.pop(ip, None)
    log_god_action("🗑 Custom response cleared", ip)


def set_timebomb(seconds: int, action: str):
    _timebomb["active"] = True
    _timebomb["trigger_at"] = time.time() + seconds
    _timebomb["action"] = action
    log_god_action("💣 TIMEBOMB SET", f"In {seconds}s → {action}")


def cancel_timebomb():
    _timebomb["active"] = False
    log_god_action("💣 Timebomb cancelled")


def resurrection():
    """Clear ALL blocks, reset everything to fresh state."""
    from routers.admin import _blocked_ips
    _blocked_ips.clear()
    _country_blacklist.clear()
    global _nuclear_active, _kill_switch
    _nuclear_active = False
    _kill_switch = False
    log_god_action("🌅 RESURRECTION", "All blocks cleared, server reborn")


def is_nuclear() -> bool:
    return _nuclear_active
