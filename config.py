"""Octa Financial Control — Configuration."""

APP_NAME    = "Financial Control"
APP_ICON    = "💶"
APP_VERSION = "1.0.0"

DARK = {
    "bg":      "#0f1421",
    "bg2":     "#1a2235",
    "bg3":     "#232f45",
    "border":  "rgba(255,255,255,0.09)",
    "text":    "#e2e8f0",
    "muted":   "#8899b0",
    "accent":  "#00BCD4",
    "accent2": "#FF6B35",
    "sidebar": "#1B2A4A",
    "success": "#6fcf97",
    "warning": "#f6cc52",
    "danger":  "#fc8181",
}

# Cost categories — order matters for display and Excel export
COST_CATEGORIES = [
    ("personnel",            "1. Personnel Costs"),
    ("travel",               "2. Travel & Subsistence"),
    ("equipment",            "3. Equipment & Infrastructure"),
    ("other_goods_services", "4. Other Goods & Services"),
    ("subcontracting",       "5. Subcontracting"),
    ("third_parties",        "6. Funding for Third Parties"),
    ("overhead",             "7. Overhead / Indirect Costs"),
]
CAT_KEYS   = [c[0] for c in COST_CATEGORIES]
CAT_LABELS = dict(COST_CATEGORIES)

# Categories that feed into overhead calculation base
OVERHEAD_BASE_CATS = {"personnel","travel","equipment","other_goods_services"}

# Category colours for charts
CAT_COLORS = {
    "personnel":            "#00BCD4",
    "travel":               "#6fcf97",
    "equipment":            "#f6cc52",
    "other_goods_services": "#FF6B35",
    "subcontracting":       "#9b59b6",
    "third_parties":        "#3498db",
    "overhead":             "#8899b0",
}

# Budget health thresholds
ALERT_AMBER = 75   # % spent → amber warning
ALERT_RED   = 95   # % spent → red danger

# Proposal statuses that should appear in this app
FUNDED_STATUS    = {"Funded", "Ended"}
FUNDED_LIFECYCLE = {"funded_project", "ongoing_project", "ended_project"}
