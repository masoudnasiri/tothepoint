"""
Phase 12 - Post-redesign UAT dataset generator (UAT1405_).

Usage:
  python scripts/create_uat_1405_dataset.py --mode plan
  python scripts/create_uat_1405_dataset.py --mode reset-domain-data
  python scripts/create_uat_1405_dataset.py --mode create
  python scripts/create_uat_1405_dataset.py --mode validate
  python scripts/create_uat_1405_dataset.py --mode cleanup
  python scripts/create_uat_1405_dataset.py --mode reset-and-create

Design notes:
- Creation uses backend schemas/crud/service validation paths where available.
- No ad-hoc raw INSERT SQL is used.
- Reset cleanup preserves users/auth records.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import and_, delete, func, or_, select

from app.database import AsyncSessionLocal
from app.crud import (
    create_budget_data,
    create_delivery_option,
    create_procurement_option,
    create_project,
    create_project_item,
    finalize_project_item,
)
import app.models_invoice_payment  # noqa: F401  keep model registry loaded
from app.models import (
    AuditLog,
    BudgetData,
    CashflowEvent,
    Currency,
    DeliveryOption,
    ExchangeRate,
    FinalizedDecision,
    ItemMaster,
    ItemSubItem,
    OptimizationResult,
    OptimizationRun,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectAssignment,
    ProjectItem,
    ProjectItemStatus,
    ProjectItemSubItem,
    ProjectPhase,
    Supplier,
    SupplierContact,
    SupplierDocument,
    SupplierPayment,
    User,
)
from app.models_invoice_payment import Invoice, Payment
from app.schemas import (
    BudgetDataCreate,
    DeliveryOptionCreate,
    ProcurementOptionCreate,
    ProjectCreate,
    ProjectItemCreate,
    ProjectItemFinalize,
)
from app.services.package_service import (
    calculate_coverage_summary,
    validate_and_compute_subitem_coverage,
    validate_main_item_quantity,
)

PREFIX = "UAT1405_"
SCRIPT_ACTION = f"{PREFIX}DATASET_GENERATOR"

# Reduce noisy Phase 3 audit logging when migration audit table is absent.
logging.getLogger("app.services.audit_service").setLevel(logging.CRITICAL)

TARGET_MASTER_ITEMS = 100
TARGET_PROJECTS = 10
TARGET_PROJECT_ITEMS_PER_PROJECT = 50
TARGET_PROJECT_ITEMS = TARGET_PROJECTS * TARGET_PROJECT_ITEMS_PER_PROJECT
TARGET_FINALIZED_RATIO = Decimal("0.70")
TARGET_PROCUREMENT_RATIO_ON_FINALIZED = Decimal("0.70")

JALALI_MONTHS_1405: List[Tuple[int, str]] = [
    (4, "Tir 1405"),
    (5, "Mordad 1405"),
    (6, "Shahrivar 1405"),
    (7, "Mehr 1405"),
    (8, "Aban 1405"),
    (9, "Azar 1405"),
    (10, "Dey 1405"),
    (11, "Bahman 1405"),
    (12, "Esfand 1405"),
]


@dataclass
class MasterRecord:
    id: int
    item_code: str
    item_name: str
    category: str
    unit: str
    base_sales_price_irr: Decimal
    subitem_rules: List[Dict[str, Any]]


@dataclass
class ProjectItemRecord:
    id: int
    project_id: int
    item_code: str
    requested_date: date
    quantity: int
    sales_unit_price_irr: Decimal


def _q(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_item_code(company: str, item_name: str, model: str = "") -> str:
    company_clean = re.sub(r"[^A-Z0-9]+", "", company.upper())
    name_clean = re.sub(r"[^A-Z0-9\s]+", "", item_name.upper())
    name_clean = re.sub(r"\s+", "-", name_clean.strip())
    model_clean = re.sub(r"[^A-Z0-9]+", "", model.upper()) if model else ""
    code = f"{company_clean}-{name_clean}-{model_clean}" if model_clean else f"{company_clean}-{name_clean}"
    code = re.sub(r"-+", "-", code)
    return code[:100]


# Reliable Jalali->Gregorian conversion based on the proven jalaali algorithm.
def jalali_to_gregorian(jy: int, jm: int, jd: int) -> date:
    jy -= 979
    jm -= 1
    jd -= 1

    j_days = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    j_day_no = 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4
    for i in range(jm):
        j_day_no += j_days[i]
    j_day_no += jd

    g_day_no = j_day_no + 79
    gy = 1600 + 400 * (g_day_no // 146097)
    g_day_no %= 146097

    leap = True
    if g_day_no >= 36525:
        g_day_no -= 1
        gy += 100 * (g_day_no // 36524)
        g_day_no %= 36524
        if g_day_no >= 365:
            g_day_no += 1
        else:
            leap = False

    gy += 4 * (g_day_no // 1461)
    g_day_no %= 1461

    if g_day_no >= 366:
        leap = False
        g_day_no -= 1
        gy += g_day_no // 365
        g_day_no %= 365

    gd = g_day_no + 1
    g_days = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    while gm <= 12 and gd > g_days[gm]:
        gd -= g_days[gm]
        gm += 1

    return date(gy, gm, gd)


def jalali_month_boundaries_1405() -> List[Dict[str, Any]]:
    boundaries: List[Dict[str, Any]] = []
    for month, label in JALALI_MONTHS_1405:
        start_g = jalali_to_gregorian(1405, month, 1)
        if month < 12:
            end_g = jalali_to_gregorian(1405, month + 1, 1) - timedelta(days=1)
        else:
            end_g = jalali_to_gregorian(1406, 1, 1) - timedelta(days=1)
        boundaries.append(
            {
                "jalali_month": label,
                "jalali_month_number": month,
                "gregorian_start": start_g.isoformat(),
                "gregorian_end": end_g.isoformat(),
            }
        )
    return boundaries


def _catalog_blueprints() -> List[Dict[str, Any]]:
    category_items: Dict[str, List[str]] = {
        "Data Center Infrastructure": [
            "Rackmount Server Node",
            "Blade Server Chassis",
            "SAN Storage Array",
            "NVMe Flash Storage Shelf",
            "Top-of-Rack Network Switch",
            "Core Data Center Switch",
            "Application Delivery Firewall",
            "Virtualization Management Server",
            "Backup Appliance",
            "KVM-over-IP Gateway",
        ],
        "Port Monitoring and CCTV": [
            "Harbor PTZ CCTV Camera",
            "Thermal Surveillance Camera",
            "NVR Recording Server",
            "Video Management Software Server",
            "Maritime Radar Display Console",
            "Industrial PoE Camera Switch",
            "Edge Analytics Camera Gateway",
            "Long-range IR Illuminator",
            "CCTV Central Storage Unit",
            "Perimeter Intrusion Camera Kit",
        ],
        "Network and Security": [
            "Enterprise Edge Router",
            "Data Center Firewall Cluster",
            "Network Access Control Appliance",
            "Intrusion Detection Sensor",
            "Secure Web Gateway Appliance",
            "Identity Management Server",
            "SIEM Log Collector Node",
            "VPN Concentrator",
            "DDoS Protection Appliance",
            "Branch Security Gateway",
        ],
        "Industrial Control and Instrumentation": [
            "PLC Main Control Rack",
            "RTU Field Controller",
            "Industrial I/O Expansion Module",
            "Process Signal Conditioner",
            "SCADA Communication Gateway",
            "HMI Industrial Panel PC",
            "Motor Control Cabinet",
            "Pressure Transmitter Package",
            "Flow Meter Signal Unit",
            "Instrumentation Junction Cabinet",
        ],
        "Power Backup and UPS": [
            "Modular UPS Unit",
            "UPS Battery Bank Cabinet",
            "Static Transfer Switch",
            "Power Distribution Unit",
            "Generator Synchronization Panel",
            "Battery Monitoring Controller",
            "Rectifier Charger Module",
            "DC Distribution Board",
            "Power Quality Analyzer",
            "Emergency Power Control Panel",
        ],
        "Fiber and Passive Network": [
            "Fiber Optic ODF Frame",
            "Core Fiber Distribution Switch",
            "DWDM Transport Shelf",
            "Fiber Splice Enclosure",
            "Industrial Media Converter",
            "Fiber Patch Panel",
            "High-density Fiber Cassette",
            "Passive CWDM Mux-Demux",
            "Fiber Link Monitoring Unit",
            "Campus Distribution Cabinet",
        ],
        "Access Control and Perimeter": [
            "Biometric Access Terminal",
            "RFID Access Control Panel",
            "Turnstile Control Unit",
            "Perimeter Fence Sensor Controller",
            "Vehicle Gate Barrier Controller",
            "Door Lock Power Supply Unit",
            "Visitor Management Kiosk",
            "Access Control Server",
            "Emergency Egress Controller",
            "Guard Patrol Checkpoint Reader",
        ],
        "Command Center and Visualization": [
            "Video Wall Controller",
            "Command Center Operator Console",
            "Large-format Monitoring Display",
            "Mission Control Audio Processor",
            "Control Room Matrix Switcher",
            "Digital Signage Processor",
            "Unified Alerting Server",
            "Interactive Situation Display",
            "Control Room Workstation",
            "Incident Timeline Server",
        ],
        "Remote Communications": [
            "Microwave Point-to-Point Radio",
            "LTE Private Network Router",
            "VSAT Terminal Controller",
            "Remote Site Industrial Switch",
            "Satellite Link Encryption Unit",
            "Telemetry Communication Gateway",
            "Ruggedized Field Router",
            "Out-of-band Management Unit",
            "Wireless Backhaul Antenna Kit",
            "Remote Site Network Cabinet",
        ],
        "Safety and Specialized Systems": [
            "Fire Detection Control Panel",
            "Gas Detection Sensor Hub",
            "Emergency Paging Controller",
            "Industrial Siren Activation Unit",
            "Hazard Monitoring Data Logger",
            "Workplace Safety Camera Node",
            "Incident Recording Appliance",
            "Safety Compliance Server",
            "Environmental Sensor Gateway",
            "Protective Relay Controller",
        ],
    }

    companies = [
        "Pars Dadeh Sanat",
        "Arman Control Systems",
        "Fanavaran Roshd",
        "Paya Energy Co",
        "Nava Telecom",
        "Sina Industrial Tech",
        "Rivar Systems",
        "Corbit Integrations",
        "Homa Network Solutions",
        "Kian Monitoring",
    ]

    units = ["set", "unit", "kit"]
    category_price_ranges: Dict[str, Tuple[int, int]] = {
        "Data Center Infrastructure": (80_000_000_000, 420_000_000_000),
        "Port Monitoring and CCTV": (25_000_000_000, 180_000_000_000),
        "Network and Security": (40_000_000_000, 320_000_000_000),
        "Industrial Control and Instrumentation": (30_000_000_000, 260_000_000_000),
        "Power Backup and UPS": (45_000_000_000, 360_000_000_000),
        "Fiber and Passive Network": (18_000_000_000, 150_000_000_000),
        "Access Control and Perimeter": (22_000_000_000, 140_000_000_000),
        "Command Center and Visualization": (35_000_000_000, 280_000_000_000),
        "Remote Communications": (26_000_000_000, 210_000_000_000),
        "Safety and Specialized Systems": (20_000_000_000, 170_000_000_000),
    }

    subitem_templates: Dict[str, List[Tuple[str, str]]] = {
        "Data Center Infrastructure": [
            ("Compute Module", "Dual-socket compute board with virtualization support"),
            ("Memory Kit", "ECC DDR memory bank matched for workload profile"),
            ("Storage Bay", "Hot-swap enterprise storage bay"),
            ("Power Module", "Redundant high-efficiency PSU"),
            ("Cooling Assembly", "Adaptive airflow and thermal control"),
            ("Network Interface", "10/25/40G network uplink card"),
            ("Rack Rail Kit", "Standard 19-inch rack mounting rail"),
            ("Firmware License", "Firmware and remote management entitlement"),
        ],
        "Port Monitoring and CCTV": [
            ("Imaging Sensor", "Low-light or thermal imaging sensor"),
            ("Lens Assembly", "Varifocal/zoom lens assembly"),
            ("PoE Injector", "Industrial-grade PoE feed module"),
            ("Mounting Bracket", "Corrosion-resistant outdoor mount"),
            ("Recording License", "Multi-channel recording software license"),
            ("Weather Shield", "IP-rated weatherproof protection"),
            ("Edge Analytics Module", "AI motion/object analytics compute board"),
            ("Surge Protection Unit", "Transient surge suppression module"),
        ],
        "Network and Security": [
            ("Control Plane Module", "Routing/security control plane board"),
            ("Data Plane Module", "Packet processing and acceleration unit"),
            ("Management Port Kit", "Out-of-band management interface kit"),
            ("Power Supply Redundancy", "Dual-feed redundant power unit"),
            ("Security Subscription", "Threat signature and update entitlement"),
            ("Rack Mount Kit", "Rack ears and reinforcement frame"),
            ("High-speed Optics", "Compatible transceiver optics set"),
            ("HA Synchronization Link", "State sync link for clustered mode"),
        ],
        "Industrial Control and Instrumentation": [
            ("CPU Control Core", "Real-time deterministic control processor"),
            ("Digital Input Module", "24V industrial digital input interface"),
            ("Digital Output Module", "Relay/transistor output interface"),
            ("Analog Signal Module", "4-20mA / 0-10V analog module"),
            ("Fieldbus Adapter", "Modbus/Profibus communication adapter"),
            ("Panel Power Unit", "Conditioned industrial power module"),
            ("I/O Terminal Block", "Shielded wiring terminal interface"),
            ("Control Firmware", "Validated industrial control firmware"),
        ],
        "Power Backup and UPS": [
            ("Rectifier Block", "Input AC to DC conversion module"),
            ("Inverter Block", "DC to AC inverter module"),
            ("Battery Cell Group", "High-cycle battery cell module"),
            ("Bypass Module", "Static/manual bypass switching unit"),
            ("Monitoring Controller", "Battery and load monitoring controller"),
            ("Thermal Protection", "Temperature and thermal trip protection"),
            ("Distribution Breaker Set", "Output breaker and protection pack"),
            ("Maintenance Kit", "Startup and maintenance accessories"),
        ],
        "Fiber and Passive Network": [
            ("Fiber Tray", "High-density splice tray"),
            ("Connector Set", "LC/SC connector and ferrule set"),
            ("Patch Cord Bundle", "Pre-tested fiber patch cord bundle"),
            ("Optical Module", "Transceiver/optical interface module"),
            ("Cable Management Arm", "Horizontal/vertical cable manager"),
            ("Labeling Kit", "Fiber route labeling and coding kit"),
            ("Protection Sleeve", "Splice protection sleeve pack"),
            ("Grounding Kit", "Optical cabinet grounding accessories"),
        ],
        "Access Control and Perimeter": [
            ("Reader Interface", "Card/biometric reader interface board"),
            ("Door Controller", "Door state and lock control module"),
            ("Power Backup Cell", "Backup battery module for controllers"),
            ("Tamper Sensor", "Tamper and enclosure breach sensor"),
            ("Event Logger", "Access event logging and buffering unit"),
            ("Relay Output Board", "Auxiliary output relay board"),
            ("Communication Bridge", "TCP/IP and RS485 bridge module"),
            ("Credential License", "Credential/user management entitlement"),
        ],
        "Command Center and Visualization": [
            ("Display Processor", "Real-time video composition processor"),
            ("Input Capture Card", "Multi-input capture interface"),
            ("Control Surface", "Operator control surface module"),
            ("Audio Codec Unit", "Audio encode/decode controller"),
            ("Signal Distribution", "Video/audio distribution amplifier"),
            ("Controller Software", "Video wall control software license"),
            ("Redundant PSU", "N+1 power redundancy module"),
            ("Rack Integration Kit", "Cabinet integration hardware set"),
        ],
        "Remote Communications": [
            ("RF Module", "High-gain RF transmission module"),
            ("Antenna Feed Kit", "Antenna feedline and connector set"),
            ("Baseband Processor", "Digital baseband processing board"),
            ("Encryption Engine", "Secure payload encryption module"),
            ("Outdoor Enclosure", "IP-rated outdoor equipment enclosure"),
            ("Power Regulator", "Input regulation for unstable sources"),
            ("Management Controller", "Remote telemetry/control controller"),
            ("Alignment Tool Kit", "Field alignment and diagnostics toolset"),
        ],
        "Safety and Specialized Systems": [
            ("Sensing Element", "Primary sensing and detection element"),
            ("Signal Interface", "Signal conditioning interface card"),
            ("Alarm Relay", "Alarm relay and annunciation output"),
            ("Controller Board", "Safety logic controller board"),
            ("Compliance License", "Compliance and reporting software license"),
            ("Backup Power Pack", "Backup battery power pack"),
            ("Mounting Assembly", "Industrial mount and housing assembly"),
            ("Calibration Kit", "Factory/field calibration accessory set"),
        ],
    }

    rows: List[Dict[str, Any]] = []
    global_index = 0
    for category, names in category_items.items():
        pmin, pmax = category_price_ranges[category]
        for local_index, item_name in enumerate(names):
            company = companies[(global_index + local_index) % len(companies)]
            model = f"{category.split()[0][:3].upper()}-{1405 + local_index:04d}-{(global_index % 17) + 11}"
            unit = units[(global_index + local_index) % len(units)]
            span = pmax - pmin
            base_price = Decimal(pmin + ((global_index * 19 + local_index * 37) % max(1, span)))
            components = subitem_templates[category]
            rows.append(
                {
                    "company": company,
                    "item_name": item_name,
                    "model": model,
                    "category": category,
                    "unit": unit,
                    "description": (
                        f"{item_name} for project procurement scenarios; suitable for {category.lower()} workloads."
                    ),
                    "base_sales_price_irr": base_price,
                    "components": components,
                    "component_count": 2 + ((global_index + local_index) % 7),
                }
            )
            global_index += 1
    return rows[:TARGET_MASTER_ITEMS]


def _project_blueprints() -> List[Dict[str, Any]]:
    return [
        {
            "project_code": f"{PREFIX}PRJ_DC_UPGRADE",
            "name": "ارتقا زیرساخت مرکز داده ملی | کارفرما: شرکت توسعه زیرساخت داده ایرانیان",
            "priority_weight": 10,
            "budget_amount": Decimal("1450000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 4,
            "phase_end_month": 9,
            "description": "Data center infrastructure upgrade",
        },
        {
            "project_code": f"{PREFIX}PRJ_PORT_CCTV",
            "name": "گسترش پایش تصویری بندر جنوبی | کارفرما: سازمان بنادر پارس",
            "priority_weight": 8,
            "budget_amount": Decimal("980000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 4,
            "phase_end_month": 10,
            "description": "Port monitoring and CCTV expansion",
        },
        {
            "project_code": f"{PREFIX}PRJ_NET_SEC_MOD",
            "name": "نوسازی شبکه و امنیت سازمانی | کارفرما: هلدینگ فناوری راهبرد",
            "priority_weight": 9,
            "budget_amount": Decimal("1120000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 5,
            "phase_end_month": 11,
            "description": "Network and security modernization",
        },
        {
            "project_code": f"{PREFIX}PRJ_INSTRUMENT",
            "name": "به‌روزرسانی کنترل صنعتی و ابزار دقیق | کارفرما: صنایع فرایندی خاور",
            "priority_weight": 7,
            "budget_amount": Decimal("860000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 5,
            "phase_end_month": 12,
            "description": "Industrial control and instrumentation upgrade",
        },
        {
            "project_code": f"{PREFIX}PRJ_UPS_BACKUP",
            "name": "استقرار پشتیبان توان و UPS | کارفرما: گروه انرژی پایدار",
            "priority_weight": 8,
            "budget_amount": Decimal("740000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 6,
            "phase_end_month": 12,
            "description": "Power backup and UPS deployment",
        },
        {
            "project_code": f"{PREFIX}PRJ_FIBER_BACKBONE",
            "name": "رول‌اوت فیبر نوری ستون فقرات | کارفرما: شرکت ارتباطات پیشرو",
            "priority_weight": 9,
            "budget_amount": Decimal("1260000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 4,
            "phase_end_month": 12,
            "description": "Fiber optic backbone rollout",
        },
        {
            "project_code": f"{PREFIX}PRJ_ACCESS_PERIMETER",
            "name": "کنترل دسترسی و امنیت پیرامونی | کارفرما: مجموعه صنایع بندری شرق",
            "priority_weight": 7,
            "budget_amount": Decimal("690000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 7,
            "phase_end_month": 12,
            "description": "Access control and perimeter security",
        },
        {
            "project_code": f"{PREFIX}PRJ_SERVER_STORAGE",
            "name": "توسعه ظرفیت سرور و ذخیره‌سازی | کارفرما: بانک داده فراگیر",
            "priority_weight": 9,
            "budget_amount": Decimal("1320000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 6,
            "phase_end_month": 11,
            "description": "Server/storage expansion",
        },
        {
            "project_code": f"{PREFIX}PRJ_CMD_CENTER",
            "name": "راه‌اندازی مرکز فرماندهی و ویدئووال | کارفرما: مرکز پایش یکپارچه کشور",
            "priority_weight": 8,
            "budget_amount": Decimal("1010000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 5,
            "phase_end_month": 12,
            "description": "Command center and video wall setup",
        },
        {
            "project_code": f"{PREFIX}PRJ_REMOTE_COMMS",
            "name": "ارتباطات سایت‌های دورافتاده | کارفرما: شرکت عملیات میدانی راهبرد",
            "priority_weight": 7,
            "budget_amount": Decimal("770000000000"),
            "budget_currency": "IRR",
            "phase_start_month": 4,
            "phase_end_month": 10,
            "description": "Remote site communications upgrade",
        },
    ]


def _iranian_suppliers() -> List[Dict[str, str]]:
    return [
        {"company_name": "شرکت مهندسی داده‌گستر پارس", "city": "تهران"},
        {"company_name": "تجهیزات شبکه آریا پرداز", "city": "کرج"},
        {"company_name": "صنایع کنترل فرایند آبتین", "city": "اصفهان"},
        {"company_name": "راهکارهای مانیتورینگ ساحل‌نگر", "city": "بندرعباس"},
        {"company_name": "گروه مهندسی امن‌پرداز نوین", "city": "مشهد"},
        {"company_name": "سامانه‌های نیرو و پشتیبان کویر", "city": "یزد"},
        {"company_name": "توسعه ارتباطات فیبر شرق", "city": "تبریز"},
        {"company_name": "اندیشه‌سازان امنیت پیرامون", "city": "شیراز"},
        {"company_name": "تامین تجهیزات مرکز داده پویا", "city": "قم"},
        {"company_name": "فن‌آوران کنترل صنعتی نقش", "city": "اهواز"},
        {"company_name": "راهبران برق اضطراری سپهر", "city": "کرمان"},
        {"company_name": "تجارت گستر ابزار دقیق البرز", "city": "قزوین"},
        {"company_name": "پیشگامان زیرساخت شبکه خلیج", "city": "بوشهر"},
        {"company_name": "شرکت سامانه‌های نظارت هوشمند", "city": "اراک"},
        {"company_name": "مهندسی ارتباطات ایمن صبا", "city": "رشت"},
        {"company_name": "تجهیزات صنعتی رادین آریا", "city": "ساری"},
        {"company_name": "گروه فنی پایش تصویر فراز", "city": "کرمانشاه"},
        {"company_name": "پشتیبانان انرژی سبز نگین", "city": "زنجان"},
        {"company_name": "شرکت توسعه امنیت دیجیتال اکسین", "city": "همدان"},
        {"company_name": "مهندسی سامانه‌های فرمان نور", "city": "اردبیل"},
    ]


def _foreign_suppliers() -> List[Dict[str, str]]:
    return [
        {"company_name": "NordHafen Industrial Systems GmbH", "country": "Germany", "city": "Hamburg"},
        {"company_name": "Shenzhen Harbor Vision Tech Co.", "country": "China", "city": "Shenzhen"},
        {"company_name": "Gulf Integrated Security FZCO", "country": "UAE", "city": "Dubai"},
        {"company_name": "Anatolia Network Solutions A.S.", "country": "Turkey", "city": "Istanbul"},
        {"company_name": "Milano Data Infrastructure SRL", "country": "Italy", "city": "Milan"},
        {"company_name": "DeltaFiber Backbone BV", "country": "Netherlands", "city": "Rotterdam"},
        {"company_name": "Seoul Control Automation Ltd.", "country": "South Korea", "city": "Seoul"},
        {"company_name": "Bharat Remote Link Pvt. Ltd.", "country": "India", "city": "Bangalore"},
        {"company_name": "Paris Secure Operations SAS", "country": "France", "city": "Paris"},
        {"company_name": "Crown Harbor Monitoring Ltd.", "country": "United Kingdom", "city": "London"},
        {"company_name": "RheinGrid Energy Controls GmbH", "country": "Germany", "city": "Berlin"},
        {"company_name": "Nanjing Industrial Telemetry Co.", "country": "China", "city": "Nanjing"},
        {"company_name": "Abu Dhabi Mission Systems LLC", "country": "UAE", "city": "Abu Dhabi"},
        {"company_name": "Marmara Safety Technologies", "country": "Turkey", "city": "Ankara"},
        {"company_name": "Torino Power Electronics SpA", "country": "Italy", "city": "Turin"},
        {"company_name": "Amsterdam VideoWall Integrators BV", "country": "Netherlands", "city": "Amsterdam"},
        {"company_name": "Busan Maritime Sensors Co.", "country": "South Korea", "city": "Busan"},
        {"company_name": "Delhi Secure Network Works", "country": "India", "city": "New Delhi"},
        {"company_name": "Lyon Infrastructure Numerique", "country": "France", "city": "Lyon"},
        {"company_name": "Manchester Edge Communications", "country": "United Kingdom", "city": "Manchester"},
    ]


async def _get_admin_user(db) -> User:
    result = await db.execute(
        select(User).where(User.role == "admin", User.is_active == True).order_by(User.id.asc())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise RuntimeError("No active admin user found. Cannot generate UAT dataset safely.")
    return user


async def _reset_domain_data(db) -> Dict[str, int]:
    deleted: Dict[str, int] = {}
    users_before = await db.scalar(select(func.count(User.id)))

    delete_plan: List[Tuple[str, Any]] = [
        ("payments", delete(Payment)),
        ("invoices", delete(Invoice)),
        ("supplier_payments", delete(SupplierPayment)),
        ("cashflow_events", delete(CashflowEvent)),
        ("finalized_decisions", delete(FinalizedDecision)),
        ("optimization_results", delete(OptimizationResult)),
        ("optimization_runs", delete(OptimizationRun)),
        ("procurement_options", delete(ProcurementOption)),
        ("delivery_options", delete(DeliveryOption)),
        ("package_subitems", delete(PackageSubItem)),
        ("procurement_packages", delete(ProcurementPackage)),
        ("project_item_subitems", delete(ProjectItemSubItem)),
        ("project_items", delete(ProjectItem)),
        ("project_phases", delete(ProjectPhase)),
        ("project_assignments", delete(ProjectAssignment)),
        ("projects", delete(Project)),
        ("supplier_documents", delete(SupplierDocument)),
        ("supplier_contacts", delete(SupplierContact)),
        ("suppliers", delete(Supplier)),
        ("item_subitems", delete(ItemSubItem)),
        ("items_master", delete(ItemMaster)),
        ("budget_data", delete(BudgetData)),
        ("exchange_rates", delete(ExchangeRate)),
        ("currencies", delete(Currency)),
        (
            "audit_logs_domain",
            delete(AuditLog).where(
                or_(
                    AuditLog.action != "LOGIN",
                    AuditLog.entity_type.in_(
                        [
                            "project",
                            "project_item",
                            "item_master",
                            "supplier",
                            "procurement_option",
                            "procurement_package",
                            "delivery_option",
                            "decision",
                            "finance",
                            "demo_dataset",
                        ]
                    ),
                )
            ),
        ),
    ]

    for key, stmt in delete_plan:
        result = await db.execute(stmt)
        deleted[key] = int(result.rowcount or 0)
    await db.commit()

    users_after = await db.scalar(select(func.count(User.id)))
    deleted["users_before"] = int(users_before or 0)
    deleted["users_after"] = int(users_after or 0)
    deleted["users_preserved"] = int(users_before == users_after)
    return deleted


async def _cleanup_prefixed_data(db) -> Dict[str, int]:
    deleted: Dict[str, int] = {}

    project_ids = (
        await db.execute(select(Project.id).where(Project.project_code.like(f"{PREFIX}%")))
    ).scalars().all()
    project_item_ids = (
        await db.execute(
            select(ProjectItem.id).where(
                or_(
                    ProjectItem.project_id.in_(project_ids) if project_ids else False,
                    ProjectItem.item_code.like(f"{PREFIX}%"),
                )
            )
        )
    ).scalars().all()
    package_ids = (
        await db.execute(
            select(ProcurementPackage.id).where(
                or_(
                    ProcurementPackage.project_item_id.in_(project_item_ids) if project_item_ids else False,
                    ProcurementPackage.package_name.like(f"{PREFIX}%"),
                )
            )
        )
    ).scalars().all()
    supplier_ids = (
        await db.execute(select(Supplier.id).where(Supplier.supplier_id.like(f"{PREFIX}%")))
    ).scalars().all()
    master_ids = (
        await db.execute(select(ItemMaster.id).where(ItemMaster.item_code.like(f"{PREFIX}%")))
    ).scalars().all()
    subitem_ids = (
        await db.execute(
            select(ItemSubItem.id).where(
                or_(
                    ItemSubItem.item_master_id.in_(master_ids) if master_ids else False,
                    ItemSubItem.part_number.like(f"{PREFIX}%"),
                )
            )
        )
    ).scalars().all()

    delete_plan: List[Tuple[str, Any]] = [
        ("payments", delete(Payment).where(Payment.package_id.in_(package_ids)) if package_ids else delete(Payment).where(False)),
        ("invoices", delete(Invoice).where(Invoice.package_id.in_(package_ids)) if package_ids else delete(Invoice).where(False)),
        (
            "supplier_payments",
            delete(SupplierPayment).where(
                or_(
                    SupplierPayment.package_id.in_(package_ids) if package_ids else False,
                    SupplierPayment.supplier_id.in_(supplier_ids) if supplier_ids else False,
                    SupplierPayment.item_code.like(f"{PREFIX}%"),
                )
            ),
        ),
        (
            "cashflow_events",
            delete(CashflowEvent).where(CashflowEvent.description.like(f"%{PREFIX}%")),
        ),
        (
            "finalized_decisions",
            delete(FinalizedDecision).where(
                or_(
                    FinalizedDecision.project_item_id.in_(project_item_ids) if project_item_ids else False,
                    FinalizedDecision.item_code.like(f"{PREFIX}%"),
                )
            ),
        ),
        (
            "procurement_options",
            delete(ProcurementOption).where(
                or_(
                    ProcurementOption.project_item_id.in_(project_item_ids) if project_item_ids else False,
                    ProcurementOption.package_id.in_(package_ids) if package_ids else False,
                    ProcurementOption.item_code.like(f"{PREFIX}%"),
                )
            ),
        ),
        (
            "delivery_options",
            delete(DeliveryOption).where(
                or_(
                    DeliveryOption.project_item_id.in_(project_item_ids) if project_item_ids else False,
                    DeliveryOption.package_id.in_(package_ids) if package_ids else False,
                )
            ),
        ),
        ("package_subitems", delete(PackageSubItem).where(PackageSubItem.package_id.in_(package_ids)) if package_ids else delete(PackageSubItem).where(False)),
        ("procurement_packages", delete(ProcurementPackage).where(ProcurementPackage.id.in_(package_ids)) if package_ids else delete(ProcurementPackage).where(False)),
        ("project_item_subitems", delete(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id.in_(project_item_ids)) if project_item_ids else delete(ProjectItemSubItem).where(False)),
        ("project_items", delete(ProjectItem).where(ProjectItem.id.in_(project_item_ids)) if project_item_ids else delete(ProjectItem).where(False)),
        ("project_phases", delete(ProjectPhase).where(ProjectPhase.project_id.in_(project_ids)) if project_ids else delete(ProjectPhase).where(False)),
        ("projects", delete(Project).where(Project.id.in_(project_ids)) if project_ids else delete(Project).where(False)),
        ("supplier_contacts", delete(SupplierContact).where(SupplierContact.supplier_id.in_(supplier_ids)) if supplier_ids else delete(SupplierContact).where(False)),
        ("supplier_documents", delete(SupplierDocument).where(SupplierDocument.supplier_id.in_(supplier_ids)) if supplier_ids else delete(SupplierDocument).where(False)),
        ("suppliers", delete(Supplier).where(Supplier.id.in_(supplier_ids)) if supplier_ids else delete(Supplier).where(False)),
        ("item_subitems", delete(ItemSubItem).where(ItemSubItem.id.in_(subitem_ids)) if subitem_ids else delete(ItemSubItem).where(False)),
        ("items_master", delete(ItemMaster).where(ItemMaster.id.in_(master_ids)) if master_ids else delete(ItemMaster).where(False)),
        ("audit_logs", delete(AuditLog).where(AuditLog.action.like(f"{PREFIX}%"))),
    ]

    for key, stmt in delete_plan:
        result = await db.execute(stmt)
        deleted[key] = int(result.rowcount or 0)
    await db.commit()

    return deleted


async def _ensure_currencies_and_rates(db, admin_id: int, month_boundaries: List[Dict[str, Any]]) -> Dict[str, int]:
    currency_map: Dict[str, Dict[str, Any]] = {
        "IRR": {"name": "Iranian Rial", "symbol": "IRR", "is_base": True},
        "USD": {"name": "US Dollar", "symbol": "$", "is_base": False},
        "EUR": {"name": "Euro", "symbol": "EUR", "is_base": False},
        "AED": {"name": "UAE Dirham", "symbol": "AED", "is_base": False},
        "CNY": {"name": "Chinese Yuan", "symbol": "CNY", "is_base": False},
        "TRY": {"name": "Turkish Lira", "symbol": "TRY", "is_base": False},
    }
    synthetic_rates = {
        "USD": Decimal("640000"),
        "EUR": Decimal("700000"),
        "AED": Decimal("174000"),
        "CNY": Decimal("89000"),
        "TRY": Decimal("19800"),
    }

    created_currency = 0
    updated_currency = 0
    created_rates = 0
    updated_rates = 0
    currency_id_by_code: Dict[str, int] = {}

    for code, info in currency_map.items():
        result = await db.execute(select(Currency).where(Currency.code == code))
        row = result.scalar_one_or_none()
        if row:
            row.name = info["name"]
            row.symbol = info["symbol"]
            row.is_base_currency = bool(info["is_base"])
            row.is_active = True
            row.created_by_id = admin_id
            currency_id_by_code[code] = row.id
            updated_currency += 1
        else:
            row = Currency(
                code=code,
                name=info["name"],
                symbol=info["symbol"],
                is_base_currency=bool(info["is_base"]),
                is_active=True,
                decimal_places=0 if code == "IRR" else 2,
                created_by_id=admin_id,
            )
            db.add(row)
            await db.flush()
            currency_id_by_code[code] = row.id
            created_currency += 1

    for month_idx, m in enumerate(month_boundaries):
        rate_date = datetime.fromisoformat(m["gregorian_start"]).date()
        for code, base_rate in synthetic_rates.items():
            adjusted_rate = _q(base_rate * Decimal(1 + ((month_idx % 3) * 0.015)))
            result = await db.execute(
                select(ExchangeRate).where(
                    ExchangeRate.date == rate_date,
                    ExchangeRate.from_currency == code,
                    ExchangeRate.to_currency == "IRR",
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.rate = adjusted_rate
                existing.is_active = True
                existing.created_by_id = admin_id
                updated_rates += 1
            else:
                row = ExchangeRate(
                    date=rate_date,
                    from_currency=code,
                    to_currency="IRR",
                    rate=adjusted_rate,
                    is_active=True,
                    created_by_id=admin_id,
                )
                db.add(row)
                created_rates += 1

    await db.commit()
    return {
        "created_currency": created_currency,
        "updated_currency": updated_currency,
        "created_exchange_rates": created_rates,
        "updated_exchange_rates": updated_rates,
        "currency_ids": currency_id_by_code,
    }


async def _ensure_monthly_budgets(db, month_boundaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    budget_values = [
        Decimal("350000000000"),
        Decimal("420000000000"),
        Decimal("510000000000"),
        Decimal("740000000000"),
        Decimal("960000000000"),
        Decimal("880000000000"),
        Decimal("1120000000000"),
        Decimal("1280000000000"),
        Decimal("690000000000"),
    ]

    created = 0
    updated = 0
    for idx, month_info in enumerate(month_boundaries):
        budget_date = datetime.fromisoformat(month_info["gregorian_start"]).date()
        budget_amount = budget_values[idx]
        multi_currency = {
            "IRR": float(budget_amount),
            "USD": float((budget_amount / Decimal("640000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "EUR": float((budget_amount / Decimal("700000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "AED": float((budget_amount / Decimal("174000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "CNY": float((budget_amount / Decimal("89000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "TRY": float((budget_amount / Decimal("19800")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        }

        existing = await db.execute(select(BudgetData).where(BudgetData.budget_date == budget_date))
        row = existing.scalar_one_or_none()
        if row:
            row.available_budget = budget_amount
            row.multi_currency_budget = multi_currency
            updated += 1
        else:
            await create_budget_data(
                db,
                BudgetDataCreate(
                    budget_date=budget_date,
                    available_budget=budget_amount,
                    multi_currency_budget={k: Decimal(str(v)) for k, v in multi_currency.items()},
                ),
            )
            created += 1

    await db.commit()
    return {"created_budgets": created, "updated_budgets": updated}


async def _create_master_catalog(db, admin_id: int) -> List[MasterRecord]:
    records: List[MasterRecord] = []
    blueprints = _catalog_blueprints()

    for idx, bp in enumerate(blueprints):
        model = bp["model"]
        code = f"{PREFIX}{generate_item_code(bp['company'], bp['item_name'], model)}"[:100]

        existing_result = await db.execute(select(ItemMaster).where(ItemMaster.item_code == code))
        master = existing_result.scalar_one_or_none()
        if master:
            # Replace sub-items to keep deterministic generator behavior.
            await db.execute(delete(ItemSubItem).where(ItemSubItem.item_master_id == master.id))
            master.company = bp["company"]
            master.item_name = bp["item_name"]
            master.model = model
            master.category = bp["category"]
            master.unit = bp["unit"]
            master.description = bp["description"]
            master.specifications = {
                "base_sales_price_irr": int(bp["base_sales_price_irr"]),
                "uat_tag": PREFIX,
                "technical_profile": f"{bp['category']} standard technical profile",
            }
            master.created_by_id = admin_id
            master.is_active = True
            await db.flush()
        else:
            master = ItemMaster(
                item_code=code,
                company=bp["company"],
                item_name=bp["item_name"],
                model=model,
                category=bp["category"],
                unit=bp["unit"],
                description=bp["description"],
                specifications={
                    "base_sales_price_irr": int(bp["base_sales_price_irr"]),
                    "uat_tag": PREFIX,
                    "technical_profile": f"{bp['category']} standard technical profile",
                },
                created_by_id=admin_id,
                is_active=True,
            )
            db.add(master)
            await db.flush()

        component_count = min(len(bp["components"]), max(2, bp["component_count"]))
        chosen_components = bp["components"][:component_count]
        subitem_rules: List[Dict[str, Any]] = []
        for comp_idx, (comp_name, comp_req) in enumerate(chosen_components, start=1):
            part_number = f"{PREFIX}{code[:40]}-C{comp_idx:02d}"
            row = ItemSubItem(
                item_master_id=master.id,
                name=comp_name,
                description=comp_req,
                part_number=part_number,
            )
            db.add(row)
            await db.flush()
            subitem_rules.append(
                {
                    "sub_item_id": row.id,
                    "multiplier": 1 + ((idx + comp_idx) % 2),
                    "requirement": comp_req,
                }
            )

        records.append(
            MasterRecord(
                id=master.id,
                item_code=master.item_code,
                item_name=master.item_name,
                category=master.category or "",
                unit=master.unit,
                base_sales_price_irr=Decimal(str(bp["base_sales_price_irr"])),
                subitem_rules=subitem_rules,
            )
        )

    await db.commit()
    return records


async def _create_projects(db) -> List[Dict[str, Any]]:
    projects: List[Dict[str, Any]] = []
    for bp in _project_blueprints():
        existing = await db.execute(select(Project).where(Project.project_code == bp["project_code"]))
        row = existing.scalar_one_or_none()
        payload = ProjectCreate(
            project_code=bp["project_code"],
            name=bp["name"],
            priority_weight=bp["priority_weight"],
        )
        if row:
            row.name = bp["name"]
            row.priority_weight = bp["priority_weight"]
            row.budget_amount = bp["budget_amount"]
            row.budget_currency = bp["budget_currency"]
            row.is_active = True
            await db.flush()
        else:
            row = await create_project(db, payload)
            row.budget_amount = bp["budget_amount"]
            row.budget_currency = bp["budget_currency"]
            row.is_active = True
            await db.commit()
            await db.refresh(row)

        # Rebuild project phase deterministically
        await db.execute(delete(ProjectPhase).where(ProjectPhase.project_id == row.id))
        phase_start = jalali_to_gregorian(1405, bp["phase_start_month"], 3)
        phase_end = jalali_to_gregorian(1405, bp["phase_end_month"], 26)
        phase = ProjectPhase(
            project_id=row.id,
            phase_name=f"{PREFIX}Main Execution Window",
            start_date=phase_start,
            end_date=phase_end,
        )
        db.add(phase)
        await db.flush()
        projects.append(
            {
                "id": int(row.id),
                "project_code": row.project_code,
                "name": row.name,
            }
        )

    await db.commit()
    return projects


async def _create_project_items_and_base_delivery(
    db,
    projects: List[Dict[str, Any]],
    masters: List[MasterRecord],
) -> List[ProjectItemRecord]:
    created_items: List[ProjectItemRecord] = []
    today_utc = datetime.utcnow()

    for project_idx, project in enumerate(projects):
        project_id = int(project["id"])
        for local_idx in range(TARGET_PROJECT_ITEMS_PER_PROJECT):
            master = masters[(project_idx * 13 + local_idx * 7) % len(masters)]
            qty = 1 + ((project_idx + local_idx) % 8)
            month_number = 4 + ((project_idx * 3 + local_idx) % 9)
            day_number = 5 + ((project_idx + local_idx * 2) % 20)
            requested_date = jalali_to_gregorian(1405, month_number, day_number)
            delivery_options = [requested_date.isoformat()]

            sales_unit_price = _q(
                master.base_sales_price_irr
                * (Decimal("1.00") + Decimal((project_idx % 3) * 5 + (local_idx % 4) * 2) / Decimal("100"))
            )
            item_description = (
                f"{PREFIX} {master.item_name} | Model {masters[(local_idx + 3) % len(masters)].item_code[-10:]} | "
                f"Estimated sales unit price (IRR): {int(sales_unit_price)}"
            )
            sub_items_payload = [
                {"sub_item_id": r["sub_item_id"], "quantity": int(qty * r["multiplier"])}
                for r in master.subitem_rules
            ]

            item = await create_project_item(
                db,
                ProjectItemCreate(
                    project_id=project_id,
                    master_item_id=master.id,
                    item_code=master.item_code,
                    item_name=master.item_name,
                    quantity=qty,
                    delivery_options=delivery_options,
                    status=ProjectItemStatus.PENDING.value,
                    external_purchase=False,
                    description=item_description,
                    is_finalized=False,
                    finalized_by=None,
                    finalized_at=None,
                    sub_items=sub_items_payload,
                ),
            )
            item_id = int(item.id)
            item_code = str(item.item_code)

            # Base delivery option to satisfy finalize workflow constraints.
            await create_delivery_option(
                db,
                DeliveryOptionCreate(
                    project_item_id=item_id,
                    package_id=None,
                    delivery_slot=(local_idx % 4) + 1,
                    delivery_date=requested_date,
                    invoice_timing_type="RELATIVE",
                    invoice_issue_date=None,
                    invoice_days_after_delivery=30,
                    invoice_amount_per_unit=sales_unit_price,
                    preference_rank=1,
                    notes=f"{PREFIX}Base delivery option",
                    is_active=True,
                ),
            )

            created_items.append(
                ProjectItemRecord(
                    id=item_id,
                    project_id=project_id,
                    item_code=item_code,
                    requested_date=requested_date,
                    quantity=qty,
                    sales_unit_price_irr=sales_unit_price,
                )
            )

            # Normalize created/updated fields for deterministic window.
            db_item = await db.get(ProjectItem, item_id)
            if db_item:
                db_item.created_at = today_utc
                db_item.updated_at = today_utc

    await db.commit()
    return created_items


async def _apply_finalization_distribution(db, admin_id: int, items: List[ProjectItemRecord]) -> Dict[str, int]:
    finalized_target = int((Decimal(len(items)) * TARGET_FINALIZED_RATIO).to_integral_value(rounding=ROUND_HALF_UP))
    finalized_target = min(finalized_target, len(items))
    finalized_ids = {itm.id for itm in items[:finalized_target]}

    for itm in items:
        db_item = await db.get(ProjectItem, itm.id)
        if not db_item:
            continue
        if itm.id in finalized_ids:
            await finalize_project_item(
                db,
                db_item.id,
                admin_id,
                ProjectItemFinalize(is_finalized=True, finalized_at=datetime.utcnow()),
            )
            db_item.status = ProjectItemStatus.DECIDED
        else:
            db_item.is_finalized = False
            db_item.finalized_by = None
            db_item.finalized_at = None
            db_item.status = ProjectItemStatus.PENDING

    await db.commit()
    return {
        "total_project_items": len(items),
        "finalized_project_items": len(finalized_ids),
        "non_finalized_project_items": len(items) - len(finalized_ids),
        "sent_to_procurement_items": len(finalized_ids),  # mapped to is_finalized in current schema
    }


async def _create_suppliers(db, admin_id: int) -> Dict[str, Any]:
    domestic = _iranian_suppliers()
    foreign = _foreign_suppliers()

    created = 0
    updated = 0
    domestic_ids: List[int] = []
    foreign_ids: List[int] = []

    for idx, row in enumerate(domestic, start=1):
        supplier_code = f"{PREFIX}SUP_IR_{idx:03d}"
        existing = await db.execute(select(Supplier).where(Supplier.supplier_id == supplier_code))
        supplier = existing.scalar_one_or_none()
        payload = dict(
            supplier_id=supplier_code,
            company_name=row["company_name"],
            legal_entity_type="LLC",
            registration_number=f"IR-{1405}{idx:04d}",
            tax_id=f"IR-TAX-{idx:05d}",
            established_year=1385 + (idx % 15),
            country="Iran",
            city=row["city"],
            address=f"منطقه صنعتی {row['city']}، بلوک {idx}",
            website=f"https://{supplier_code.lower()}.example.ir",
            domain=f"{supplier_code.lower()}.example.ir",
            primary_email=f"sales{idx}@{supplier_code.lower()}.example.ir",
            main_phone=f"+98-21-{70000000 + idx}",
            category="Industrial & Technology Supply",
            industry="Infrastructure",
            product_service_lines=["Data Center", "Network", "Security"],
            main_brands_represented=["Rivar", "Corbit", "ParsTech"],
            main_markets_regions=["Iran"],
            certifications=["ISO9001", "ISO27001"],
            ownership_type="Private",
            annual_revenue_range="10M-100M",
            number_of_employees="50-200",
            warehouse_locations=[row["city"]],
            key_clients_references=["National Infrastructure Org", "Regional Utility Board"],
            payment_terms="30% advance / 60% before delivery / 10% after acceptance",
            currency_preference="IRR",
            shipping_methods=["Road", "Air"],
            incoterms=["EXW", "DAP"],
            average_lead_time_days=20 + (idx % 15),
            quality_assurance_process="Factory acceptance + site acceptance protocol",
            warranty_policy="18-month replacement warranty",
            after_sales_policy="On-site response within 48 hours",
            delivery_accuracy_percent=Decimal("92.00") + Decimal(idx % 7),
            response_time_hours=12 + (idx % 24),
            compliance_status="APPROVED",
            status="ACTIVE",
            risk_level="LOW" if idx % 4 else "MEDIUM",
            internal_rating=Decimal("4.20"),
            performance_metrics={"on_time_delivery": 90 + (idx % 8), "quality_score": 88 + (idx % 9)},
            notes=f"{PREFIX}Iranian approved supplier profile",
            created_by_id=admin_id,
            last_updated_by_id=admin_id,
        )
        if supplier:
            for k, v in payload.items():
                setattr(supplier, k, v)
            updated += 1
        else:
            supplier = Supplier(**payload)
            db.add(supplier)
            await db.flush()
            created += 1
        domestic_ids.append(supplier.id)

        contact = SupplierContact(
            contact_id=f"{PREFIX}CONT_IR_{idx:03d}",
            supplier_id=supplier.id,
            full_name=f"مدیر فروش {row['city']}",
            job_title="Sales Manager",
            role="Commercial",
            department="Sales",
            email=f"contact{idx}@{supplier_code.lower()}.example.ir",
            phone=f"+98-912-{300000 + idx}",
            language_preference="fa",
            timezone="Asia/Tehran",
            working_hours="08:30-16:30",
            is_primary_contact=True,
            is_active=True,
            notes=f"{PREFIX}Primary commercial contact",
            created_by_id=admin_id,
        )
        # Upsert simple contact
        existing_contact = await db.execute(select(SupplierContact).where(SupplierContact.contact_id == contact.contact_id))
        ec = existing_contact.scalar_one_or_none()
        if ec:
            for field in [
                "full_name",
                "job_title",
                "role",
                "department",
                "email",
                "phone",
                "language_preference",
                "timezone",
                "working_hours",
                "is_primary_contact",
                "is_active",
                "notes",
            ]:
                setattr(ec, field, getattr(contact, field))
        else:
            db.add(contact)

    for idx, row in enumerate(foreign, start=1):
        supplier_code = f"{PREFIX}SUP_FX_{idx:03d}"
        existing = await db.execute(select(Supplier).where(Supplier.supplier_id == supplier_code))
        supplier = existing.scalar_one_or_none()
        currency_pref = ["USD", "EUR", "AED", "CNY", "TRY"][idx % 5]
        payload = dict(
            supplier_id=supplier_code,
            company_name=row["company_name"],
            legal_entity_type="Corporation",
            registration_number=f"FX-{1405}{idx:04d}",
            tax_id=f"FX-TAX-{idx:05d}",
            established_year=1995 + (idx % 20),
            country=row["country"],
            city=row["city"],
            address=f"Business District, {row['city']}",
            website=f"https://{supplier_code.lower()}.global.example",
            domain=f"{supplier_code.lower()}.global.example",
            primary_email=f"sales@{supplier_code.lower()}.global.example",
            main_phone=f"+44-20-{76000000 + idx}",
            category="International Infrastructure Supply",
            industry="Technology & Industrial",
            product_service_lines=["Security", "Network", "Power", "Automation"],
            main_brands_represented=["GlobalEdge", "SecureLine", "Corbit"],
            main_markets_regions=[row["country"], "Middle East", "Central Asia"],
            certifications=["ISO9001", "ISO14001", "CE"],
            ownership_type="Private",
            annual_revenue_range=">100M",
            number_of_employees=">200",
            warehouse_locations=[row["city"], "Jebel Ali" if row["country"] != "UAE" else "Dubai Logistics"],
            key_clients_references=["Port Authority", "National Grid Operator"],
            payment_terms="50% advance / 50% on delivery",
            currency_preference=currency_pref,
            shipping_methods=["Sea", "Air", "Road"],
            incoterms=["FOB", "CIF", "DAP"],
            average_lead_time_days=35 + (idx % 25),
            quality_assurance_process="Factory QA + third-party pre-shipment inspection",
            warranty_policy="24-month international warranty",
            after_sales_policy="Remote troubleshooting + regional partner support",
            delivery_accuracy_percent=Decimal("89.00") + Decimal(idx % 6),
            response_time_hours=18 + (idx % 30),
            compliance_status="APPROVED",
            status="ACTIVE",
            risk_level="MEDIUM" if idx % 3 else "LOW",
            internal_rating=Decimal("4.10"),
            performance_metrics={"on_time_delivery": 85 + (idx % 10), "quality_score": 86 + (idx % 9)},
            notes=f"{PREFIX}Foreign approved supplier profile",
            created_by_id=admin_id,
            last_updated_by_id=admin_id,
        )
        if supplier:
            for k, v in payload.items():
                setattr(supplier, k, v)
            updated += 1
        else:
            supplier = Supplier(**payload)
            db.add(supplier)
            await db.flush()
            created += 1
        foreign_ids.append(supplier.id)

        contact = SupplierContact(
            contact_id=f"{PREFIX}CONT_FX_{idx:03d}",
            supplier_id=supplier.id,
            full_name=f"Regional Account Manager {idx:02d}",
            job_title="Regional Account Manager",
            role="Commercial",
            department="International Sales",
            email=f"ram{idx}@{supplier_code.lower()}.global.example",
            phone=f"+971-55-{400000 + idx}",
            language_preference="en",
            timezone="UTC+3",
            working_hours="09:00-18:00",
            is_primary_contact=True,
            is_active=True,
            notes=f"{PREFIX}Primary international contact",
            created_by_id=admin_id,
        )
        existing_contact = await db.execute(select(SupplierContact).where(SupplierContact.contact_id == contact.contact_id))
        ec = existing_contact.scalar_one_or_none()
        if ec:
            for field in [
                "full_name",
                "job_title",
                "role",
                "department",
                "email",
                "phone",
                "language_preference",
                "timezone",
                "working_hours",
                "is_primary_contact",
                "is_active",
                "notes",
            ]:
                setattr(ec, field, getattr(contact, field))
        else:
            db.add(contact)

    await db.commit()
    return {
        "created_suppliers": created,
        "updated_suppliers": updated,
        "domestic_supplier_ids": domestic_ids,
        "foreign_supplier_ids": foreign_ids,
    }


async def _create_procurement_data(
    db,
    finalized_items: List[ProjectItemRecord],
    domestic_supplier_ids: List[int],
    foreign_supplier_ids: List[int],
    currency_ids: Dict[str, int],
) -> Dict[str, Any]:
    procurement_target = int(
        (Decimal(len(finalized_items)) * TARGET_PROCUREMENT_RATIO_ON_FINALIZED).to_integral_value(
            rounding=ROUND_HALF_UP
        )
    )
    procurement_target = min(procurement_target, len(finalized_items))
    target_items = finalized_items[:procurement_target]

    early_target = int(Decimal(procurement_target) * Decimal("0.25"))
    late_target = int(Decimal(procurement_target) * Decimal("0.25"))

    packages_created = 0
    options_created = 0
    delivery_options_created = 0
    coverage_case_counter = {"fully_covered": 0, "partially_covered": 0, "uncovered": 0}
    mismatch_counter = {"early": 0, "aligned": 0, "late": 0}

    payment_terms_variants = [
        {"type": "installments", "schedule": [{"percent": 30, "due_offset": 0}, {"percent": 60, "due_offset": 30}, {"percent": 10, "due_offset": 75}]},
        {"type": "installments", "schedule": [{"percent": 50, "due_offset": 0}, {"percent": 50, "due_offset": 45}]},
        {"type": "installments", "schedule": [{"percent": 20, "due_offset": 0}, {"percent": 80, "due_offset": 30}]},
        {"type": "installments", "schedule": [{"percent": 0, "due_offset": 0}, {"percent": 100, "due_offset": 30}]},
    ]

    for idx, itm in enumerate(target_items):
        if idx < early_target:
            mismatch_kind = "early"
            delivery_date = itm.requested_date - timedelta(days=8 + (idx % 11))
        elif idx < early_target + late_target:
            mismatch_kind = "late"
            delivery_date = itm.requested_date + timedelta(days=9 + (idx % 14))
        else:
            mismatch_kind = "aligned"
            delivery_date = itm.requested_date + timedelta(days=(idx % 5) - 2)
        mismatch_counter[mismatch_kind] += 1

        foreign_purchase = (idx % 5 == 0)
        if foreign_purchase:
            supplier_id = foreign_supplier_ids[idx % len(foreign_supplier_ids)]
            currency_code = ["USD", "EUR", "AED", "CNY", "TRY"][idx % 5]
        else:
            supplier_id = domestic_supplier_ids[idx % len(domestic_supplier_ids)]
            currency_code = "IRR"

        supplier_obj = await db.get(Supplier, supplier_id)
        if not supplier_obj:
            continue
        supplier_name = str(supplier_obj.company_name)
        supplier_created_by_id = supplier_obj.created_by_id

        subitems_result = await db.execute(
            select(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id == itm.id).order_by(ProjectItemSubItem.id)
        )
        project_subitems = subitems_result.scalars().all()
        if not project_subitems:
            continue

        coverage_case = idx % 3  # 0 full, 1 complementary, 2 partial
        created_packages: List[Dict[str, Any]] = []

        async def _create_package(name_suffix: str, package_type: str, main_qty: int) -> Dict[str, Any]:
            await validate_main_item_quantity(db, itm.id, main_qty)
            pkg = ProcurementPackage(
                project_item_id=itm.id,
                package_name=f"{PREFIX}PKG_{itm.id}_{name_suffix}",
                package_type=package_type,
                supplier_id=supplier_id,
                description=f"{PREFIX}Package for project item {itm.item_code}",
                is_active=True,
                main_item_quantity=main_qty,
                created_by_id=supplier_created_by_id,
            )
            db.add(pkg)
            await db.flush()
            return {"id": int(pkg.id), "package_name": pkg.package_name}

        if coverage_case == 0:
            pkg = await _create_package("FULL", "FULL", itm.quantity)
            created_packages.append(pkg)
            for sub in project_subitems:
                coverage = await validate_and_compute_subitem_coverage(
                    db,
                    package_id=pkg["id"],
                    project_item_subitem_id=sub.id,
                    quantity_covered=int(sub.quantity or 0),
                )
                db.add(
                    PackageSubItem(
                        package_id=pkg["id"],
                        project_item_subitem_id=sub.id,
                        quantity_covered=int(sub.quantity or 0),
                        is_fully_covered=coverage["is_fully_covered"],
                        coverage_percentage=coverage["coverage_percentage"],
                    )
                )
            coverage_case_counter["fully_covered"] += 1
        elif coverage_case == 1:
            split_idx = max(1, len(project_subitems) // 2)
            pkg_a = await _create_package("PART_A", "PARTIAL", max(1, itm.quantity // 2))
            pkg_b = await _create_package("PART_B", "PARTIAL", itm.quantity - max(1, itm.quantity // 2))
            created_packages.extend([pkg_a, pkg_b])
            for sub in project_subitems[:split_idx]:
                coverage = await validate_and_compute_subitem_coverage(
                    db,
                    package_id=pkg_a["id"],
                    project_item_subitem_id=sub.id,
                    quantity_covered=int(sub.quantity or 0),
                )
                db.add(
                    PackageSubItem(
                        package_id=pkg_a["id"],
                        project_item_subitem_id=sub.id,
                        quantity_covered=int(sub.quantity or 0),
                        is_fully_covered=coverage["is_fully_covered"],
                        coverage_percentage=coverage["coverage_percentage"],
                    )
                )
            for sub in project_subitems[split_idx:]:
                coverage = await validate_and_compute_subitem_coverage(
                    db,
                    package_id=pkg_b["id"],
                    project_item_subitem_id=sub.id,
                    quantity_covered=int(sub.quantity or 0),
                )
                db.add(
                    PackageSubItem(
                        package_id=pkg_b["id"],
                        project_item_subitem_id=sub.id,
                        quantity_covered=int(sub.quantity or 0),
                        is_fully_covered=coverage["is_fully_covered"],
                        coverage_percentage=coverage["coverage_percentage"],
                    )
                )
            coverage_case_counter["fully_covered"] += 1
        else:
            pkg = await _create_package("PARTIAL", "PARTIAL", max(1, itm.quantity // 2))
            created_packages.append(pkg)
            subset_size = max(1, len(project_subitems) // 2)
            for sub in project_subitems[:subset_size]:
                partial_qty = max(1, int((sub.quantity or 0) * 0.6))
                coverage = await validate_and_compute_subitem_coverage(
                    db,
                    package_id=pkg["id"],
                    project_item_subitem_id=sub.id,
                    quantity_covered=partial_qty,
                )
                db.add(
                    PackageSubItem(
                        package_id=pkg["id"],
                        project_item_subitem_id=sub.id,
                        quantity_covered=partial_qty,
                        is_fully_covered=coverage["is_fully_covered"],
                        coverage_percentage=coverage["coverage_percentage"],
                    )
                )
            coverage_case_counter["partially_covered"] += 1

        packages_created += len(created_packages)

        # Create delivery+procurement options per package.
        for pkg_offset, pkg in enumerate(created_packages):
            unit_price = itm.sales_unit_price_irr
            cost_factor = Decimal("0.68") + Decimal(((idx + pkg_offset) % 9) / 100)
            total_cost = _q(unit_price * Decimal(itm.quantity) * cost_factor)
            shipping_cost = _q(total_cost * Decimal("0.03"))
            payment_terms = payment_terms_variants[(idx + pkg_offset) % len(payment_terms_variants)]
            procurement_item_code = itm.item_code[:50]

            await create_delivery_option(
                db,
                DeliveryOptionCreate(
                    package_id=pkg["id"],
                    project_item_id=itm.id,
                    delivery_slot=(pkg_offset % 3) + 1,
                    delivery_date=delivery_date,
                    invoice_timing_type="RELATIVE",
                    invoice_issue_date=None,
                    invoice_days_after_delivery=30 + ((idx + pkg_offset) % 20),
                    invoice_amount_per_unit=unit_price,
                    preference_rank=(pkg_offset + 1),
                    notes=f"{PREFIX}Delivery timing for mismatch scenario ({mismatch_kind})",
                    is_active=True,
                ),
            )
            delivery_option_id = await db.scalar(
                select(func.max(DeliveryOption.id)).where(
                    DeliveryOption.project_item_id == itm.id,
                    DeliveryOption.package_id == pkg["id"],
                    DeliveryOption.delivery_date == delivery_date,
                )
            )
            if not delivery_option_id:
                raise RuntimeError(f"Failed to resolve delivery option id for package {pkg['id']}")
            delivery_options_created += 1

            await create_procurement_option(
                db,
                ProcurementOptionCreate(
                    package_id=pkg["id"],
                    project_item_id=itm.id,
                    item_code=procurement_item_code,
                    supplier_name=supplier_name,
                    supplier_id=supplier_id,
                    base_cost=total_cost,
                    currency_id=currency_ids[currency_code],
                    shipping_cost=shipping_cost,
                    delivery_option_id=delivery_option_id,
                    lomc_lead_time=max(0, (delivery_date - itm.requested_date).days),
                    purchase_date=max(date.today(), itm.requested_date - timedelta(days=45)),
                    expected_delivery_date=delivery_date,
                    discount_bundle_threshold=max(1, itm.quantity // 2),
                    discount_bundle_percent=Decimal("2.50") + Decimal((idx + pkg_offset) % 4),
                    payment_terms=payment_terms,
                    is_finalized=True,
                ),
            )
            options_created += 1

    await db.commit()
    return {
        "target_items_with_procurement": procurement_target,
        "packages_created": packages_created,
        "procurement_options_created": options_created,
        "delivery_options_created": delivery_options_created,
        "coverage_case_counter": coverage_case_counter,
        "delivery_mismatch_counter": mismatch_counter,
    }


async def _validate_dataset(db) -> Dict[str, Any]:
    project_ids = (
        await db.execute(select(Project.id).where(Project.project_code.like(f"{PREFIX}%")))
    ).scalars().all()

    master_items_count = await db.scalar(
        select(func.count(ItemMaster.id)).where(ItemMaster.item_code.like(f"{PREFIX}%"))
    )
    subitems_count = await db.scalar(
        select(func.count(ItemSubItem.id))
        .join(ItemMaster, ItemMaster.id == ItemSubItem.item_master_id)
        .where(ItemMaster.item_code.like(f"{PREFIX}%"))
    )
    projects_count = await db.scalar(select(func.count(Project.id)).where(Project.project_code.like(f"{PREFIX}%")))
    project_items_count = await db.scalar(
        select(func.count(ProjectItem.id)).where(ProjectItem.project_id.in_(project_ids) if project_ids else False)
    )
    finalized_count = await db.scalar(
        select(func.count(ProjectItem.id)).where(
            ProjectItem.project_id.in_(project_ids) if project_ids else False,
            ProjectItem.is_finalized == True,
        )
    )
    non_finalized_count = await db.scalar(
        select(func.count(ProjectItem.id)).where(
            ProjectItem.project_id.in_(project_ids) if project_ids else False,
            ProjectItem.is_finalized == False,
        )
    )
    suppliers_domestic = await db.scalar(
        select(func.count(Supplier.id)).where(Supplier.supplier_id.like(f"{PREFIX}SUP_IR_%"))
    )
    suppliers_foreign = await db.scalar(
        select(func.count(Supplier.id)).where(Supplier.supplier_id.like(f"{PREFIX}SUP_FX_%"))
    )
    approved_suppliers = await db.scalar(
        select(func.count(Supplier.id)).where(
            Supplier.supplier_id.like(f"{PREFIX}SUP_%"),
            Supplier.status == "ACTIVE",
            Supplier.compliance_status == "APPROVED",
        )
    )

    required_currency_codes = ["IRR", "USD", "EUR", "AED", "CNY", "TRY"]
    currency_rows = (
        await db.execute(select(Currency.code).where(Currency.code.in_(required_currency_codes)))
    ).scalars().all()
    month_boundaries = jalali_month_boundaries_1405()
    budget_dates = [datetime.fromisoformat(row["gregorian_start"]).date() for row in month_boundaries]
    budget_months = await db.scalar(select(func.count(BudgetData.id)).where(BudgetData.budget_date.in_(budget_dates)))

    item_ids_with_procurement = (
        await db.execute(
            select(func.distinct(ProcurementPackage.project_item_id)).join(
                ProjectItem, ProjectItem.id == ProcurementPackage.project_item_id
            ).where(ProjectItem.project_id.in_(project_ids) if project_ids else False)
        )
    ).scalars().all()
    procurement_package_count = await db.scalar(
        select(func.count(ProcurementPackage.id)).join(ProjectItem, ProjectItem.id == ProcurementPackage.project_item_id).where(
            ProjectItem.project_id.in_(project_ids) if project_ids else False
        )
    )
    procurement_option_count = await db.scalar(
        select(func.count(ProcurementOption.id)).join(ProjectItem, ProjectItem.id == ProcurementOption.project_item_id).where(
            ProjectItem.project_id.in_(project_ids) if project_ids else False
        )
    )

    coverage_counts = {"fully_covered": 0, "partially_covered": 0, "uncovered": 0}
    delivery_counts = {"early": 0, "aligned": 0, "late": 0}

    for item_id in item_ids_with_procurement:
        summary = await calculate_coverage_summary(db, int(item_id))
        if summary["is_fully_covered"]:
            coverage_counts["fully_covered"] += 1
        else:
            has_any = any(v["covered"] > 0 for v in summary["subitems"].values())
            if has_any:
                coverage_counts["partially_covered"] += 1
            else:
                coverage_counts["uncovered"] += 1

        item = await db.get(ProjectItem, int(item_id))
        if not item or not item.delivery_options:
            continue
        requested = datetime.fromisoformat(item.delivery_options[0]).date()
        d_result = await db.execute(
            select(func.min(DeliveryOption.delivery_date)).where(
                DeliveryOption.project_item_id == int(item_id),
                DeliveryOption.package_id.is_not(None),
                DeliveryOption.is_active == True,
            )
        )
        actual = d_result.scalar_one_or_none()
        if not actual:
            continue
        delta = (actual - requested).days
        if delta < -2:
            delivery_counts["early"] += 1
        elif delta > 2:
            delivery_counts["late"] += 1
        else:
            delivery_counts["aligned"] += 1

    optimization_decisions = await db.scalar(select(func.count(FinalizedDecision.id)))

    return {
        "prefix": PREFIX,
        "master_item_count": int(master_items_count or 0),
        "sub_item_count": int(subitems_count or 0),
        "project_count": int(projects_count or 0),
        "project_item_count": int(project_items_count or 0),
        "finalized_count": int(finalized_count or 0),
        "sent_to_procurement_count": int(finalized_count or 0),
        "non_finalized_count": int(non_finalized_count or 0),
        "supplier_domestic_count": int(suppliers_domestic or 0),
        "supplier_foreign_count": int(suppliers_foreign or 0),
        "approved_supplier_count": int(approved_suppliers or 0),
        "currencies_available": sorted(list(set(currency_rows))),
        "budget_months_count": int(budget_months or 0),
        "procurement_item_count": int(len(item_ids_with_procurement)),
        "procurement_package_count": int(procurement_package_count or 0),
        "procurement_option_count": int(procurement_option_count or 0),
        "coverage_summary": coverage_counts,
        "delivery_summary": delivery_counts,
        "optimization_run": False,
        "finalized_decision_rows_present": int(optimization_decisions or 0),
        "jalali_to_gregorian_method": "jalaali algorithm implementation in script (deterministic conversion utility)",
        "jalali_range_boundaries": month_boundaries,
    }


async def mode_plan() -> Dict[str, Any]:
    month_map = jalali_month_boundaries_1405()
    finalized_target = int(
        (Decimal(TARGET_PROJECT_ITEMS) * TARGET_FINALIZED_RATIO).to_integral_value(rounding=ROUND_HALF_UP)
    )
    procurement_target = int(
        (Decimal(finalized_target) * TARGET_PROCUREMENT_RATIO_ON_FINALIZED).to_integral_value(
            rounding=ROUND_HALF_UP
        )
    )
    return {
        "mode": "plan",
        "prefix": PREFIX,
        "target_counts": {
            "master_items": TARGET_MASTER_ITEMS,
            "projects": TARGET_PROJECTS,
            "project_items_total": TARGET_PROJECT_ITEMS,
            "finalized_target": finalized_target,
            "procurement_target": procurement_target,
            "suppliers_domestic": 20,
            "suppliers_foreign": 20,
            "budget_months": len(JALALI_MONTHS_1405),
        },
        "jalali_to_gregorian_method": "jalaali algorithm implementation in script",
        "jalali_month_boundaries": month_map,
        "safety": {
            "preserve_users": True,
            "preserve_auth_records": True,
            "reset_domain_data_scope": "projects/items/procurement/finance/audit-domain only",
        },
    }


async def mode_reset_domain_data() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        admin = await _get_admin_user(db)
        reset_summary = await _reset_domain_data(db)
        # User preservation check.
        users_after = (
            await db.execute(select(User.username, User.role, User.is_active).order_by(User.id.asc()).limit(10))
        ).all()
        return {
            "mode": "reset-domain-data",
            "admin_user": admin.username,
            "reset_summary": reset_summary,
            "preserved_users_preview": [
                {"username": r[0], "role": r[1], "is_active": bool(r[2])}
                for r in users_after
            ],
        }


async def mode_cleanup() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        summary = await _cleanup_prefixed_data(db)
        validation = await _validate_dataset(db)
        return {"mode": "cleanup", "cleanup_summary": summary, "post_cleanup_validation": validation}


async def mode_create() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        admin = await _get_admin_user(db)
        admin_id = int(admin.id)
        cleanup_summary = await _cleanup_prefixed_data(db)

        month_boundaries = jalali_month_boundaries_1405()
        finance_summary = await _ensure_currencies_and_rates(db, admin_id, month_boundaries)
        budget_summary = await _ensure_monthly_budgets(db, month_boundaries)

        masters = await _create_master_catalog(db, admin_id)
        projects = await _create_projects(db)
        item_records = await _create_project_items_and_base_delivery(db, projects, masters)
        finalization_summary = await _apply_finalization_distribution(db, admin_id, item_records)
        supplier_summary = await _create_suppliers(db, admin_id)

        finalized_items = item_records[: finalization_summary["finalized_project_items"]]
        procurement_summary = await _create_procurement_data(
            db=db,
            finalized_items=finalized_items,
            domestic_supplier_ids=supplier_summary["domestic_supplier_ids"],
            foreign_supplier_ids=supplier_summary["foreign_supplier_ids"],
            currency_ids=finance_summary["currency_ids"],
        )

        db.add(
            AuditLog(
                user_id=admin_id,
                action=f"{PREFIX}DATASET_CREATE",
                entity_type="dataset",
                details={
                    "master_items": len(masters),
                    "projects": len(projects),
                    "project_items": len(item_records),
                    "finalized": finalization_summary["finalized_project_items"],
                    "procurement_items": procurement_summary["target_items_with_procurement"],
                },
            )
        )
        await db.commit()
        validation_summary = await _validate_dataset(db)

        return {
            "mode": "create",
            "prefix_cleanup_before_create": cleanup_summary,
            "finance_summary": finance_summary,
            "budget_summary": budget_summary,
            "created_master_items": len(masters),
            "created_projects": len(projects),
            "created_project_items": len(item_records),
            "finalization_summary": finalization_summary,
            "supplier_summary": {
                "domestic_count": len(supplier_summary["domestic_supplier_ids"]),
                "foreign_count": len(supplier_summary["foreign_supplier_ids"]),
            },
            "procurement_summary": procurement_summary,
            "validation": validation_summary,
        }


async def mode_validate() -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        return {"mode": "validate", "validation": await _validate_dataset(db)}


async def mode_reset_and_create() -> Dict[str, Any]:
    reset_out = await mode_reset_domain_data()
    create_out = await mode_create()
    validate_out = await mode_validate()
    return {
        "mode": "reset-and-create",
        "reset": reset_out,
        "create": create_out,
        "validate": validate_out,
    }


async def main(mode: str) -> Dict[str, Any]:
    if mode == "plan":
        return await mode_plan()
    if mode == "reset-domain-data":
        return await mode_reset_domain_data()
    if mode == "create":
        return await mode_create()
    if mode == "validate":
        return await mode_validate()
    if mode == "cleanup":
        return await mode_cleanup()
    if mode == "reset-and-create":
        return await mode_reset_and_create()
    raise ValueError(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create deterministic UAT 1405 dataset")
    parser.add_argument(
        "--mode",
        choices=["plan", "reset-domain-data", "create", "validate", "cleanup", "reset-and-create"],
        default="plan",
    )
    args = parser.parse_args()
    output = asyncio.run(main(args.mode))
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
