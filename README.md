# ♾️ EquiChain

### Collective Buying Power for Small Businesses

> EquiChain turns everyday merchant conversations into structured demand—and fragmented demand into collective purchasing power.

---

## 🚀 What is EquiChain?

Small businesses often purchase supplies individually, even when nearby businesses need the same products around the same time.

EquiChain is an **AI-powered coordination layer for small businesses**.

Instead of forcing merchants to fill complex forms, merchants can simply describe their business activity in natural language.

For example:

> "Bhai oil almost khatam hai. Kal subah tak 20 litres chahiye. Aaj sales ₹5,200 hui."

EquiChain uses **Google Gemini** to understand the conversation, extract structured information, normalize the demand, and identify opportunities to combine demand across merchants.

---

## 💡 The Problem

Small businesses frequently manage important operational information through:

* WhatsApp conversations
* Informal notes
* Memory
* Receipts
* Spreadsheets
* Multiple languages
* Unstructured messages

This creates fragmented demand.

For example:

| Merchant              |       Requirement |
| --------------------- | ----------------: |
| Restaurant A          | 20L sunflower oil |
| Restaurant B          | 30L sunflower oil |
| Restaurant C          | 25L sunflower oil |
| Restaurant D          | 20L sunflower oil |
| **Collective demand** |           **95L** |

Individually, each merchant has limited purchasing power.

Collectively, they represent a stronger procurement opportunity.

---

## 🧠 How EquiChain Works

```text
Merchant Conversation
        ↓
Gemini Understanding
        ↓
Demand Extraction
        ↓
Demand Normalization
        ↓
Demand Matching
        ↓
Collective Pool
        ↓
PoolScore
        ↓
Price Intelligence
        ↓
EquiScore
        ↓
EquiPulse
```

### 1. Merchant Conversation

A merchant describes their business activity naturally.

Example:

> "Sunflower oil 30 litres chahiye kal. Aaj sales 6800 hue."

### 2. Gemini Understanding

Gemini identifies structured information such as:

* Product
* Quantity
* Unit
* Urgency
* Revenue
* Inventory need
* Confidence

### 3. Demand Normalization

Different expressions are converted into a common representation.

Examples:

```text
"Need 20 litres sunflower oil"
"2 cans oil, 10L each"
"सूरजमुखी तेल 20 लीटर चाहिए"
"Oil khatam, 20 litre chahiye"
```

can be normalized into:

```text
Product: SUNFLOWER OIL
Quantity: 20L
Urgency: High
```

### 4. Demand Matching

EquiChain looks for merchants with compatible demand.

### 5. Collective Pool

Matching demand is aggregated into a procurement opportunity.

Example:

```text
20L + 30L + 25L + 20L = 95L
```

### 6. PoolScore

PoolScore estimates how actionable a collective procurement opportunity is using signals such as:

* Merchant participation
* Demand volume
* Demand consistency
* Urgency
* Geographic fit

### 7. Price Intelligence

The MVP compares a benchmark price with a supplier quote to show potential procurement value.

> Current supplier data in the MVP is simulated and clearly labeled.

### 8. EquiScore

EquiScore is an **explainable business activity score**.

It is **not a credit score** and is not used to make lending decisions.

It uses activity signals such as:

* Revenue consistency
* Transaction regularity
* Procurement reliability
* Procurement activity
* Business activity history
* Data confidence

### 9. EquiPulse

EquiPulse combines the merchant's own business activity with network-level demand signals.

---

## ✨ Key Features

### 🤖 AI-Powered Natural Language Input

Merchants don't need to learn a complicated procurement form.

They can simply describe what they need.

### 🌐 Multilingual Understanding

EquiChain can interpret different ways merchants express the same requirement, including English, Hinglish, and Hindi.

### 🔗 Collective Demand Aggregation

Individual requirements are combined into larger procurement opportunities.

### 📊 PoolScore

A transparent score helps identify stronger procurement opportunities.

### 💰 Price Intelligence

The MVP compares benchmark and supplier pricing to estimate potential procurement value.

### 📈 EquiScore

An explainable business activity profile based on observed activity.

### 📡 EquiPulse

A combined view of business activity and network demand.

---

## 🛠️ Tech Stack

| Technology       | Purpose                                       |
| ---------------- | --------------------------------------------- |
| Python           | Application logic                             |
| Streamlit        | Web application                               |
| Google Gemini    | Natural-language understanding and extraction |
| Google GenAI SDK | Gemini API integration                        |

---

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/thenavya/EquiChain.git
cd EquiChain
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your Gemini API key

Set your Gemini API key as an environment variable.

**Do not commit your API key to GitHub.**

### 5. Run the application

```bash
streamlit run app.py
```

The application will open locally in your browser.

---

## 🔐 Security

API credentials should never be committed to the repository.

The `.gitignore` file excludes:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

## 🎯 Why This Matters

Small businesses may be individually fragmented, but their combined demand can be significant.

EquiChain aims to create a coordination layer that makes previously invisible demand measurable and actionable.

The procurement use case is the initial wedge.

As merchants repeatedly use the system, EquiChain can build richer structured business activity data that may support future products and services.

---

## 🔄 The EquiChain Flywheel

```text
More Merchant Conversations
          ↓
More Structured Demand
          ↓
Better Demand Matching
          ↓
Larger Procurement Pools
          ↓
Greater Merchant Value
          ↓
More Merchant Participation
          ↓
More Structured Demand
```

---

## ⚠️ MVP Scope

The current prototype focuses on:

* Natural-language merchant input
* Gemini-powered extraction
* Demand normalization
* Demand matching
* Collective demand aggregation
* PoolScore
* Price Intelligence
* EquiScore
* EquiPulse

The current MVP does **not** implement:

* Actual lending
* Credit decisions
* Blockchain infrastructure
* Escrow
* A production supplier marketplace
* Production voice infrastructure
* Advanced geospatial optimization
* Complex machine-learning forecasting

These are intentionally outside the current MVP scope.

---

## 🌱 Future Direction

Potential future development includes:

* Real supplier integrations
* Live supplier quotations
* Automated procurement workflows
* Supplier discovery
* Geographic demand clustering
* Recurring procurement prediction
* Business analytics
* Additional languages
* WhatsApp-based merchant interaction
* More sophisticated demand forecasting

---

## 🧩 Project Vision

> **Make the invisible economy visible.**

EquiChain aims to transform fragmented merchant activity into structured collective intelligence—starting with procurement.

---

## 👩‍💻 Built By

**Navya**

GitHub: https://github.com/thenavya

---

## 📄 License

This project is currently a prototype created for hackathon and innovation purposes.
