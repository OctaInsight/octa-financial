"""Octa Financial Control — Database layer."""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone, date
from config import (FUNDED_STATUS, FUNDED_LIFECYCLE, OVERHEAD_BASE_CATS,
                    CAT_KEYS, COST_CATEGORIES)
import json


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["supabase"]["url"],
                         st.secrets["supabase"]["key"])

def db() -> Client:
    return _client()

def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Funded projects ───────────────────────────────────────────────────────────

def get_funded_projects(organisation: str = "", is_admin: bool = False) -> tuple:
    try:
        resp = db().table("proposals").select("*") \
                   .order("proposal_id", desc=True).execute()
        all_props = resp.data or []
    except Exception as e:
        return [], str(e)

    projects = [
        p for p in all_props
        if (p.get("status") or "")           in FUNDED_STATUS
        or (p.get("lifecycle_status") or "")  in FUNDED_LIFECYCLE
    ]
    return projects, None


def get_project(proposal_id: str) -> dict | None:
    try:
        r = db().table("proposals").select("*") \
                .eq("proposal_id", proposal_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


# ── Work packages ─────────────────────────────────────────────────────────────

def get_work_packages(proposal_id: str) -> list:
    try:
        return db().table("work_packages").select("*") \
                   .eq("proposal_id", proposal_id) \
                   .order("wp_number").execute().data or []
    except Exception:
        return []


# ── Partners ──────────────────────────────────────────────────────────────────

def get_project_partners(proposal_id: str) -> list:
    try:
        prop = get_project(proposal_id)
        if not prop:
            return []
        names = []
        coord = (prop.get("coordinator") or "").strip()
        if coord: names.append(coord)
        plist = prop.get("partners_list") or []
        if isinstance(plist, str):
            try:    plist = json.loads(plist)
            except: plist = [plist]
        names.extend([str(n).strip() for n in plist if n])
        if not names:
            return []
        all_p = db().table("partners").select(
            "id,full_name,short_name,country,partner_type"
        ).order("full_name").execute().data or []
        result = []; seen = set()
        for name in names:
            nl = name.lower()
            for p in all_p:
                if p["id"] in seen: continue
                fn = (p.get("full_name") or "").lower()
                sn = (p.get("short_name") or "").lower()
                if nl in fn or fn in nl or (sn and (nl in sn or sn in nl)):
                    is_coord = (name == coord)
                    result.append({**p, "is_coordinator": is_coord})
                    seen.add(p["id"])
                    break
        return result
    except Exception:
        return []


# ── Budget entries ────────────────────────────────────────────────────────────

def get_budget_entries(proposal_id: str) -> list:
    try:
        return db().table("budget_entries").select("*") \
                   .eq("proposal_id", proposal_id).execute().data or []
    except Exception:
        return []


def upsert_budget_entry(data: dict) -> tuple:
    """Create or update a budget entry. Returns (success, entry_id|error)."""
    try:
        data["updated_at"] = _now()
        existing = db().table("budget_entries").select("budget_entry_id") \
                       .eq("proposal_id", data["proposal_id"]) \
                       .eq("wp_id",        data["wp_id"]) \
                       .eq("partner_id",   data["partner_id"]) \
                       .eq("cost_category",data["cost_category"]) \
                       .execute()
        if existing.data:
            eid = existing.data[0]["budget_entry_id"]
            db().table("budget_entries").update(data) \
                .eq("budget_entry_id", eid).execute()
            return True, eid
        r = db().table("budget_entries").insert(data).execute()
        return True, r.data[0]["budget_entry_id"] if r.data else None
    except Exception as e:
        return False, str(e)


def update_actual_spent(entry_id: int, actual: float,
                         notes: str = "", period: int = 1,
                         user_id: int = None) -> bool:
    try:
        patch = {
            "actual_spent_amount": actual,
            "notes":               notes,
            "reported_period":     period,
            "updated_at":          _now(),
        }
        if user_id: patch["last_updated_by"] = user_id
        db().table("budget_entries").update(patch) \
            .eq("budget_entry_id", entry_id).execute()
        return True
    except Exception:
        return False


# ── Overhead settings ─────────────────────────────────────────────────────────

def get_overhead_settings(proposal_id: str) -> dict:
    """Returns {partner_id: overhead_percentage}."""
    try:
        rows = db().table("overhead_settings").select("*") \
                   .eq("proposal_id", proposal_id).execute().data or []
        return {r["partner_id"]: float(r["overhead_percentage"]) for r in rows}
    except Exception:
        return {}


def save_overhead_setting(proposal_id: str, partner_id: int,
                           pct: float) -> bool:
    try:
        db().table("overhead_settings").upsert({
            "proposal_id":         proposal_id,
            "partner_id":          partner_id,
            "overhead_percentage": pct,
            "updated_at":          _now(),
        }, on_conflict="proposal_id,partner_id").execute()
        return True
    except Exception:
        return False


# ── Structured budget data ────────────────────────────────────────────────────

def get_budget_matrix(proposal_id: str) -> dict:
    """
    Returns nested dict:
    {partner_id: {wp_id: {category: {planned, actual}}}}
    Plus totals: project_total_planned, project_total_actual
    Also computes overhead from overhead_settings.
    """
    entries  = get_budget_entries(proposal_id)
    oh_pcts  = get_overhead_settings(proposal_id)

    matrix: dict = {}
    for e in entries:
        pid = e.get("partner_id")
        wid = e.get("wp_id")
        cat = e.get("cost_category","")
        if not pid or not wid or not cat:
            continue
        if pid not in matrix:  matrix[pid] = {}
        if wid not in matrix[pid]: matrix[pid][wid] = {}
        matrix[pid][wid][cat] = {
            "planned": float(e.get("planned_amount",0) or 0),
            "actual":  float(e.get("actual_spent_amount",0) or 0),
            "entry_id": e.get("budget_entry_id"),
            "notes":    e.get("notes",""),
            "period":   e.get("reported_period",1),
        }

    # Inject auto-calculated overhead
    for pid, wps in matrix.items():
        oh_pct = oh_pcts.get(pid, 25.0) / 100
        for wid, cats in wps.items():
            planned_base = sum(
                cats.get(c,{}).get("planned",0)
                for c in OVERHEAD_BASE_CATS
            )
            actual_base = sum(
                cats.get(c,{}).get("actual",0)
                for c in OVERHEAD_BASE_CATS
            )
            matrix[pid][wid]["overhead"] = {
                "planned":  round(planned_base * oh_pct, 2),
                "actual":   round(actual_base  * oh_pct, 2),
                "entry_id": None,  # computed — not stored directly
                "auto":     True,
            }

    return matrix


def get_budget_summary_by_partner(proposal_id: str) -> list:
    """
    Returns [{ partner_id, partner_name, planned, actual, remaining,
               pct_spent, by_category:{cat:{planned,actual}} }, ...]
    """
    matrix   = get_budget_matrix(proposal_id)
    partners = get_project_partners(proposal_id)
    p_map    = {p["id"]: p for p in partners}

    result = []
    for pid, wps in matrix.items():
        by_cat: dict = {k: {"planned":0,"actual":0} for k in CAT_KEYS}
        for wid, cats in wps.items():
            for cat in CAT_KEYS:
                d = cats.get(cat, {})
                by_cat[cat]["planned"] += d.get("planned",0)
                by_cat[cat]["actual"]  += d.get("actual",0)

        total_p = sum(v["planned"] for v in by_cat.values())
        total_a = sum(v["actual"]  for v in by_cat.values())
        p       = p_map.get(pid,{})
        result.append({
            "partner_id":   pid,
            "partner_name": p.get("full_name","") or p.get("short_name","") or f"Partner {pid}",
            "short_name":   p.get("short_name","") or "",
            "is_coord":     p.get("is_coordinator",False),
            "planned":      total_p,
            "actual":       total_a,
            "remaining":    total_p - total_a,
            "pct_spent":    round(total_a / total_p * 100, 1) if total_p else 0,
            "by_category":  by_cat,
        })

    return sorted(result, key=lambda x: -x["planned"])


def get_project_totals(proposal_id: str) -> dict:
    """Project-level totals across all partners and WPs."""
    rows = get_budget_entries(proposal_id)
    oh   = get_overhead_settings(proposal_id)
    matrix = get_budget_matrix(proposal_id)

    by_cat = {k: {"planned":0,"actual":0} for k in CAT_KEYS}
    for pid, wps in matrix.items():
        for wid, cats in wps.items():
            for cat in CAT_KEYS:
                d = cats.get(cat,{})
                by_cat[cat]["planned"] += d.get("planned",0)
                by_cat[cat]["actual"]  += d.get("actual",0)

    total_p = sum(v["planned"] for v in by_cat.values())
    total_a = sum(v["actual"]  for v in by_cat.values())
    return {
        "planned":    total_p,
        "actual":     total_a,
        "remaining":  total_p - total_a,
        "pct_spent":  round(total_a / total_p * 100,1) if total_p else 0,
        "by_category": by_cat,
    }


# ── Financial snapshots ───────────────────────────────────────────────────────

def save_financial_snapshot(proposal_id: str, partner_id: int,
                             period: int, by_cat: dict,
                             total_planned: float, notes: str = "") -> bool:
    try:
        db().table("financial_snapshots").upsert({
            "proposal_id":        proposal_id,
            "partner_id":         partner_id,
            "reporting_period":   period,
            "snapshot_date":      date.today().isoformat(),
            "personnel_spent":    by_cat.get("personnel",{}).get("actual",0),
            "travel_spent":       by_cat.get("travel",{}).get("actual",0),
            "equipment_spent":    by_cat.get("equipment",{}).get("actual",0),
            "other_goods_spent":  by_cat.get("other_goods_services",{}).get("actual",0),
            "subcontracting_spent":by_cat.get("subcontracting",{}).get("actual",0),
            "third_parties_spent":by_cat.get("third_parties",{}).get("actual",0),
            "overhead_spent":     by_cat.get("overhead",{}).get("actual",0),
            "total_spent":        sum(v.get("actual",0) for v in by_cat.values()),
            "total_planned":      total_planned,
            "notes":              notes,
        }, on_conflict="proposal_id,partner_id,reporting_period").execute()
        return True
    except Exception:
        return False


def get_financial_snapshots(proposal_id: str,
                             partner_id: int = None) -> list:
    try:
        q = db().table("financial_snapshots").select("*") \
                .eq("proposal_id", proposal_id)
        if partner_id:
            q = q.eq("partner_id", partner_id)
        return q.order("reporting_period").execute().data or []
    except Exception:
        return []
