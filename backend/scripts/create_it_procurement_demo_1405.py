"""
IT procurement demo dataset for Jalali year 1405.

Prefix:
  DEMO_IT_1405_

Usage:
  python scripts/create_it_procurement_demo_1405.py --mode create
  python scripts/create_it_procurement_demo_1405.py --mode cleanup
  python scripts/create_it_procurement_demo_1405.py --mode verify

Docker (from the compose project directory):
  docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode create
  docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode cleanup
  docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode verify

Currency convention:
  All monetary values are stored as Iranian Rial (IRR).
  1 Toman = 10 Rial. Example: 450,000,000 IRR = 45,000,000 Toman.
  Prices are demo assumptions for presentation, not official supplier quotes.

Date convention:
  Business dates are Jalali 1 Shahrivar 1405 through 29 Esfand 1405.
  The database stores Gregorian dates. Conversion table is hardcoded below
  (no jdatetime dependency).

Why direct ORM inserts (not HTTP API):
  There is no bulk seed API. Creating ~900 project items and ~600 options
  over HTTP would be slow and would still write the same tables. This script
  uses the live SQLAlchemy models and the same fields the services persist.
  Finalization, assignment, package coverage, and option timing follow the
  current application contracts. A sample of options is passed through
  apply_procurement_option_persistence_contract after insert.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import delete, false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
import app.models_invoice_payment  # noqa: F401
from app.models import (
    AuditLog,
    BudgetData,
    Currency,
    DeliveryOption,
    ItemMaster,
    ItemSubItem,
    OptimizationSubmission,
    PackageSubItem,
    PaymentMethod,
    ProcurementAssignment,
    ProcurementCostComponent,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectAssignment,
    ProjectItem,
    ProjectItemStatus,
    ProjectItemSubItem,
    ProjectPhase,
    Supplier,
    User,
)
from app.services.procurement_financials_service import (
    apply_procurement_option_persistence_contract,
)


PREFIX = "DEMO_IT_1405_"
CURRENCY_CODE = "IRR"
CURRENCY_UNIT = "Iranian Rial (IRR). 1 Toman = 10 Rial."
JALALI_START = "1405-06-01"  # 1 Shahrivar 1405
JALALI_END = "1405-12-29"  # 29 Esfand 1405
GREGORIAN_START = date(2026, 8, 23)
GREGORIAN_END = date(2027, 3, 20)
SHORTAGE_MONTH_JALALI = "Mehr 1405"
SHORTAGE_BUDGET_DATE = date(2026, 9, 23)  # 1 Mehr 1405
FX_USD_IRR = Decimal("850000")  # demo assumption, not a live market feed
CONTRACT_SAMPLE_LIMIT = 12

# Jalali month starts stored as Gregorian (1405).
JALALI_MONTH_STARTS: List[Tuple[str, date]] = [
    ("Shahrivar 1405", date(2026, 8, 23)),
    ("Mehr 1405", date(2026, 9, 23)),
    ("Aban 1405", date(2026, 10, 23)),
    ("Azar 1405", date(2026, 11, 22)),
    ("Dey 1405", date(2026, 12, 22)),
    ("Bahman 1405", date(2027, 1, 21)),
    ("Esfand 1405", date(2027, 2, 20)),
]

# Demo unit sales prices in IRR (Rial). These are presentation assumptions.
PRICING_ASSUMPTIONS: Dict[str, Dict[str, Any]] = {
    "RACK_SERVER": {
        "name_en": "Rack Server",
        "name_fa": "سرور رک‌مونت",
        "company": "Dell",
        "model": "PowerEdge R760",
        "category": "Server Equipment",
        "unit": "unit",
        "family": "server",
        "sales_irr": 3_500_000_000,
        "subitems": [
            ("Chassis", 1),
            ("CPU", 2),
            ("Heatsink", 2),
            ("RAM", 8),
            ("NVMe SSD", 4),
            ("HDD Storage", 4),
            ("RAID Controller", 1),
            ("Power Supply", 2),
            ("Rail Kit", 1),
            ("Network Card", 2),
            ("TPM Module", 1),
            ("Warranty Support Pack", 1),
        ],
    },
    "GPU_SERVER": {
        "name_en": "GPU Server",
        "name_fa": "سرور پردازنده گرافیکی",
        "company": "Dell",
        "model": "PowerEdge XE9680",
        "category": "Server Equipment",
        "unit": "unit",
        "family": "server",
        "sales_irr": 12_000_000_000,
        "subitems": [
            ("Chassis", 1),
            ("CPU", 2),
            ("Heatsink", 2),
            ("RAM", 16),
            ("NVMe SSD", 8),
            ("RAID Controller", 1),
            ("Power Supply", 4),
            ("Rail Kit", 1),
            ("Network Card", 2),
            ("GPU Card", 4),
            ("TPM Module", 1),
            ("Warranty Support Pack", 1),
        ],
    },
    "STORAGE_SERVER": {
        "name_en": "Storage Server",
        "name_fa": "سرور ذخیره‌سازی",
        "company": "HPE",
        "model": "ProLiant DL380 Gen11",
        "category": "Server Equipment",
        "unit": "unit",
        "family": "server",
        "sales_irr": 4_200_000_000,
        "subitems": [
            ("Chassis", 1),
            ("CPU", 2),
            ("Heatsink", 2),
            ("RAM", 12),
            ("NVMe SSD", 2),
            ("HDD Storage", 12),
            ("RAID Controller", 1),
            ("Power Supply", 2),
            ("Rail Kit", 1),
            ("Network Card", 2),
            ("Warranty Support Pack", 1),
        ],
    },
    "TOWER_SERVER": {
        "name_en": "Tower Server",
        "name_fa": "سرور تاور",
        "company": "HPE",
        "model": "ProLiant ML350",
        "category": "Server Equipment",
        "unit": "unit",
        "family": "server",
        "sales_irr": 1_800_000_000,
        "subitems": [
            ("Chassis", 1),
            ("CPU", 1),
            ("Heatsink", 1),
            ("RAM", 4),
            ("NVMe SSD", 2),
            ("HDD Storage", 4),
            ("Power Supply", 1),
            ("Network Card", 1),
            ("Warranty Support Pack", 1),
        ],
    },
    "CORE_SWITCH": {
        "name_en": "Core Switch",
        "name_fa": "سوییچ هسته",
        "company": "Cisco",
        "model": "Catalyst 9500",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 2_800_000_000,
        "subitems": [
            ("Main Device", 1),
            ("Power Module", 2),
            ("SFP Transceiver", 16),
            ("Rackmount Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "ACCESS_SWITCH": {
        "name_en": "Access Switch",
        "name_fa": "سوییچ دسترسی",
        "company": "Cisco",
        "model": "Catalyst 9200",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 450_000_000,
        "subitems": [
            ("Main Device", 1),
            ("Power Module", 1),
            ("SFP Transceiver", 4),
            ("Rackmount Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "ROUTER": {
        "name_en": "Router",
        "name_fa": "روتر",
        "company": "Cisco",
        "model": "ISR 4451",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 980_000_000,
        "subitems": [
            ("Main Device", 1),
            ("Power Module", 1),
            ("SFP Transceiver", 4),
            ("Rackmount Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "FIREWALL": {
        "name_en": "Firewall",
        "name_fa": "فایروال",
        "company": "Fortinet",
        "model": "FortiGate 600F",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 1_800_000_000,
        "subitems": [
            ("Main Device", 1),
            ("Power Module", 2),
            ("SFP Transceiver", 8),
            ("Rackmount Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "WAP": {
        "name_en": "Wireless Access Point",
        "name_fa": "اکسس‌پوینت بی‌سیم",
        "company": "Cisco",
        "model": "Catalyst 9130",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 85_000_000,
        "subitems": [
            ("Main Device", 1),
            ("Mounting Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "SFP_MODULE": {
        "name_en": "SFP Module",
        "name_fa": "ماژول SFP",
        "company": "Cisco",
        "model": "SFP-10G-SR",
        "category": "Network Equipment",
        "unit": "piece",
        "family": "network",
        "sales_irr": 18_000_000,
        "subitems": [],
    },
    "PATCH_PANEL": {
        "name_en": "Patch Panel",
        "name_fa": "پچ‌پنل",
        "company": "Panduit",
        "model": "CP24",
        "category": "Network Equipment",
        "unit": "unit",
        "family": "network",
        "sales_irr": 12_000_000,
        "subitems": [],
    },
    "NAS": {
        "name_en": "NAS Storage",
        "name_fa": "ذخیره‌ساز NAS",
        "company": "Synology",
        "model": "SA6400",
        "category": "Storage and Backup",
        "unit": "unit",
        "family": "storage",
        "sales_irr": 2_200_000_000,
        "subitems": [
            ("Controller", 1),
            ("Disk Shelf", 1),
            ("Enterprise HDD", 12),
            ("SSD Cache", 2),
            ("Backup License", 1),
            ("Support Contract", 1),
        ],
    },
    "SAN": {
        "name_en": "SAN Storage",
        "name_fa": "ذخیره‌ساز SAN",
        "company": "Dell",
        "model": "PowerStore 500T",
        "category": "Storage and Backup",
        "unit": "unit",
        "family": "storage",
        "sales_irr": 6_500_000_000,
        "subitems": [
            ("Controller", 2),
            ("Disk Shelf", 2),
            ("Enterprise HDD", 24),
            ("SSD Cache", 4),
            ("HBA Card", 2),
            ("Backup License", 1),
            ("Support Contract", 1),
        ],
    },
    "BACKUP_APPLIANCE": {
        "name_en": "Backup Appliance",
        "name_fa": "دستگاه پشتیبان‌گیری",
        "company": "Dell",
        "model": "PowerProtect DP4400",
        "category": "Storage and Backup",
        "unit": "unit",
        "family": "storage",
        "sales_irr": 3_100_000_000,
        "subitems": [
            ("Controller", 1),
            ("Disk Shelf", 1),
            ("Enterprise HDD", 8),
            ("SSD Cache", 2),
            ("Backup License", 1),
            ("Support Contract", 1),
        ],
    },
    "TAPE_BACKUP": {
        "name_en": "Tape Backup Unit",
        "name_fa": "کتابخانه نوار پشتیبان",
        "company": "IBM",
        "model": "TS4300",
        "category": "Storage and Backup",
        "unit": "unit",
        "family": "storage",
        "sales_irr": 1_450_000_000,
        "subitems": [
            ("Controller", 1),
            ("Tape Drive", 2),
            ("Rackmount Kit", 1),
            ("Backup License", 1),
            ("Support Contract", 1),
        ],
    },
    "NVR": {
        "name_en": "CCTV NVR",
        "name_fa": "دستگاه ضبط تصاویر",
        "company": "Hikvision",
        "model": "DS-9664NI",
        "category": "Security and Monitoring",
        "unit": "unit",
        "family": "security",
        "sales_irr": 280_000_000,
        "subitems": [
            ("Main Unit", 1),
            ("Storage Disk", 4),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "IP_CAMERA": {
        "name_en": "IP Camera",
        "name_fa": "دوربین تحت شبکه",
        "company": "Hikvision",
        "model": "DS-2CD2387",
        "category": "Security and Monitoring",
        "unit": "unit",
        "family": "security",
        "sales_irr": 80_000_000,
        "subitems": [
            ("Camera Module", 1),
            ("Lens", 1),
            ("Mounting Kit", 1),
            ("License", 1),
        ],
    },
    "ACCESS_CONTROL": {
        "name_en": "Access Control Controller",
        "name_fa": "کنترلر کنترل تردد",
        "company": "Hikvision",
        "model": "DS-K2604",
        "category": "Security and Monitoring",
        "unit": "unit",
        "family": "security",
        "sales_irr": 95_000_000,
        "subitems": [
            ("Main Unit", 1),
            ("Mounting Kit", 1),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "SECURITY_SENSOR": {
        "name_en": "Security Sensor",
        "name_fa": "سنسور امنیتی",
        "company": "Hikvision",
        "model": "DS-PDP18",
        "category": "Security and Monitoring",
        "unit": "piece",
        "family": "security",
        "sales_irr": 8_500_000,
        "subitems": [],
    },
    "SIEM": {
        "name_en": "SIEM Appliance",
        "name_fa": "دستگاه SIEM",
        "company": "Splunk",
        "model": "Enterprise 48",
        "category": "Security and Monitoring",
        "unit": "unit",
        "family": "security",
        "sales_irr": 4_800_000_000,
        "subitems": [
            ("Main Unit", 1),
            ("Storage Disk", 8),
            ("License", 1),
            ("Support Contract", 1),
        ],
    },
    "LAPTOP": {
        "name_en": "Business Laptop",
        "name_fa": "لپ‌تاپ سازمانی",
        "company": "Lenovo",
        "model": "ThinkPad T14",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 450_000_000,
        "subitems": [
            ("Device", 1),
            ("RAM Upgrade", 1),
            ("SSD Upgrade", 1),
            ("Adapter", 1),
            ("Warranty", 1),
        ],
    },
    "WORKSTATION": {
        "name_en": "Engineering Workstation",
        "name_fa": "ورک‌استیشن مهندسی",
        "company": "HP",
        "model": "Z4 G5",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 950_000_000,
        "subitems": [
            ("Device", 1),
            ("RAM Upgrade", 1),
            ("SSD Upgrade", 1),
            ("Adapter", 1),
            ("Warranty", 1),
        ],
    },
    "MINI_PC": {
        "name_en": "Mini PC",
        "name_fa": "مینی کامپیوتر",
        "company": "Dell",
        "model": "OptiPlex 7010",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 220_000_000,
        "subitems": [
            ("Device", 1),
            ("RAM Upgrade", 1),
            ("SSD Upgrade", 1),
            ("Adapter", 1),
            ("Warranty", 1),
        ],
    },
    "MONITOR": {
        "name_en": "Monitor",
        "name_fa": "مانیتور",
        "company": "Dell",
        "model": "P2723D",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 120_000_000,
        "subitems": [],
    },
    "DOCK": {
        "name_en": "Docking Station",
        "name_fa": "داک استیشن",
        "company": "Lenovo",
        "model": "ThinkPad Universal Dock",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 35_000_000,
        "subitems": [],
    },
    "UPS": {
        "name_en": "UPS",
        "name_fa": "یوپی‌اس",
        "company": "APC",
        "model": "Smart-UPS 3000",
        "category": "End-User and Office IT",
        "unit": "unit",
        "family": "endpoint",
        "sales_irr": 250_000_000,
        "subitems": [
            ("Device", 1),
            ("Battery Pack", 1),
            ("Network Card", 1),
            ("Warranty", 1),
        ],
    },
}

SUPPLIERS: List[Dict[str, Any]] = [
    {
        "code": "SUP01",
        "name": f"{PREFIX}پردازش‌گران آتیه",
        "focus": ["server", "storage"],
        "positioning": "server and storage specialist",
        "strength": "enterprise hardware",
        "weakness": "longer delivery time",
        "lead_days": 45,
        "payment": "NET30",
        "reliability": Decimal("92.50"),
        "discount_profile": "balanced",
        "fx_sensitive": False,
        "capacity": "high",
        "city": "Tehran",
    },
    {
        "code": "SUP02",
        "name": f"{PREFIX}شبکه‌افزار سپهر",
        "focus": ["network"],
        "positioning": "network equipment specialist",
        "strength": "switches/routers/firewalls",
        "weakness": "license lead time",
        "lead_days": 35,
        "payment": "NET30",
        "reliability": Decimal("90.00"),
        "discount_profile": "license-heavy",
        "fx_sensitive": True,
        "capacity": "medium",
        "city": "Tehran",
    },
    {
        "code": "SUP03",
        "name": f"{PREFIX}داده‌پردازان رسا",
        "focus": ["server", "network", "endpoint", "storage", "security"],
        "positioning": "general IT supplier",
        "strength": "competitive price",
        "weakness": "limited warranty",
        "lead_days": 28,
        "payment": "CASH",
        "reliability": Decimal("84.00"),
        "discount_profile": "aggressive-price",
        "fx_sensitive": False,
        "capacity": "high",
        "city": "Isfahan",
    },
    {
        "code": "SUP04",
        "name": f"{PREFIX}ایمن‌سازان هوشمند",
        "focus": ["security"],
        "positioning": "security and monitoring",
        "strength": "CCTV/access control/security",
        "weakness": "partial stock",
        "lead_days": 25,
        "payment": "NET30",
        "reliability": Decimal("86.00"),
        "discount_profile": "partial-stock",
        "fx_sensitive": False,
        "capacity": "medium",
        "city": "Mashhad",
    },
    {
        "code": "SUP05",
        "name": f"{PREFIX}رایان‌گستر خاورمیانه",
        "focus": ["endpoint"],
        "positioning": "laptops and office IT",
        "strength": "fast delivery",
        "weakness": "higher price",
        "lead_days": 10,
        "payment": "CASH",
        "reliability": Decimal("96.00"),
        "discount_profile": "premium-fast",
        "fx_sensitive": False,
        "capacity": "high",
        "city": "Tehran",
    },
    {
        "code": "SUP06",
        "name": f"{PREFIX}فناوران ابری کوشا",
        "focus": ["server", "storage"],
        "positioning": "virtualization/cloud infrastructure",
        "strength": "licenses and implementation bundle",
        "weakness": "higher service cost",
        "lead_days": 40,
        "payment": "NET45",
        "reliability": Decimal("88.00"),
        "discount_profile": "bundle-service",
        "fx_sensitive": True,
        "capacity": "medium",
        "city": "Tehran",
    },
    {
        "code": "SUP07",
        "name": f"{PREFIX}نوآوران ذخیره‌سازی",
        "focus": ["storage"],
        "positioning": "storage/backup specialist",
        "strength": "backup and SAN/NAS",
        "weakness": "FX-sensitive pricing",
        "lead_days": 38,
        "payment": "LC30",
        "reliability": Decimal("89.00"),
        "discount_profile": "fx-linked",
        "fx_sensitive": True,
        "capacity": "medium",
        "city": "Shiraz",
    },
    {
        "code": "SUP08",
        "name": f"{PREFIX}راهکارهای مرکز داده کارا",
        "focus": ["server", "network", "storage"],
        "positioning": "datacenter integrated packages",
        "strength": "complete bundles",
        "weakness": "payment terms stricter",
        "lead_days": 32,
        "payment": "CASH",
        "reliability": Decimal("93.00"),
        "discount_profile": "full-bundle",
        "fx_sensitive": False,
        "capacity": "high",
        "city": "Tehran",
    },
    {
        "code": "SUP09",
        "name": f"{PREFIX}ارتباطات امن پارسیان",
        "focus": ["network", "security"],
        "positioning": "firewall/VPN/security appliance",
        "strength": "security support",
        "weakness": "license dependency",
        "lead_days": 30,
        "payment": "NET30",
        "reliability": Decimal("91.00"),
        "discount_profile": "support-premium",
        "fx_sensitive": True,
        "capacity": "medium",
        "city": "Tehran",
    },
    {
        "code": "SUP10",
        "name": f"{PREFIX}سامانه‌پرداز نگین",
        "focus": ["server", "network", "endpoint", "storage", "security"],
        "positioning": "mixed IT procurement",
        "strength": "flexible payment",
        "weakness": "medium delivery reliability",
        "lead_days": 22,
        "payment": "NET45",
        "reliability": Decimal("81.00"),
        "discount_profile": "flexible-payment",
        "fx_sensitive": False,
        "capacity": "medium",
        "city": "Karaj",
    },
    {
        "code": "SUP11",
        "name": f"{PREFIX}تجهیزات رایان مهر",
        "focus": ["endpoint"],
        "positioning": "endpoint and accessories",
        "strength": "low price",
        "weakness": "limited enterprise warranty",
        "lead_days": 18,
        "payment": "CASH",
        "reliability": Decimal("83.00"),
        "discount_profile": "low-price",
        "fx_sensitive": False,
        "capacity": "high",
        "city": "Tabriz",
    },
    {
        "code": "SUP12",
        "name": f"{PREFIX}زیرساخت هوشمند آریا",
        "focus": ["server", "network", "storage", "security"],
        "positioning": "project-based IT infrastructure",
        "strength": "balanced price/delivery/payment",
        "weakness": "limited stock on specialized components",
        "lead_days": 24,
        "payment": "NET30",
        "reliability": Decimal("87.00"),
        "discount_profile": "balanced",
        "fx_sensitive": False,
        "capacity": "medium",
        "city": "Tehran",
    },
]

PROJECTS: List[Dict[str, Any]] = [
    {"code": "PRJ01", "name": "Data Center Modernization", "priority": 10, "style": "urgent", "families": ["server", "storage", "network"], "count": 32},
    {"code": "PRJ02", "name": "Core Network Upgrade", "priority": 9, "style": "urgent", "families": ["network"], "count": 28},
    {"code": "PRJ03", "name": "Branch Office IT Refresh", "priority": 6, "style": "normal", "families": ["endpoint", "network"], "count": 30},
    {"code": "PRJ04", "name": "Security Monitoring Expansion", "priority": 8, "style": "urgent", "families": ["security", "network"], "count": 34},
    {"code": "PRJ05", "name": "Backup Infrastructure Upgrade", "priority": 7, "style": "budget", "families": ["storage", "server"], "count": 26},
    {"code": "PRJ06", "name": "Virtualization Cluster Expansion", "priority": 9, "style": "urgent", "families": ["server", "storage"], "count": 31},
    {"code": "PRJ07", "name": "Headquarters Endpoint Renewal", "priority": 5, "style": "normal", "families": ["endpoint"], "count": 29},
    {"code": "PRJ08", "name": "Disaster Recovery Site Preparation", "priority": 10, "style": "urgent", "families": ["server", "storage", "network"], "count": 33},
    {"code": "PRJ09", "name": "Access Control Modernization", "priority": 6, "style": "normal", "families": ["security"], "count": 27},
    {"code": "PRJ10", "name": "Monitoring Room Equipment Upgrade", "priority": 7, "style": "normal", "families": ["security", "endpoint"], "count": 30},
    {"code": "PRJ11", "name": "Firewall and VPN Renewal", "priority": 9, "style": "urgent", "families": ["network", "security"], "count": 32},
    {"code": "PRJ12", "name": "Storage Capacity Expansion", "priority": 6, "style": "budget", "families": ["storage"], "count": 28},
    {"code": "PRJ13", "name": "Server Room Standardization", "priority": 8, "style": "normal", "families": ["server", "network"], "count": 35},
    {"code": "PRJ14", "name": "Wireless Network Expansion", "priority": 5, "style": "budget", "families": ["network"], "count": 24},
    {"code": "PRJ15", "name": "IT Infrastructure for New Office", "priority": 7, "style": "normal", "families": ["endpoint", "network", "security"], "count": 31},
    {"code": "PRJ16", "name": "SOC Enablement Infrastructure", "priority": 9, "style": "urgent", "families": ["security", "server"], "count": 29},
    {"code": "PRJ17", "name": "Database Server Upgrade", "priority": 8, "style": "normal", "families": ["server", "storage"], "count": 30},
    {"code": "PRJ18", "name": "Application Server Expansion", "priority": 7, "style": "normal", "families": ["server"], "count": 33},
    {"code": "PRJ19", "name": "Video Surveillance Storage Upgrade", "priority": 6, "style": "budget", "families": ["security", "storage"], "count": 27},
    {"code": "PRJ20", "name": "Procurement Platform Hardware Refresh", "priority": 5, "style": "normal", "families": ["server", "endpoint"], "count": 28},
    {"code": "PRJ21", "name": "Helpdesk Endpoint Replacement", "priority": 4, "style": "budget", "families": ["endpoint"], "count": 32},
    {"code": "PRJ22", "name": "Network Segmentation Project", "priority": 8, "style": "urgent", "families": ["network", "security"], "count": 30},
    {"code": "PRJ23", "name": "High Availability Infrastructure", "priority": 10, "style": "urgent", "families": ["server", "storage", "network"], "count": 29},
    {"code": "PRJ24", "name": "Remote Work Security Project", "priority": 7, "style": "normal", "families": ["security", "endpoint"], "count": 31},
    {"code": "PRJ25", "name": "Edge Monitoring Infrastructure", "priority": 6, "style": "budget", "families": ["security", "network"], "count": 26},
    {"code": "PRJ26", "name": "IT Asset Lifecycle Renewal", "priority": 4, "style": "budget", "families": ["endpoint", "network"], "count": 34},
    {"code": "PRJ27", "name": "Financial Systems Server Upgrade", "priority": 9, "style": "urgent", "families": ["server", "storage"], "count": 28},
    {"code": "PRJ28", "name": "HR Systems Infrastructure Upgrade", "priority": 5, "style": "normal", "families": ["server", "endpoint"], "count": 30},
    {"code": "PRJ29", "name": "Executive Office IT Modernization", "priority": 6, "style": "normal", "families": ["endpoint"], "count": 32},
    {"code": "PRJ30", "name": "Enterprise Reporting Infrastructure", "priority": 7, "style": "budget", "families": ["server", "storage"], "count": 31},
]

PAYMENT_METHODS: List[Dict[str, Any]] = [
    {"code": "CASH", "name_en": "Cash / Immediate", "name_fa": "نقدی", "delay": 0},
    {"code": "NET30", "name_en": "Net 30", "name_fa": "۳۰ روزه", "delay": 30},
    {"code": "NET45", "name_en": "Net 45", "name_fa": "۴۵ روزه", "delay": 45},
    {"code": "LC30", "name_en": "Letter of Credit 30", "name_fa": "اعتبار اسنادی ۳۰ روزه", "delay": 30},
]

OPTION_VARIANTS: List[Dict[str, Any]] = [
    {"key": "low_price_slow", "cost_ratio": Decimal("0.72"), "lead_extra": 20, "payment": "CASH", "warranty": "12 months"},
    {"key": "high_price_fast", "cost_ratio": Decimal("0.88"), "lead_extra": -8, "payment": "CASH", "warranty": "24 months"},
    {"key": "better_payment", "cost_ratio": Decimal("0.80"), "lead_extra": 5, "payment": "NET45", "warranty": "18 months"},
    {"key": "strong_warranty", "cost_ratio": Decimal("0.84"), "lead_extra": 3, "payment": "NET30", "warranty": "36 months"},
    {"key": "fx_sensitive", "cost_ratio": Decimal("0.77"), "lead_extra": 10, "payment": "LC30", "warranty": "24 months"},
    {"key": "partial_stock", "cost_ratio": Decimal("0.75"), "lead_extra": 14, "payment": "NET30", "warranty": "12 months"},
]


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)


def _in(column, ids: Sequence[Any]):
    return column.in_(list(ids)) if ids else false()


def _date_in_range(index: int, span_days: int = 209) -> date:
    offset = index % max(span_days, 1)
    candidate = GREGORIAN_START + timedelta(days=offset)
    if candidate > GREGORIAN_END:
        return GREGORIAN_END
    return candidate


def _qty_for(family: str, index: int) -> int:
    if family == "endpoint":
        return [4, 8, 12, 16, 24, 6, 10, 20][index % 8]
    if family == "network":
        return [2, 4, 6, 8, 12, 3][index % 6]
    if family == "security":
        return [2, 4, 8, 16, 6, 10][index % 6]
    if family == "storage":
        return [1, 2, 3, 4, 2][index % 5]
    return [1, 2, 4, 3, 6, 2][index % 6]


def _catalog_keys_for(families: Sequence[str]) -> List[str]:
    keys = [key for key, spec in PRICING_ASSUMPTIONS.items() if spec["family"] in families]
    return keys or list(PRICING_ASSUMPTIONS.keys())


def _empty_counts() -> Dict[str, int]:
    return {
        "audit_logs": 0,
        "optimization_submissions": 0,
        "procurement_assignments": 0,
        "procurement_cost_components": 0,
        "procurement_options": 0,
        "delivery_options": 0,
        "package_subitems": 0,
        "procurement_packages": 0,
        "project_item_subitems": 0,
        "project_items": 0,
        "item_subitems": 0,
        "items_master": 0,
        "project_assignments": 0,
        "project_phases": 0,
        "projects": 0,
        "suppliers": 0,
        "payment_methods": 0,
        "budget_deleted": 0,
        "budget_restored": 0,
    }


async def _load_users(db: AsyncSession) -> Dict[str, Any]:
    users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()  # noqa: E712
    by_name = {user.username: user for user in users}
    pmo = by_name.get("pmo1") or by_name.get("admin") or next((u for u in users if u.role in {"pmo", "admin"}), None)
    admin = by_name.get("admin") or pmo
    pm = by_name.get("pm1") or next((u for u in users if u.role == "pm"), None)
    procurement_users = [u for u in users if u.role == "procurement"]
    if by_name.get("proc1") and by_name["proc1"] not in procurement_users:
        procurement_users.insert(0, by_name["proc1"])
    if not procurement_users and by_name.get("proc1"):
        procurement_users = [by_name["proc1"]]
    if not procurement_users:
        raise RuntimeError("No procurement user found. Expected at least proc1.")
    if pmo is None or admin is None:
        raise RuntimeError("No PMO/admin user found for finalization and assignment actor fields.")
    return {
        "pmo": pmo,
        "admin": admin,
        "pm": pm,
        "procurement_users": procurement_users,
        "proc_limitation": len(procurement_users) == 1,
    }


async def _commit_with_retry(db: AsyncSession, attempts: int = 3) -> None:
    last_error: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            await db.commit()
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.4 * attempt)
            try:
                await db.rollback()
            except Exception:
                pass
    if last_error is not None:
        raise last_error


async def _get_currency_id(db: AsyncSession) -> int:
    result = await db.execute(select(Currency).where(Currency.code == CURRENCY_CODE))
    currency = result.scalar_one_or_none()
    if currency is not None:
        return int(currency.id)
    currency = Currency(
        code=CURRENCY_CODE,
        name="Iranian Rial",
        symbol="﷼",
        is_base_currency=True,
        is_active=True,
        decimal_places=0,
    )
    db.add(currency)
    await db.flush()
    return int(currency.id)


async def cleanup_demo_dataset() -> Dict[str, int]:
    deleted = _empty_counts()
    demo_projects = select(Project.id).where(Project.project_code.like(f"{PREFIX}%"))
    demo_items = select(ProjectItem.id).where(
        ProjectItem.project_id.in_(demo_projects) | ProjectItem.item_code.like(f"{PREFIX}%")
    )
    demo_packages = select(ProcurementPackage.id).where(
        ProcurementPackage.project_item_id.in_(demo_items)
        | ProcurementPackage.package_name.like(f"{PREFIX}%")
    )
    demo_options = select(ProcurementOption.id).where(
        ProcurementOption.item_code.like(f"{PREFIX}%")
        | ProcurementOption.project_item_id.in_(demo_items)
        | ProcurementOption.package_id.in_(demo_packages)
    )
    demo_masters = select(ItemMaster.id).where(ItemMaster.item_code.like(f"{PREFIX}%"))

    async with AsyncSessionLocal() as db:
        snapshot_row = (
            await db.execute(
                select(AuditLog).where(
                    AuditLog.action == f"{PREFIX}BUDGET_SNAPSHOT",
                    AuditLog.entity_type == "demo_dataset",
                )
            )
        ).scalar_one_or_none()
        snapshot = (snapshot_row.details or {}) if snapshot_row else {}

        for key, stmt in [
            (
                "optimization_submissions",
                delete(OptimizationSubmission).where(
                    OptimizationSubmission.project_item_id.in_(demo_items)
                ),
            ),
            (
                "procurement_assignments",
                delete(ProcurementAssignment).where(
                    ProcurementAssignment.project_id.in_(demo_projects)
                    | ProcurementAssignment.project_item_id.in_(demo_items)
                ),
            ),
            (
                "procurement_cost_components",
                delete(ProcurementCostComponent).where(
                    ProcurementCostComponent.procurement_option_id.in_(demo_options)
                ),
            ),
            (
                "procurement_options",
                delete(ProcurementOption).where(ProcurementOption.id.in_(demo_options)),
            ),
            (
                "delivery_options",
                delete(DeliveryOption).where(
                    DeliveryOption.project_item_id.in_(demo_items)
                    | DeliveryOption.package_id.in_(demo_packages)
                ),
            ),
            (
                "package_subitems",
                delete(PackageSubItem).where(PackageSubItem.package_id.in_(demo_packages)),
            ),
            (
                "procurement_packages",
                delete(ProcurementPackage).where(ProcurementPackage.id.in_(demo_packages)),
            ),
            (
                "project_item_subitems",
                delete(ProjectItemSubItem).where(
                    ProjectItemSubItem.project_item_id.in_(demo_items)
                ),
            ),
            (
                "project_items",
                delete(ProjectItem).where(ProjectItem.id.in_(demo_items)),
            ),
            (
                "item_subitems",
                delete(ItemSubItem).where(
                    ItemSubItem.item_master_id.in_(demo_masters)
                    | ItemSubItem.part_number.like(f"{PREFIX}%")
                ),
            ),
            (
                "items_master",
                delete(ItemMaster).where(ItemMaster.item_code.like(f"{PREFIX}%")),
            ),
            (
                "project_assignments",
                delete(ProjectAssignment).where(ProjectAssignment.project_id.in_(demo_projects)),
            ),
            (
                "project_phases",
                delete(ProjectPhase).where(ProjectPhase.project_id.in_(demo_projects)),
            ),
            (
                "projects",
                delete(Project).where(Project.project_code.like(f"{PREFIX}%")),
            ),
            (
                "suppliers",
                delete(Supplier).where(Supplier.supplier_id.like(f"{PREFIX}%")),
            ),
            (
                "payment_methods",
                delete(PaymentMethod).where(PaymentMethod.code.like(f"{PREFIX}%")),
            ),
        ]:
            result = await db.execute(stmt)
            deleted[key] = int(result.rowcount or 0)
            await _commit_with_retry(db)

        for entry in snapshot.get("budgets", []):
            budget_date = date.fromisoformat(entry["budget_date"])
            created = bool(entry.get("created"))
            original = entry.get("original_available_budget")
            row = (
                await db.execute(select(BudgetData).where(BudgetData.budget_date == budget_date))
            ).scalar_one_or_none()
            if row is None:
                continue
            if created:
                await db.delete(row)
                deleted["budget_deleted"] += 1
            elif original is not None:
                row.available_budget = _money(original)
                deleted["budget_restored"] += 1
        await _commit_with_retry(db)

        result = await db.execute(
            delete(AuditLog).where(
                (AuditLog.action.like(f"{PREFIX}%")) | (AuditLog.entity_type == "demo_dataset")
            )
        )
        deleted["audit_logs"] = int(result.rowcount or 0)
        await _commit_with_retry(db)
    return deleted


async def verify_demo_dataset() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        project_ids = (
            await db.execute(select(Project.id).where(Project.project_code.like(f"{PREFIX}%")))
        ).scalars().all()
        project_item_ids = (
            await db.execute(
                select(ProjectItem.id).where(
                    _in(ProjectItem.project_id, project_ids) | ProjectItem.item_code.like(f"{PREFIX}%")
                )
            )
        ).scalars().all()
        item_master_ids = (
            await db.execute(select(ItemMaster.id).where(ItemMaster.item_code.like(f"{PREFIX}%")))
        ).scalars().all()
        supplier_ids = (
            await db.execute(select(Supplier.id).where(Supplier.supplier_id.like(f"{PREFIX}%")))
        ).scalars().all()
        package_ids = (
            await db.execute(
                select(ProcurementPackage.id).where(
                    _in(ProcurementPackage.project_item_id, project_item_ids)
                    | ProcurementPackage.package_name.like(f"{PREFIX}%")
                )
            )
        ).scalars().all()
        option_ids = (
            await db.execute(
                select(ProcurementOption.id).where(
                    _in(ProcurementOption.project_item_id, project_item_ids)
                    | ProcurementOption.item_code.like(f"{PREFIX}%")
                )
            )
        ).scalars().all()

        finalized_ids = (
            await db.execute(
                select(ProjectItem.id).where(
                    _in(ProjectItem.id, project_item_ids),
                    ProjectItem.is_finalized == True,  # noqa: E712
                )
            )
        ).scalars().all()
        assigned_item_ids = set(
            (
                await db.execute(
                    select(ProcurementAssignment.project_item_id).where(
                        _in(ProcurementAssignment.project_item_id, finalized_ids),
                        ProcurementAssignment.status == "active",
                    )
                )
            ).scalars().all()
        )
        option_item_ids = set(
            (
                await db.execute(
                    select(ProcurementOption.project_item_id).where(_in(ProcurementOption.id, option_ids))
                )
            ).scalars().all()
        )
        opt_ready_ids = set(
            (
                await db.execute(
                    select(ProcurementOption.project_item_id).where(
                        _in(ProcurementOption.id, option_ids),
                        ProcurementOption.is_finalized == True,  # noqa: E712
                    )
                )
            ).scalars().all()
        )
        submitted_ids = (
            await db.execute(
                select(OptimizationSubmission.project_item_id).where(
                    _in(OptimizationSubmission.project_item_id, project_item_ids),
                    OptimizationSubmission.status == "SENT",
                )
            )
        ).scalars().all()
        subitem_count = (
            await db.execute(
                select(ItemSubItem.id).where(
                    _in(ItemSubItem.item_master_id, item_master_ids) | ItemSubItem.part_number.like(f"{PREFIX}%")
                )
            )
        ).scalars().all()
        package_sub_count = (
            await db.execute(select(PackageSubItem.id).where(_in(PackageSubItem.package_id, package_ids)))
        ).scalars().all()
        budget_dates = [month_date for _, month_date in JALALI_MONTH_STARTS]
        budget_rows = (
            await db.execute(select(BudgetData).where(_in(BudgetData.budget_date, budget_dates)))
        ).scalars().all()
        shortage = next((row for row in budget_rows if row.budget_date == SHORTAGE_BUDGET_DATE), None)
        rc8 = (
            await db.execute(select(Project.id).where(Project.project_code.like("DEMO_RC8_%")))
        ).scalars().all()
        ph5 = (
            await db.execute(select(Project.id).where(Project.project_code.like("PH5%")))
        ).scalars().all()

        return {
            "prefix": PREFIX,
            "date_range_jalali": f"{JALALI_START} to {JALALI_END}",
            "date_range_gregorian": f"{GREGORIAN_START.isoformat()} to {GREGORIAN_END.isoformat()}",
            "currency_unit_convention": CURRENCY_UNIT,
            "master_items": len(item_master_ids),
            "sub_items": len(subitem_count),
            "suppliers": len(supplier_ids),
            "projects": len(project_ids),
            "project_items": len(project_item_ids),
            "finalized_project_items": len(finalized_ids),
            "procurement_assignments": len([i for i in assigned_item_ids if i]),
            "items_with_supplier_options": len([i for i in option_item_ids if i]),
            "supplier_options": len(option_ids),
            "packages": len(package_ids),
            "package_sub_items": len(package_sub_count),
            "budget_records": len(budget_rows),
            "shortage_window_created": bool(shortage),
            "shortage_window": SHORTAGE_MONTH_JALALI if shortage else None,
            "optimization_ready": len([i for i in opt_ready_ids if i]),
            "optimization_submissions": len(submitted_ids),
            "cleanup_supported": True,
            "no_demo_rc8_dependency": True,
            "no_ph5_dependency": True,
            "unrelated_demo_rc8_projects_present": len(rc8),
            "unrelated_ph5_projects_present": len(ph5),
        }


async def create_demo_dataset(*, skip_pre_clean: bool = False) -> Dict[str, Any]:
    cleanup_summary = {} if skip_pre_clean else await cleanup_demo_dataset()
    async with AsyncSessionLocal() as db:
        users = await _load_users(db)
        pmo = users["pmo"]
        admin = users["admin"]
        pm_user = users["pm"]
        proc_users = users["procurement_users"]
        currency_id = await _get_currency_id(db)
        now = datetime.now(timezone.utc)

        payment_methods: Dict[str, PaymentMethod] = {}
        for spec in PAYMENT_METHODS:
            method = PaymentMethod(
                code=f"{PREFIX}{spec['code']}",
                name_en=f"{PREFIX}{spec['name_en']}",
                name_fa=f"{PREFIX}{spec['name_fa']}",
                description=f"{PREFIX} demo payment method for IT 1405 scenario",
                settlement_delay_days=spec["delay"],
                is_active=True,
            )
            db.add(method)
            payment_methods[spec["code"]] = method
        await db.flush()

        suppliers: Dict[str, Supplier] = {}
        for spec in SUPPLIERS:
            supplier = Supplier(
                supplier_id=f"{PREFIX}{spec['code']}",
                company_name=spec["name"],
                legal_entity_type="LLC",
                country="Iran",
                city=spec["city"],
                category="IT Equipment",
                industry="Information Technology",
                product_service_lines=spec["focus"],
                payment_terms=spec["payment"],
                currency_preference=CURRENCY_CODE,
                average_lead_time_days=spec["lead_days"],
                delivery_accuracy_percent=spec["reliability"],
                warranty_policy=spec["strength"],
                after_sales_policy=spec["weakness"],
                status="ACTIVE",
                risk_level="LOW" if spec["reliability"] >= Decimal("90") else "MEDIUM",
                compliance_status="APPROVED",
                internal_rating=Decimal("4.20") if spec["reliability"] >= Decimal("90") else Decimal("3.60"),
                performance_metrics={
                    "positioning": spec["positioning"],
                    "strength": spec["strength"],
                    "weakness": spec["weakness"],
                    "discount_profile": spec["discount_profile"],
                    "fx_sensitive": spec["fx_sensitive"],
                    "supply_capacity": spec["capacity"],
                    "delivery_reliability": str(spec["reliability"]),
                },
                notes=(
                    f"{PREFIX} {spec['positioning']}. Strength: {spec['strength']}. "
                    f"Weakness: {spec['weakness']}."
                ),
                created_by_id=admin.id,
            )
            db.add(supplier)
            suppliers[spec["code"]] = supplier
        await _commit_with_retry(db)

        masters: Dict[str, ItemMaster] = {}
        master_subitems: Dict[str, List[ItemSubItem]] = {}
        for key, spec in PRICING_ASSUMPTIONS.items():
            master = ItemMaster(
                item_code=f"{PREFIX}{key}",
                company=spec["company"],
                item_name=spec["name_en"],
                model=spec["model"],
                part_number=f"{PREFIX}PN_{key}",
                category=spec["category"],
                unit=spec["unit"],
                description=(
                    f"{PREFIX}{spec['name_fa']} | demo sales assumption "
                    f"{spec['sales_irr']} IRR ({spec['sales_irr'] // 10} Toman)"
                ),
                specifications={
                    "family": spec["family"],
                    "sales_price_irr": spec["sales_irr"],
                    "currency": CURRENCY_CODE,
                    "pricing_source": "demo_assumption_not_official_quote",
                },
                is_active=True,
                created_by_id=admin.id,
            )
            db.add(master)
            masters[key] = master
        await db.flush()

        for key, spec in PRICING_ASSUMPTIONS.items():
            created_subs: List[ItemSubItem] = []
            for name, _qty in spec["subitems"]:
                slug = name.upper().replace(" ", "_")
                sub = ItemSubItem(
                    item_master_id=masters[key].id,
                    name=name,
                    description=f"{PREFIX}{spec['name_en']} / {name}",
                    part_number=f"{PREFIX}{key}_{slug}",
                )
                db.add(sub)
                created_subs.append(sub)
            master_subitems[key] = created_subs
        await _commit_with_retry(db)

        projects: List[Project] = []
        for spec in PROJECTS:
            budget_amount = _money(18_000_000_000 if spec["style"] == "budget" else 32_000_000_000)
            if spec["style"] == "urgent":
                budget_amount = _money(40_000_000_000)
            project = Project(
                project_code=f"{PREFIX}{spec['code']}",
                name=f"{PREFIX}{spec['name']}",
                priority_weight=spec["priority"],
                budget_amount=budget_amount,
                budget_currency=CURRENCY_CODE,
                is_active=True,
            )
            db.add(project)
            projects.append(project)
        await db.flush()

        if pm_user is not None:
            for project in projects:
                db.add(ProjectAssignment(user_id=pm_user.id, project_id=project.id))
        for project in projects:
            db.add(
                ProjectPhase(
                    project_id=project.id,
                    phase_name=f"{PREFIX}1405 Procurement Window",
                    start_date=GREGORIAN_START,
                    end_date=GREGORIAN_END,
                )
            )
        await _commit_with_retry(db)

        created_items: List[Dict[str, Any]] = []
        global_index = 0
        for project, spec in zip(projects, PROJECTS):
            catalog_keys = _catalog_keys_for(spec["families"])
            for item_idx in range(spec["count"]):
                key = catalog_keys[item_idx % len(catalog_keys)]
                catalog = PRICING_ASSUMPTIONS[key]
                qty = _qty_for(catalog["family"], item_idx + spec["priority"])
                requested = _date_in_range(global_index + spec["priority"] * 3)
                supply_by = min(requested + timedelta(days=21 + (item_idx % 25)), GREGORIAN_END)
                item_code = f"{PREFIX}{spec['code']}_I{item_idx + 1:02d}_{key}"[:50]
                item = ProjectItem(
                    project_id=project.id,
                    master_item_id=masters[key].id,
                    item_code=item_code,
                    item_name=catalog["name_en"],
                    quantity=qty,
                    delivery_options=[requested.isoformat(), supply_by.isoformat()],
                    status=ProjectItemStatus.PENDING,
                    description=(
                        f"{PREFIX}{catalog['name_fa']} for {spec['name']} "
                        f"| Jalali window {JALALI_START} to {JALALI_END}"
                    ),
                    is_finalized=False,
                )
                db.add(item)
                created_items.append(
                    {
                        "item": item,
                        "key": key,
                        "qty": qty,
                        "requested": requested,
                        "supply_by": supply_by,
                        "project": project,
                        "global_index": global_index,
                        "catalog": catalog,
                    }
                )
                global_index += 1
        await db.flush()

        item_sub_rels: Dict[int, List[ProjectItemSubItem]] = {}
        for row in created_items:
            rels: List[ProjectItemSubItem] = []
            for sub, (_name, unit_qty) in zip(master_subitems[row["key"]], row["catalog"]["subitems"]):
                rel = ProjectItemSubItem(
                    project_item_id=row["item"].id,
                    item_subitem_id=sub.id,
                    quantity=int(unit_qty) * int(row["qty"]),
                )
                db.add(rel)
                rels.append(rel)
            item_sub_rels[row["item"].id] = rels
        await db.flush()

        for row in created_items:
            sales_unit = _money(row["catalog"]["sales_irr"])
            delivery = DeliveryOption(
                project_item_id=row["item"].id,
                delivery_date=row["supply_by"],
                invoice_timing_type="RELATIVE",
                invoice_days_after_delivery=30,
                invoice_amount_per_unit=sales_unit,
                preference_rank=1,
                notes=f"{PREFIX} sales price assumption {sales_unit} IRR/unit",
                is_active=True,
            )
            db.add(delivery)
            row["delivery"] = delivery
        await _commit_with_retry(db)

        finalized_rows = [row for row in created_items if row["global_index"] % 10 < 3]
        for row in finalized_rows:
            item = row["item"]
            item.is_finalized = True
            item.finalized_by = pmo.id
            item.finalized_at = now
            item.status = ProjectItemStatus.SUGGESTED
            item.procurement_date = row["requested"]
        await db.flush()

        assignment_count = 0
        for idx, row in enumerate(finalized_rows):
            assignee = proc_users[idx % len(proc_users)]
            db.add(
                ProcurementAssignment(
                    project_id=row["project"].id,
                    project_item_id=row["item"].id,
                    assignee_user_id=assignee.id,
                    assigned_by_user_id=pmo.id,
                    status="active",
                    assignment_scope="project_item",
                    note=f"{PREFIX} assigned to {assignee.username} for 1405 IT procurement",
                )
            )
            assignment_count += 1
            if assignment_count % 40 == 0:
                await _commit_with_retry(db)
        await _commit_with_retry(db)

        optioned_rows = [row for i, row in enumerate(finalized_rows) if i % 5 != 4]
        package_count = 0
        package_sub_count = 0
        option_count = 0
        component_count = 0
        optimization_ready = 0
        submitted = 0
        contract_applied = 0
        option_ids_for_contract: List[int] = []

        for row_idx, row in enumerate(optioned_rows):
            family = row["catalog"]["family"]
            matching = [spec for spec in SUPPLIERS if family in spec["focus"]]
            if len(matching) < 2:
                matching = SUPPLIERS[:]
            variant_count = 2 + (row_idx % 3)  # 2..4
            rels = item_sub_rels[row["item"].id]
            sales_total = _money(row["catalog"]["sales_irr"]) * row["qty"]
            pending_packages: List[Dict[str, Any]] = []

            for variant_idx in range(variant_count):
                variant = OPTION_VARIANTS[variant_idx % len(OPTION_VARIANTS)]
                supplier_spec = matching[(row_idx + variant_idx) % len(matching)]
                supplier = suppliers[supplier_spec["code"]]
                is_decomposed = bool(rels)
                package_type = "FULL"
                covered_rels = rels
                incomplete = False
                if is_decomposed:
                    if variant["key"] == "partial_stock" and len(rels) >= 3:
                        package_type = "PARTIAL"
                        covered_rels = rels[: max(1, len(rels) // 3)]
                        incomplete = True
                    elif variant["key"] in {"better_payment", "fx_sensitive"} and len(rels) >= 4:
                        package_type = "PARTIAL"
                        half = (len(rels) + 1) // 2
                        covered_rels = rels[:half] if variant_idx % 2 == 0 else rels[half:]
                    else:
                        package_type = "FULL"
                        covered_rels = rels

                package = ProcurementPackage(
                    project_item_id=row["item"].id,
                    package_name=f"{PREFIX}{row['item'].item_code}_{variant['key']}"[:200],
                    package_type=package_type,
                    supplier_id=supplier.id,
                    description=(
                        f"{PREFIX}{variant['key']} package from {supplier.company_name}"
                    ),
                    is_active=True,
                    main_item_quantity=row["qty"] if package_type == "FULL" else max(1, row["qty"] // 2),
                    created_by_id=proc_users[row_idx % len(proc_users)].id,
                )
                db.add(package)
                pending_packages.append(
                    {
                        "package": package,
                        "variant": variant,
                        "supplier_spec": supplier_spec,
                        "supplier": supplier,
                        "package_type": package_type,
                        "covered_rels": covered_rels,
                        "incomplete": incomplete,
                    }
                )
            await db.flush()
            package_count += len(pending_packages)

            created_options: List[ProcurementOption] = []
            pending_components: List[Tuple[ProcurementOption, List[Tuple[str, Decimal, str]], str]] = []
            for pending in pending_packages:
                package = pending["package"]
                variant = pending["variant"]
                supplier_spec = pending["supplier_spec"]
                supplier = pending["supplier"]
                package_type = pending["package_type"]
                covered_rels = pending["covered_rels"]
                incomplete = pending["incomplete"]

                for rel in covered_rels:
                    covered = int(rel.quantity or 0)
                    if incomplete:
                        covered = max(1, covered // 2)
                    percent = Decimal("0")
                    if rel.quantity:
                        raw_percent = (Decimal(covered) * Decimal("100")) / Decimal(rel.quantity)
                        percent = _money(raw_percent if raw_percent < Decimal("100") else Decimal("100"))
                    db.add(
                        PackageSubItem(
                            package_id=package.id,
                            project_item_subitem_id=rel.id,
                            quantity_covered=covered,
                            is_fully_covered=covered >= int(rel.quantity or 0),
                            coverage_percentage=percent,
                        )
                    )
                    package_sub_count += 1

                lead = max(7, int(supplier_spec["lead_days"]) + int(variant["lead_extra"]))
                delivery_date = min(row["requested"] + timedelta(days=lead), GREGORIAN_END)
                payment_code = variant["payment"]
                payment_method = payment_methods[payment_code]
                payment_date = row["requested"] + timedelta(days=3 if payment_code == "CASH" else 10)
                cost_total = _money(sales_total * variant["cost_ratio"])
                if package_type != "FULL":
                    cost_total = _money(cost_total * Decimal("0.55"))
                base_price = _money(cost_total * Decimal("0.86"))
                shipping = _money(cost_total * Decimal("0.04"))
                vat = _money(cost_total * Decimal("0.08"))
                extras = _money(cost_total - base_price - shipping - vat)
                if extras <= 0:
                    extras = _money("100000")
                    base_price = _money(cost_total - shipping - vat - extras)

                option = ProcurementOption(
                    package_id=package.id,
                    project_item_id=row["item"].id,
                    item_code=row["item"].item_code,
                    supplier_name=supplier.company_name,
                    supplier_id=supplier.id,
                    cost_amount=cost_total,
                    cost_currency=CURRENCY_CODE,
                    shipping_cost=shipping,
                    payment_method_id=payment_method.id,
                    planned_supplier_payment_date=payment_date,
                    supplier_effective_receipt_date=payment_date
                    + timedelta(days=payment_method.settlement_delay_days),
                    base_cost=base_price,
                    currency_id=currency_id,
                    lomc_lead_time=lead,
                    purchase_date=row["requested"],
                    expected_delivery_date=delivery_date,
                    delivery_option_id=row["delivery"].id,
                    project_requested_delivery_date=row["supply_by"],
                    supplier_actual_delivery_date=delivery_date,
                    selected_delivery_date=delivery_date,
                    delivery_date_source="SUPPLIER_ACTUAL",
                    delivery_date_variance_days=(delivery_date - row["supply_by"]).days,
                    forecast_customer_invoice_date=delivery_date + timedelta(days=30),
                    forecast_customer_invoice_date_source="SYSTEM_DEFAULT",
                    forecast_customer_receipt_date=delivery_date + timedelta(days=60),
                    forecast_customer_receipt_date_source="SYSTEM_DEFAULT",
                    forecast_customer_receipt_delay_days=30,
                    date_calculation_trace=[
                        f"{PREFIX} populated using persistence-contract equivalent mapping",
                        f"variant={variant['key']}",
                        f"warranty={variant['warranty']}",
                        f"payment_method={payment_code}",
                        f"fx_sensitive={bool(supplier_spec['fx_sensitive'] or variant['key'] == 'fx_sensitive')}",
                        f"sales_total_irr={sales_total}",
                        f"margin_vs_sales={_money((sales_total - cost_total) / sales_total * 100)}",
                        f"fx_assumption_usd_irr={FX_USD_IRR}",
                    ],
                    payment_terms=(
                        {"type": "cash", "discount_percent": 2}
                        if payment_code == "CASH"
                        else {
                            "type": "installments",
                            "schedule": (
                                [
                                    {"percent": 30, "due_offset": 0},
                                    {"percent": 70, "due_offset": 45},
                                ]
                                if payment_code == "NET45"
                                else [
                                    {"percent": 40, "due_offset": 0},
                                    {"percent": 60, "due_offset": 30},
                                ]
                            ),
                        }
                    ),
                    is_active=True,
                    is_finalized=not incomplete,
                )
                db.add(option)
                created_options.append(option)
                extra_type = "CUSTOMS" if variant["key"] == "fx_sensitive" else "OTHER"
                pending_components.append(
                    (
                        option,
                        [
                            ("BASE_PRICE", base_price, "SUPPLIER"),
                            ("SHIPPING", shipping, "LOGISTICS_PROVIDER"),
                            ("VAT", vat, "SUPPLIER"),
                            (
                                extra_type,
                                extras,
                                "CUSTOMS_OR_CLEARANCE" if extra_type == "CUSTOMS" else "OTHER",
                            ),
                        ],
                        variant["key"],
                    )
                )
            await db.flush()
            option_count += len(created_options)

            for option, components, variant_key in pending_components:
                for component_type, amount, payee in components:
                    db.add(
                        ProcurementCostComponent(
                            procurement_option_id=option.id,
                            component_type=component_type,
                            description=f"{PREFIX}{component_type} for {variant_key}",
                            amount_value=amount,
                            amount_currency=CURRENCY_CODE,
                            amount_irr=amount,
                            exchange_rate_date=row["requested"],
                            payment_metadata={
                                "inherit_option_payment_schedule": True,
                                "payee_type": payee,
                                "payment_type": "CASH",
                            },
                            is_active=True,
                        )
                    )
                    component_count += 1
                if len(option_ids_for_contract) < CONTRACT_SAMPLE_LIMIT and option.is_finalized:
                    option_ids_for_contract.append(option.id)

            ready_options = [opt for opt in created_options if opt.is_finalized]
            if len(ready_options) >= 2:
                optimization_ready += 1
                if row_idx % 2 == 0:
                    db.add(
                        OptimizationSubmission(
                            project_item_id=row["item"].id,
                            status="SENT",
                            partial_coverage_acknowledged=any(
                                "variant=partial_stock" in (opt.date_calculation_trace or [])
                                for opt in created_options
                            ),
                            submitted_by_id=proc_users[row_idx % len(proc_users)].id,
                            notes=f"{PREFIX} ready for optimization comparison, decisions not locked",
                            summary_payload={
                                "prefix": PREFIX,
                                "option_ids": [opt.id for opt in ready_options],
                                "sales_total_irr": str(sales_total),
                            },
                        )
                    )
                    submitted += 1
            if row_idx > 0 and row_idx % 15 == 0:
                await _commit_with_retry(db)

        await _commit_with_retry(db)
        for option_id in option_ids_for_contract:
            await apply_procurement_option_persistence_contract(option_id=option_id, db=db)
            contract_applied += 1
        await _commit_with_retry(db)

        budget_snapshot: List[Dict[str, Any]] = []
        normal_budget = _money("500000000000")
        shortage_budget = _money("80000000000")
        for month_name, month_date in JALALI_MONTH_STARTS:
            existing = (
                await db.execute(select(BudgetData).where(BudgetData.budget_date == month_date))
            ).scalar_one_or_none()
            amount = shortage_budget if month_date == SHORTAGE_BUDGET_DATE else normal_budget
            if existing is None:
                db.add(
                    BudgetData(
                        budget_date=month_date,
                        available_budget=amount,
                        multi_currency_budget={CURRENCY_CODE: float(amount)},
                    )
                )
                budget_snapshot.append(
                    {
                        "budget_date": month_date.isoformat(),
                        "jalali_month": month_name,
                        "created": True,
                        "increment": str(amount),
                    }
                )
            else:
                original = _money(existing.available_budget)
                existing.available_budget = _money(original + amount)
                existing.multi_currency_budget = {
                    **(existing.multi_currency_budget or {}),
                    CURRENCY_CODE: float(_money(existing.available_budget)),
                    f"{PREFIX}increment": float(amount),
                }
                budget_snapshot.append(
                    {
                        "budget_date": month_date.isoformat(),
                        "jalali_month": month_name,
                        "created": False,
                        "original_available_budget": str(original),
                        "increment": str(amount),
                    }
                )

        db.add(
            AuditLog(
                user_id=admin.id,
                action=f"{PREFIX}BUDGET_SNAPSHOT",
                entity_type="demo_dataset",
                details={
                    "prefix": PREFIX,
                    "currency": CURRENCY_CODE,
                    "budgets": budget_snapshot,
                    "shortage_window": SHORTAGE_MONTH_JALALI,
                },
            )
        )
        db.add(
            AuditLog(
                user_id=admin.id,
                action=f"{PREFIX}CREATED",
                entity_type="demo_dataset",
                details={
                    "prefix": PREFIX,
                    "projects": len(projects),
                    "project_items": len(created_items),
                    "finalized": len(finalized_rows),
                    "assignments": assignment_count,
                    "items_with_options": len(optioned_rows),
                    "options": option_count,
                    "packages": package_count,
                },
            )
        )
        await _commit_with_retry(db)

        summary = await verify_demo_dataset()
        summary.update(
            {
                "mode": "create",
                "cleanup_before_create": cleanup_summary,
                "procurement_users": [user.username for user in proc_users],
                "procurement_user_limitation": users["proc_limitation"],
                "persistence_contract_sample": contract_applied,
                "cost_components": component_count,
                "optimization_submissions_created": submitted,
                "pricing_source": "demo_assumption_not_official_quote",
                "fx_usd_irr_assumption": str(FX_USD_IRR),
                "direct_orm_reason": (
                    "No bulk seed API exists; ORM writes use the same models/fields as "
                    "finalization, assignment, package, and procurement-option services."
                ),
            }
        )
        return summary


async def main(mode: str, skip_pre_clean: bool = False) -> Dict[str, Any]:
    if mode == "cleanup":
        return {"mode": "cleanup", "cleanup_supported": True, "cleanup_removed": await cleanup_demo_dataset()}
    if mode == "verify":
        result = await verify_demo_dataset()
        result["mode"] = "verify"
        return result
    if mode == "create":
        return await create_demo_dataset(skip_pre_clean=skip_pre_clean)
    raise ValueError(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/cleanup/verify DEMO_IT_1405 IT procurement dataset")
    parser.add_argument("--mode", choices=["create", "cleanup", "verify"], required=True)
    parser.add_argument(
        "--skip-pre-clean",
        action="store_true",
        help="Skip prefix cleanup before create. Use only on an empty DEMO_IT_1405_ dataset.",
    )
    args = parser.parse_args()
    print(json.dumps(asyncio.run(main(args.mode, args.skip_pre_clean)), indent=2, default=str))
