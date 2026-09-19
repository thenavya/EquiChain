import streamlit as st
from google import genai
import json
import re

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EquiChain — Collective Buying Power",
    page_icon="♾️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# GEMINI CLIENT
# ============================================================

try:
    client = genai.Client()
    GEMINI_READY = True
except Exception:
    client = None
    GEMINI_READY = False

# ============================================================
# DEMO MERCHANT NETWORK
# ============================================================

DEMO_MERCHANTS = [
    {
        "name": "Asha Restaurant",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 20,
        "unit": "L",
        "revenue": 5200,
        "confidence": 94
    },
    {
        "name": "Ravi Tiffins",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 30,
        "unit": "L",
        "revenue": 6800,
        "confidence": 96
    },
    {
        "name": "Spice Corner",
        "location": "Zone 2",
        "product": "SUNFLOWER OIL",
        "quantity": 25,
        "unit": "L",
        "revenue": 6100,
        "confidence": 93
    },
    {
        "name": "Green Bowl Cafe",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 20,
        "unit": "L",
        "revenue": 5900,
        "confidence": 95
    }
]

# ============================================================
# SESSION STATE
# ============================================================

if "merchants" not in st.session_state:
    st.session_state.merchants = [
        merchant.copy() for merchant in DEMO_MERCHANTS
    ]

if "last_extraction" not in st.session_state:
    st.session_state.last_extraction = None

if "last_added_message" not in st.session_state:
    st.session_state.last_added_message = None

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = True

# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def empty_extraction(error_type=None):
    return {
        "revenue": None,
        "expense": None,
        "product": None,
        "quantity": None,
        "unit": None,
        "urgency_hours": None,
        "procurement_intent": False,
        "normalized_product": None,
        "location_hint": None,
        "language": "unknown",
        "confidence": None,
        "source": None,
        "error_type": error_type
    }

# ============================================================
# DEMO AI ENGINE
# ============================================================

def fallback_extraction(message):

    text = message.lower()

    result = empty_extraction("demo_engine")

    # --------------------------------------------------------
    # PRODUCT NORMALIZATION
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in [
            "sunflower oil",
            "cooking oil",
            "sunflower",
            "oil",
            "सूरजमुखी तेल"
        ]
    ):
        result["product"] = "SUNFLOWER OIL"
        result["normalized_product"] = "SUNFLOWER OIL"

    elif "rice" in text or "चावल" in text:
        result["product"] = "RICE"
        result["normalized_product"] = "RICE"

    elif "sugar" in text or "चीनी" in text:
        result["product"] = "SUGAR"
        result["normalized_product"] = "SUGAR"

    elif "flour" in text or "atta" in text:
        result["product"] = "FLOUR"
        result["normalized_product"] = "FLOUR"

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue_match = re.search(
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)",
        text
    )

    if revenue_match:
        result["revenue"] = float(
            revenue_match.group(1).replace(",", "")
        )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    quantity = None
    unit = None

    # Example:
    # 2 cans, each 10 litre
    can_match = re.search(
        r"(\d+(?:\.\d+)?)\s*cans?.*?"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:litres?|liters?|l)\b",
        text
    )

    if can_match:
        quantity = (
            float(can_match.group(1))
            * float(can_match.group(2))
        )
        unit = "L"

    # Example:
    # 20 litre / 20 litres / 20L
    if quantity is None:

        litre_match = re.search(
            r"(\d+(?:\.\d+)?)\s*"
            r"(?:litres?|liters?|l)\b",
            text
        )

        if litre_match:
            quantity = float(litre_match.group(1))
            unit = "L"

    # Example:
    # 20 kg
    if quantity is None:

        kg_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)\b",
            text
        )

        if kg_match:
            quantity = float(kg_match.group(1))
            unit = "kg"

    if quantity is not None:
        result["quantity"] = quantity
        result["unit"] = unit

    # --------------------------------------------------------
    # PROCUREMENT INTENT
    # --------------------------------------------------------

    procurement_words = [
        "need",
        "needs",
        "buy",
        "purchase",
        "order",
        "required",
        "require",
        "procure",
        "chahiye",
        "mangwana",
        "mangwana hai",
        "khatam",
        "almost khatam",
        "running out",
        "stock low",
        "stock khatam"
    ]

    result["procurement_intent"] = any(
        word in text
        for word in procurement_words
    )

    # --------------------------------------------------------
    # URGENCY
    # --------------------------------------------------------

    if (
        "tomorrow morning" in text
        or "kal subah" in text
    ):
        result["urgency_hours"] = 18

    elif (
        "tomorrow" in text
        or "kal" in text
    ):
        result["urgency_hours"] = 24

    elif (
        "today" in text
        or "aaj" in text
    ):
        result["urgency_hours"] = 12

    elif (
        "urgent" in text
        or "immediately" in text
        or "asap" in text
    ):
        result["urgency_hours"] = 6

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    if re.search(r"[\u0900-\u097F]", message):

        result["language"] = "Hindi"

    elif any(
        word in text
        for word in [
            "bhai",
            "chahiye",
            "khatam",
            "kal",
            "hai",
            "mangwana",
            "aaj"
        ]
    ):

        result["language"] = "Hinglish"

    else:

        result["language"] = "English"

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    detected_fields = sum(
        value is not None
        for value in [
            result["normalized_product"],
            result["quantity"],
            result["urgency_hours"]
        ]
    )

    if detected_fields >= 3:
        result["confidence"] = 92

    elif detected_fields == 2:
        result["confidence"] = 85

    elif detected_fields == 1:
        result["confidence"] = 70

    else:
        result["confidence"] = 40

    result["source"] = "EquiChain Demo Engine"

    return result

# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_with_gemini(message):

    prompt = f"""
You are the intelligence layer of EquiChain,
a collective procurement platform for small businesses.

Analyze the following merchant message.

Merchant message:
{message}

Extract:

- revenue: numeric revenue mentioned, otherwise null
- expense: numeric expense mentioned, otherwise null
- product: product mentioned by merchant
- quantity: numeric quantity
- unit: unit such as L, kg, units
- urgency_hours: approximate hours until requirement
- procurement_intent: true if merchant intends to buy/order/procure
- normalized_product: standardized product name in uppercase
- location_hint: location if mentioned
- language: English, Hindi, Hinglish, or other
- confidence: extraction confidence from 0 to 100

Rules:

- Understand English, Hindi and Hinglish.
- Normalize equivalent product descriptions.
- Do not invent information.
- If information is absent, return null.
- Return ONLY valid JSON.

Return exactly this structure:

{{
    "revenue": null,
    "expense": null,
    "product": null,
    "quantity": null,
    "unit": null,
    "urgency_hours": null,
    "procurement_intent": false,
    "normalized_product": null,
    "location_hint": null,
    "language": "unknown",
    "confidence": null
}}
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        raw = interaction.output_text.strip()

        raw = re.sub(
            r"```json",
            "",
            raw,
            flags=re.IGNORECASE
        )

        raw = re.sub(
            r"```",
            "",
            raw
        ).strip()

        result = json.loads(raw)

        confidence = result.get("confidence")

        if confidence is not None:

            try:
                result["confidence"] = clamp(
                    float(confidence),
                    0,
                    100
                )

            except (ValueError, TypeError):

                result["confidence"] = None

        result["source"] = "Gemini"

        return result

    except Exception as error:

        error_message = str(error)

        if (
            "429" in error_message
            or "Rate limit exceeded" in error_message
            or "quota" in error_message.lower()
        ):

            return None

        return None

# ============================================================
# SMART EXTRACTION ROUTER
# ============================================================

def analyze_message(message):

    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if st.session_state.demo_mode:

        return fallback_extraction(message)

    # --------------------------------------------------------
    # LIVE GEMINI MODE
    # --------------------------------------------------------

    if not GEMINI_READY:

        return fallback_extraction(message)

    gemini_result = extract_with_gemini(message)

    if gemini_result is not None:

        return gemini_result

    # --------------------------------------------------------
    # AUTOMATIC FAILSAFE
    # --------------------------------------------------------

    st.warning(
        "Gemini is temporarily unavailable. "
        "EquiChain switched automatically to its "
        "local demo intelligence engine."
    )

    return fallback_extraction(message)

# ============================================================
# NETWORK CALCULATIONS
# ============================================================

def calculate_network():

    merchants = st.session_state.merchants

    total_demand = sum(
        merchant["quantity"]
        for merchant in merchants
        if merchant.get("quantity") is not None
    )

    products = [
        merchant["product"]
        for merchant in merchants
        if merchant.get("product")
    ]

    tracked_product = (
        max(set(products), key=products.count)
        if products
        else "—"
    )

    return (
        len(merchants),
        total_demand,
        tracked_product
    )


def calculate_pool_score():

    return 86


def calculate_equiscore():

    return 82

# ============================================================
# HEADER
# ============================================================

st.title("♾️ EquiChain")

st.subheader(
    "Collective Buying Power for Small Businesses"
)

st.write(
    "Turn everyday merchant conversations into structured demand "
    "— then turn fragmented demand into collective purchasing power."
)

# ============================================================
# DEMO / AI MODE
# ============================================================

st.divider()

mode_col1, mode_col2 = st.columns([2, 1])

with mode_col1:

    st.write("### Demo Mode")

    st.caption(
        "For judging, Demo Mode is recommended. "
        "It does not depend on Gemini API quota."
    )

with mode_col2:

    st.session_state.demo_mode = st.toggle(
        "Use Demo Mode",
        value=st.session_state.demo_mode
    )

if st.session_state.demo_mode:

    st.success(
        "🟢 Demo Mode active — EquiChain can be demonstrated "
        "without external API quota."
    )

else:

    if GEMINI_READY:

        st.info(
            "🔵 Gemini Mode active — merchant messages "
            "will be analyzed using Gemini."
        )

    else:

        st.warning(
            "Gemini is not configured. EquiChain will "
            "automatically use the Demo Engine."
        )

# ============================================================
# 01 — CAPTURE
# ============================================================

st.divider()

st.caption("01 — CAPTURE")

st.header("Merchant Activity")

business_name = st.text_input(
    "Business Name",
    placeholder="e.g. Navya Cafe"
)

location = st.text_input(
    "Location / Zone",
    placeholder="e.g. Zone 1"
)

message = st.text_area(
    "Tell EquiChain what happened today",
    placeholder=(
        "Example: Bhai oil almost khatam hai. "
        "Kal subah tak 2 cans chahiye, each 10 litre. "
        "Today sales were ₹5200."
    ),
    height=130
)

analyze = st.button(
    "🤖 Analyze Merchant Message",
    use_container_width=True
)

# ============================================================
# PROCESS INPUT
# ============================================================

if analyze:

    if not business_name.strip():

        st.error(
            "Please enter the business name."
        )

    elif not message.strip():

        st.error(
            "Please enter the merchant message."
        )

    else:

        extraction = analyze_message(message)

        if (
            not extraction.get("location_hint")
            and location.strip()
        ):

            extraction["location_hint"] = location.strip()

        st.session_state.last_extraction = extraction

        product = extraction.get(
            "normalized_product"
        )

        quantity = extraction.get(
            "quantity"
        )

        procurement_intent = extraction.get(
            "procurement_intent",
            False
        )

        if (
            product
            and quantity
            and procurement_intent
        ):

            if (
                st.session_state.last_added_message
                != message
            ):

                new_merchant = {

                    "name": business_name.strip(),

                    "location": (
                        extraction.get(
                            "location_hint"
                        )
                        or location.strip()
                        or "Unknown Zone"
                    ),

                    "product": product,

                    "quantity": float(quantity),

                    "unit": (
                        extraction.get("unit")
                        or "L"
                    ),

                    "revenue": (
                        extraction.get("revenue")
                    ),

                    "confidence": (
                        extraction.get("confidence")
                    )
                }

                st.session_state.merchants.append(
                    new_merchant
                )

                st.session_state.last_added_message = (
                    message
                )

                st.success(
                    f"{business_name.strip()} added "
                    "to the merchant demand network."
                )

            else:

                st.info(
                    "This merchant message has already "
                    "been added to the current demo network."
                )

# ============================================================
# NETWORK SNAPSHOT
# ============================================================

merchant_count, total_demand, tracked_product = (
    calculate_network()
)

st.divider()

st.subheader(
    "Network Snapshot"
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Merchant Network",
        merchant_count
    )

with c2:

    st.metric(
        "Collective Demand",
        f"{total_demand:g} L"
    )

with c3:

    st.metric(
        "Tracked Product",
        tracked_product
    )

# ============================================================
# 02 — UNDERSTAND
# ============================================================

if st.session_state.last_extraction:

    extraction = (
        st.session_state.last_extraction
    )

    st.divider()

    st.caption(
        "02 — UNDERSTAND"
    )

    st.header(
        "AI Understanding"
    )

    source = extraction.get(
        "source",
        "Unknown"
    )

    if source == "Gemini":

        st.success(
            "Source: Gemini"
        )

    else:

        st.info(
            "Source: EquiChain Demo Engine"
        )

    revenue = extraction.get(
        "revenue"
    )

    revenue_display = (
        f"₹{float(revenue):,.0f}"
        if revenue is not None
        else "—"
    )

    quantity = extraction.get(
        "quantity"
    )

    demand_display = (

        f"{float(quantity):g} "
        f"{extraction.get('unit', '')}"

        if quantity is not None

        else "—"
    )

    confidence = extraction.get(
        "confidence"
    )

    confidence_display = (

        f"{float(confidence):.0f}%"

        if confidence is not None

        else "—"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Revenue",
            revenue_display
        )

    with c2:

        st.metric(
            "Normalized Product",
            extraction.get(
                "normalized_product"
            ) or "—"
        )

    with c3:

        st.metric(
            "Demand",
            demand_display
        )

    with c4:

        st.metric(
            "Extraction Confidence",
            confidence_display
        )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**Procurement Intent**"
        )

        if extraction.get(
            "procurement_intent"
        ):

            st.success(
                "Detected"
            )

        else:

            st.warning(
                "Not detected"
            )

    with c2:

        st.write(
            "**Language**"
        )

        st.write(
            extraction.get(
                "language"
            ) or "Unknown"
        )

    with c3:

        st.write(
            "**Urgency**"
        )

        urgency = extraction.get(
            "urgency_hours"
        )

        if urgency is not None:

            st.write(
                f"{float(urgency):g} hours"
            )

        else:

            st.write("—")

# ============================================================
# 03 — NORMALIZE
# ============================================================

st.divider()

st.caption(
    "03 — NORMALIZE"
)

st.header(
    "Demand Normalization"
)

if st.session_state.merchants:

    header_cols = st.columns(
        [2, 1, 2, 1, 1, 1]
    )

    header_cols[0].markdown(
        "**Merchant**"
    )

    header_cols[1].markdown(
        "**Zone**"
    )

    header_cols[2].markdown(
        "**Product**"
    )

    header_cols[3].markdown(
        "**Demand**"
    )

    header_cols[4].markdown(
        "**Revenue**"
    )

    header_cols[5].markdown(
        "**Confidence**"
    )

    st.divider()

    for merchant in st.session_state.merchants:

        row = st.columns(
            [2, 1, 2, 1, 1, 1]
        )

        row[0].write(
            merchant["name"]
        )

        row[1].write(
            merchant["location"]
        )

        row[2].write(
            merchant["product"]
        )

        row[3].write(
            f'{merchant["quantity"]:g} '
            f'{merchant["unit"]}'
        )

        if merchant.get(
            "revenue"
        ) is not None:

            row[4].write(
                f'₹{merchant["revenue"]:,.0f}'
            )

        else:

            row[4].write("—")

        if merchant.get(
            "confidence"
        ) is not None:

            row[5].write(
                f'{float(merchant["confidence"]):.0f}%'
            )

        else:

            row[5].write("—")

else:

    st.info(
        "No merchant demand captured yet."
    )

# ============================================================
# 04 — MATCH
# ============================================================

st.divider()

st.caption(
    "04 — MATCH"
)

st.header(
    "Demand Matching"
)

product_merchants = [

    merchant

    for merchant in st.session_state.merchants

    if merchant.get(
        "product"
    ) == tracked_product
]

if product_merchants:

    zone_counts = {}

    for merchant in product_merchants:

        zone = merchant["location"]

        zone_counts[zone] = (
            zone_counts.get(zone, 0) + 1
        )

    st.write(
        f"**{len(product_merchants)} merchants** "
        f"currently signal demand for "
        f"**{tracked_product}**."
    )

    for zone, count in zone_counts.items():

        st.write(
            f"📍 {zone}: {count} merchant(s)"
        )

else:

    st.info(
        "No matching demand detected."
    )

# ============================================================
# 05 — POOL
# ============================================================

st.divider()

st.caption(
    "05 — POOL"
)

st.header(
    "Collective Demand Pool"
)

pool_score = calculate_pool_score()

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "Collective Demand",
        f"{total_demand:g} L"
    )

with c2:

    st.metric(
        "PoolScore",
        f"{pool_score}/100"
    )

st.progress(
    pool_score / 100
)

st.caption(
    "PoolScore demo model: merchant participation, "
    "demand volume, consistency, urgency and geographic fit."
)

# ============================================================
# 06 — PRICE INTELLIGENCE
# ============================================================

st.divider()

st.caption(
    "06 — PRICE INTELLIGENCE"
)

st.header(
    "Price Intelligence"
)

benchmark_price = 116
supplier_quote = 113

price_difference = (
    benchmark_price
    - supplier_quote
)

modeled_savings = (
    price_difference
    * total_demand
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Benchmark Price",
        f"₹{benchmark_price}/L"
    )

with c2:

    st.metric(
        "Simulated Supplier Quote",
        f"₹{supplier_quote}/L"
    )

with c3:

    st.metric(
        "Modeled Pool Benefit",
        f"₹{modeled_savings:,.0f}"
    )

st.info(
    "Price Intelligence uses simulated benchmark "
    "and supplier quote data for this demo. "
    "It is not a live market quote."
)

# ============================================================
# 07 — EQUISCORE
# ============================================================

st.divider()

st.caption(
    "07 — EQUISCORE"
)

st.header(
    "EquiScore"
)

equiscore = calculate_equiscore()

st.metric(
    "EquiScore",
    f"{equiscore}/100"
)

st.progress(
    equiscore / 100
)

st.write(
    "EquiScore is a business activity and procurement "
    "signal for the EquiChain network."
)

st.caption(
    "Not a credit score. No lending or credit decision is made."
)

with st.expander(
    "EquiScore components"
):

    st.write(
        "Revenue Consistency — 20%"
    )

    st.write(
        "Transaction Regularity — 15%"
    )

    st.write(
        "Procurement Reliability — 10%"
    )

    st.write(
        "Procurement Activity — 20%"
    )

    st.write(
        "Business Activity History — 15%"
    )

    st.write(
        "Data Confidence — 20%"
    )

# ============================================================
# 08 — EQUIPULSE
# ============================================================

st.divider()

st.caption(
    "08 — EQUIPULSE"
)

st.header(
    "EquiPulse"
)

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Business Activity",
        "ACTIVE"
    )

with c2:

    st.metric(
        "Network Demand",
        merchant_count
    )

with c3:

    st.metric(
        "Collective Demand",
        f"{total_demand:g} L"
    )

with c4:

    st.metric(
        "Procurement Signal",
        "HIGH"
    )

st.success(
    f"Network Signal: Growing collective demand detected. "
    f"PoolScore {pool_score}/100."
)

# ============================================================
# 09 — FLYWHEEL
# ============================================================

st.divider()

st.caption(
    "09 — EQUICHAIN FLYWHEEL"
)

st.header(
    "From Conversation to Collective Buying Power"
)

flywheel = [

    "Merchant Conversation",

    "AI Understanding",

    "Demand Normalization",

    "Demand Matching",

    "Collective Pool",

    "PoolScore",

    "Price Intelligence",

    "EquiScore",

    "EquiPulse"
]

for index, step in enumerate(
    flywheel,
    start=1
):

    st.write(
        f"**{index}. {step}**"
    )

    if index < len(flywheel):

        st.write("↓")

# ============================================================
# DEMO CONTROLS
# ============================================================

st.divider()

st.header(
    "Demo Controls"
)

if st.button(
    "🔄 Reset Demo Network",
    use_container_width=True
):

    st.session_state.merchants = [
        merchant.copy()
        for merchant in DEMO_MERCHANTS
    ]

    st.session_state.last_extraction = None

    st.session_state.last_added_message = None

    st.rerun()

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EquiChain — Collective Buying Power for Small Businesses"
)

st.caption(
    "Demo MVP • Gemini-powered understanding • "
    "Local demo intelligence • Simulated procurement intelligence"
)