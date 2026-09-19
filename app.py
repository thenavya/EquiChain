import streamlit as st
from google import genai
import json
import re

st.set_page_config(
    page_title="EquiChain",
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
# DEMO MERCHANTS
# ============================================================

DEMO_MERCHANTS = [
    {
        "name": "Asha Restaurant",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 20,
        "unit": "L",
        "urgency_hours": 24,
        "revenue": 5200,
        "confidence": 94
    },
    {
        "name": "Ravi Tiffins",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 30,
        "unit": "L",
        "urgency_hours": 36,
        "revenue": 6800,
        "confidence": 96
    },
    {
        "name": "Spice Corner",
        "location": "Zone 2",
        "product": "SUNFLOWER OIL",
        "quantity": 25,
        "unit": "L",
        "urgency_hours": 48,
        "revenue": 6100,
        "confidence": 93
    },
    {
        "name": "Green Bowl Cafe",
        "location": "Zone 1",
        "product": "SUNFLOWER OIL",
        "quantity": 20,
        "unit": "L",
        "urgency_hours": 30,
        "revenue": 5900,
        "confidence": 95
    }
]


# ============================================================
# SESSION STATE
# ============================================================

if "merchant_pool" not in st.session_state:
    st.session_state.merchant_pool = DEMO_MERCHANTS.copy()

if "last_extraction" not in st.session_state:
    st.session_state.last_extraction = None

if "last_added_message" not in st.session_state:
    st.session_state.last_added_message = ""

if "pool_created" not in st.session_state:
    st.session_state.pool_created = False

if "pool_id" not in st.session_state:
    st.session_state.pool_id = None


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
        "error_type": error_type
    }


# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_with_gemini(message):

    if not GEMINI_READY:
        return empty_extraction("client_unavailable")

    prompt = f"""
You are the intelligence engine of EquiChain.

EquiChain helps small businesses convert natural-language
business conversations into structured procurement demand.

Extract ONLY information explicitly present in the merchant message.

IMPORTANT:
- Do not invent missing values.
- Understand English, Hinglish and Hindi.
- Understand informal merchant language.
- Normalize equivalent product descriptions.
- "oil", "cooking oil", "sunflower oil",
  "sunflower cooking oil", "सूरजमुखी तेल"
  should normalize to SUNFLOWER OIL.
- If the merchant says "2 cans, each 10 litres",
  quantity = 20 and unit = L.
- Detect procurement intent when the merchant clearly
  indicates that stock needs to be purchased.
- Estimate urgency only when reasonably supported.
- Confidence should represent extraction confidence.
- If a field is not explicitly present, return null.

Return ONLY valid JSON.

Required fields:

{{
  "revenue": number or null,
  "expense": number or null,
  "product": string or null,
  "quantity": number or null,
  "unit": string or null,
  "urgency_hours": number or null,
  "procurement_intent": true or false,
  "normalized_product": string or null,
  "location_hint": string or null,
  "language": string,
  "confidence": number
}}

Merchant message:

{message}
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

        return result

    except Exception as e:

        error_message = str(e)

        if (
            "429" in error_message
            or "Rate limit exceeded" in error_message
            or "quota" in error_message.lower()
        ):

            st.warning(
                "Gemini API quota has been reached for the "
                "current Free Tier limit. New AI extraction "
                "requests are temporarily paused."
            )

            return empty_extraction("rate_limit")

        st.error(
            f"Gemini extraction error: {error_message}"
        )

        return empty_extraction("extraction_error")


# ============================================================
# EQUISCORE
# ============================================================

def calculate_equiscore(
    merchant_pool,
    last_extraction
):

    merchant_count = len(merchant_pool)

    revenues = [
        float(m.get("revenue", 0))
        for m in merchant_pool
        if m.get("revenue") is not None
    ]

    if revenues:

        avg_revenue = sum(revenues) / len(revenues)

        if avg_revenue >= 7000:
            revenue_score = 100
        elif avg_revenue >= 5000:
            revenue_score = 90
        elif avg_revenue >= 3000:
            revenue_score = 75
        elif avg_revenue > 0:
            revenue_score = 60
        else:
            revenue_score = 40

    else:
        revenue_score = 40


    if merchant_count >= 9:
        transaction_score = 95
    elif merchant_count >= 7:
        transaction_score = 90
    elif merchant_count >= 5:
        transaction_score = 82
    elif merchant_count >= 3:
        transaction_score = 72
    elif merchant_count >= 1:
        transaction_score = 60
    else:
        transaction_score = 40


    if merchant_count >= 9:
        procurement_reliability = 95
    elif merchant_count >= 7:
        procurement_reliability = 88
    elif merchant_count >= 5:
        procurement_reliability = 80
    elif merchant_count >= 3:
        procurement_reliability = 70
    elif merchant_count >= 1:
        procurement_reliability = 55
    else:
        procurement_reliability = 40


    total_quantity = sum(
        float(m.get("quantity", 0))
        for m in merchant_pool
        if m.get("quantity") is not None
    )

    if total_quantity >= 200:
        procurement_activity = 100
    elif total_quantity >= 150:
        procurement_activity = 95
    elif total_quantity >= 100:
        procurement_activity = 88
    elif total_quantity >= 75:
        procurement_activity = 80
    elif total_quantity >= 50:
        procurement_activity = 70
    elif total_quantity > 0:
        procurement_activity = 55
    else:
        procurement_activity = 40


    if merchant_count >= 9:
        activity_history = 95
    elif merchant_count >= 7:
        activity_history = 90
    elif merchant_count >= 5:
        activity_history = 82
    elif merchant_count >= 3:
        activity_history = 72
    elif merchant_count >= 1:
        activity_history = 60
    else:
        activity_history = 40


    confidence_values = [
        float(m.get("confidence"))
        for m in merchant_pool
        if m.get("confidence") is not None
    ]

    if confidence_values:

        data_confidence = (
            sum(confidence_values)
            / len(confidence_values)
        )

    elif (
        last_extraction
        and last_extraction.get("confidence") is not None
    ):

        data_confidence = float(
            last_extraction.get("confidence")
        )

    else:
        data_confidence = 50


    overall_score = (
        revenue_score * 0.20
        + transaction_score * 0.15
        + procurement_reliability * 0.10
        + procurement_activity * 0.20
        + activity_history * 0.15
        + data_confidence * 0.20
    )

    return {
        "overall": round(clamp(overall_score)),
        "revenue_consistency": round(revenue_score),
        "transaction_regularity": round(transaction_score),
        "procurement_reliability": round(
            procurement_reliability
        ),
        "procurement_activity": round(
            procurement_activity
        ),
        "business_activity_history": round(
            activity_history
        ),
        "data_confidence": round(
            data_confidence
        )
    }


# ============================================================
# HEADER
# ============================================================

st.title("♾️ EquiChain")

st.subheader(
    "Collective Buying Power for Small Businesses"
)

st.write(
    "Turn everyday merchant conversations into structured "
    "demand — then turn fragmented demand into collective "
    "purchasing power."
)


# ============================================================
# NETWORK SNAPSHOT
# ============================================================

merchant_pool = st.session_state.merchant_pool

snapshot_count = len(merchant_pool)

snapshot_quantity = sum(
    float(m.get("quantity", 0))
    for m in merchant_pool
)

snapshot_product = (
    merchant_pool[-1].get("product")
    if merchant_pool
    else "—"
)

st.markdown("### Network Snapshot")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Merchant Network",
        snapshot_count
    )

with c2:
    st.metric(
        "Collective Demand",
        f"{snapshot_quantity:g} L"
    )

with c3:
    st.metric(
        "Tracked Product",
        snapshot_product
    )


# ============================================================
# MERCHANT ACTIVITY
# ============================================================

st.divider()

st.caption("01 — CAPTURE")

st.header("Merchant Activity")

business_name = st.text_input(
    "Business Name",
    placeholder="e.g. Royal Spice Kitchen"
)

location = st.text_input(
    "Location / Zone",
    placeholder="e.g. Zone 2"
)

merchant_message = st.text_area(
    "Tell EquiChain what happened today",
    placeholder=(
        "Example: Bhai oil almost khatam hai. "
        "Kal subah tak 2 cans chahiye, each 10 litre. "
        "Today sales were ₹5200."
    ),
    height=130
)

if st.button(
    "🤖 Analyze with Gemini",
    type="primary",
    use_container_width=True
):

    if not business_name.strip():

        st.warning(
            "Please enter the business name."
        )

    elif not merchant_message.strip():

        st.warning(
            "Please enter merchant activity."
        )

    else:

        extraction = extract_with_gemini(
            merchant_message
        )

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

        confidence = extraction.get(
            "confidence"
        )

        duplicate = (
            st.session_state.last_added_message
            == merchant_message.strip()
        )

        if (
            product
            and quantity
            and procurement_intent
            and not duplicate
        ):

            new_merchant = {
                "name": business_name.strip(),

                "location": (
                    location.strip()
                    if location.strip()
                    else "Unknown Zone"
                ),

                "product": product,

                "quantity": float(quantity),

                "unit": extraction.get(
                    "unit",
                    "L"
                ),

                "urgency_hours": extraction.get(
                    "urgency_hours"
                ),

                "revenue": extraction.get(
                    "revenue"
                ),

                "confidence": confidence
            }

            st.session_state.merchant_pool.append(
                new_merchant
            )

            st.session_state.last_added_message = (
                merchant_message.strip()
            )

            st.session_state.pool_created = False
            st.session_state.pool_id = None

            st.success(
                f"{business_name} added to the merchant network."
            )

        elif extraction.get("error_type") == "rate_limit":

            st.info(
                "The existing demo network remains available. "
                "AI extraction will resume when the Gemini quota resets."
            )


# ============================================================
# GEMINI UNDERSTANDING
# ============================================================

if st.session_state.last_extraction:

    extraction = st.session_state.last_extraction

    st.divider()

    st.caption("02 — UNDERSTAND")

    st.header("Gemini Understanding")

    revenue = extraction.get("revenue")

    revenue_display = (
        f"₹{float(revenue):,.0f}"
        if revenue is not None
        else "—"
    )

    quantity = extraction.get("quantity")

    demand_display = (
        f"{float(quantity):g} "
        f"{extraction.get('unit', '')}"
        if quantity is not None
        else "—"
    )

    confidence = extraction.get(
        "confidence"
    )

    if confidence is None:
        confidence_display = "—"
    else:
        confidence_display = (
            f"{float(confidence):.0f}%"
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
            "AI Confidence",
            confidence_display
        )

    st.caption(
        f"Language detected: "
        f"{extraction.get('language', 'unknown')}"
    )

    if extraction.get("error_type") == "rate_limit":

        st.warning(
            "Gemini is temporarily unavailable because "
            "the current API quota has been reached."
        )


# ============================================================
# CURRENT PRODUCT
# ============================================================

merchant_pool = st.session_state.merchant_pool

current_product = None

if st.session_state.last_extraction:

    current_product = (
        st.session_state.last_extraction.get(
            "normalized_product"
        )
    )

if not current_product and merchant_pool:

    current_product = merchant_pool[-1].get(
        "product"
    )


# ============================================================
# MATCHING MERCHANTS
# ============================================================

matching_merchants = []

if current_product:

    matching_merchants = [
        merchant
        for merchant in merchant_pool
        if merchant.get("product")
        == current_product
    ]

matching_count = len(
    matching_merchants
)

total_quantity = sum(
    float(m.get("quantity", 0))
    for m in matching_merchants
)


# ============================================================
# POOLSCORE
# ============================================================

participation_score = min(
    25,
    matching_count * 5
)

volume_score = min(
    30,
    (total_quantity / 100) * 30
)

consistency_score = min(
    20,
    matching_count * 4
)

urgencies = [
    float(m.get("urgency_hours"))
    for m in matching_merchants
    if m.get("urgency_hours") is not None
]

if urgencies:

    average_urgency = (
        sum(urgencies)
        / len(urgencies)
    )

    if average_urgency <= 24:
        urgency_score = 15
    elif average_urgency <= 36:
        urgency_score = 12
    elif average_urgency <= 48:
        urgency_score = 9
    elif average_urgency <= 72:
        urgency_score = 6
    else:
        urgency_score = 3

else:
    urgency_score = 0


geographic_score = (
    10
    if any(
        m.get("location")
        for m in matching_merchants
    )
    else 0
)

pool_score = min(
    100,
    round(
        participation_score
        + volume_score
        + consistency_score
        + urgency_score
        + geographic_score
    )
)


# ============================================================
# COLLECTIVE DEMAND
# ============================================================

st.divider()

st.caption("03 — AGGREGATE")

st.header("Collective Demand Pool")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Matching Merchants",
        matching_count
    )

with c2:
    st.metric(
        "Aggregated Demand",
        f"{total_quantity:g} L"
    )

with c3:
    st.metric(
        "PoolScore",
        f"{pool_score}/100"
    )


# ============================================================
# MERCHANT NETWORK
# ============================================================

st.subheader("Merchant Network")

if matching_merchants:

    network_columns = st.columns(
        min(4, len(matching_merchants))
    )

    for index, merchant in enumerate(
        matching_merchants
    ):

        with network_columns[
            index % len(network_columns)
        ]:

            st.info(
                f"**{merchant.get('name', 'Merchant')}**\n\n"
                f"📍 {merchant.get('location', 'Unknown Zone')}\n\n"
                f"🛢️ {float(merchant.get('quantity', 0)):g} "
                f"{merchant.get('unit', 'L')}"
            )

else:

    st.info(
        "Merchant demand will appear here after "
        "matching activity is detected."
    )


# ============================================================
# PROCUREMENT OPPORTUNITY
# ============================================================

st.divider()

st.caption("04 — ACT")

st.header("Procurement Opportunity")

if current_product and matching_count >= 2:

    average_demand = (
        total_quantity
        / matching_count
    )

    if pool_score >= 75:
        opportunity = "HIGH"
    elif pool_score >= 40:
        opportunity = "MEDIUM"
    else:
        opportunity = "WATCH"

    st.success(
        f"EquiChain detected a collective procurement "
        f"opportunity: {total_quantity:g} L of "
        f"{current_product} across "
        f"{matching_count} merchants."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Average Merchant Demand",
            f"{average_demand:.1f} L"
        )

    with c2:
        st.metric(
            "Collective Demand",
            f"{total_quantity:g} L"
        )

    with c3:
        st.metric(
            "Buying Opportunity",
            opportunity
        )

    if st.button(
        "🛒 Create Procurement Pool",
        use_container_width=True
    ):

        product_code = (
            current_product[:4].upper()
            if current_product
            else "POOL"
        )

        st.session_state.pool_id = (
            f"EC-{product_code}-"
            f"{matching_count:02d}-"
            f"{int(total_quantity):03d}"
        )

        st.session_state.pool_created = True

    if st.session_state.pool_created:

        st.success(
            "Procurement pool created successfully."
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Pool ID",
                st.session_state.pool_id
            )

        with c2:
            st.metric(
                "Pool Status",
                "OPEN"
            )

        st.caption(
            "Awaiting supplier quotes."
        )

else:

    st.info(
        "EquiChain is waiting for at least two "
        "merchants with matching procurement demand."
    )


# ============================================================
# PRICE INTELLIGENCE
# ============================================================

st.divider()

st.caption("05 — PRICE INTELLIGENCE")

st.header("Price Intelligence")

if current_product and matching_count >= 2:

    benchmark_price = 116
    supplier_quote = 113

    price_difference = (
        benchmark_price
        - supplier_quote
    )

    modeled_saving = (
        price_difference
        * total_quantity
    )

    st.caption(
        "Supplier intelligence shown below is simulated "
        "for the MVP demonstration."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Benchmark",
            f"₹{benchmark_price}/L"
        )

    with c2:
        st.metric(
            "Supplier Quote",
            f"₹{supplier_quote}/L"
        )

    with c3:
        st.metric(
            "Potential Difference",
            f"₹{price_difference}/L"
        )

    st.info(
        f"At {total_quantity:g} L, the modeled "
        f"price difference is ₹{modeled_saving:,.0f}."
    )

else:

    st.info(
        "Price intelligence becomes available when "
        "a collective procurement opportunity is detected."
    )


# ============================================================
# EQUISCORE
# ============================================================

equiscore = calculate_equiscore(
    merchant_pool,
    st.session_state.last_extraction
)

st.divider()

st.caption("06 — BUSINESS INTELLIGENCE")

st.header("EquiScore")

c1, c2 = st.columns([1, 2])

with c1:

    st.metric(
        "Overall EquiScore",
        f"{equiscore['overall']}/100"
    )

    st.caption(
        "Explainable business activity profile"
    )

with c2:

    score_items = [
        (
            "Revenue Consistency",
            equiscore["revenue_consistency"]
        ),
        (
            "Transaction Regularity",
            equiscore["transaction_regularity"]
        ),
        (
            "Procurement Reliability",
            equiscore["procurement_reliability"]
        ),
        (
            "Procurement Activity",
            equiscore["procurement_activity"]
        ),
        (
            "Business Activity History",
            equiscore["business_activity_history"]
        ),
        (
            "Data Confidence",
            equiscore["data_confidence"]
        )
    ]

    for label, score in score_items:

        st.write(
            f"**{label}** — {score}/100"
        )

        st.progress(
            score / 100
        )

st.caption(
    "EquiScore is an explainable business-activity "
    "profile for the MVP. It is not a credit score "
    "and does not make lending decisions."
)


# ============================================================
# EQUIPULSE
# ============================================================

st.divider()

st.caption("07 — NETWORK INTELLIGENCE")

st.header("EquiPulse")

business_activity = (
    "ACTIVE"
    if merchant_pool
    else "WAITING"
)

if (
    current_product
    and matching_count >= 2
    and total_quantity >= 75
):

    procurement_signal = "HIGH"

elif (
    current_product
    and matching_count >= 2
):

    procurement_signal = "MEDIUM"

elif current_product:

    procurement_signal = "WATCH"

else:

    procurement_signal = "NONE"


if matching_count >= 5:

    network_signal = (
        "Strong collective demand detected"
    )

elif matching_count >= 3:

    network_signal = (
        "Growing collective demand detected"
    )

elif matching_count >= 2:

    network_signal = (
        "Early collective demand detected"
    )

elif matching_count == 1:

    network_signal = (
        "Merchant demand detected — "
        "waiting for another matching business"
    )

else:

    network_signal = (
        "Waiting for merchant activity"
    )


pulse_cols = st.columns(5)

with pulse_cols[0]:
    st.metric(
        "Business Activity",
        business_activity
    )

with pulse_cols[1]:
    st.metric(
        "Network Demand",
        matching_count
    )

with pulse_cols[2]:
    st.metric(
        "Collective Demand",
        f"{total_quantity:g} L"
    )

with pulse_cols[3]:
    st.metric(
        "Procurement Signal",
        procurement_signal
    )

with pulse_cols[4]:
    st.metric(
        "PoolScore",
        f"{pool_score}/100"
    )

st.info(
    f"**Network Signal:** {network_signal}"
)

if current_product:

    st.success(
        f"EquiPulse is monitoring "
        f"{current_product} demand across "
        f"{matching_count} merchants."
    )


# ============================================================
# FLYWHEEL
# ============================================================

st.divider()

st.caption("SYSTEM")

st.header("The EquiChain Flywheel")

flywheel = [
    "Merchant Conversation",
    "Gemini Understanding",
    "Demand Normalization",
    "Demand Matching",
    "Collective Pool",
    "PoolScore",
    "Price Intelligence",
    "EquiScore",
    "EquiPulse"
]

st.write(
    "  →  ".join(flywheel)
)


# ============================================================
# DEMO CONTROLS
# ============================================================

st.divider()

with st.expander("⚙️ Demo Controls"):

    st.caption(
        "Reset the network to the original 4-merchant demo state."
    )

    if st.button(
        "🔄 Reset Demo Network",
        use_container_width=True
    ):

        st.session_state.merchant_pool = (
            DEMO_MERCHANTS.copy()
        )

        st.session_state.last_extraction = None
        st.session_state.last_added_message = ""
        st.session_state.pool_created = False
        st.session_state.pool_id = None

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "♾️ EquiChain — Make the invisible economy visible."
)
