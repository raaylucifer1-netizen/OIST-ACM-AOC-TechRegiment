# 🇮🇳 Aaru India

> **AI-Powered Synthetic Consumer Research Platform for the Indian Market**

Aaru India is an AI-powered market research platform that enables companies to evaluate products before launch using permanent AI-generated Indian consumer personas instead of traditional surveys and focus groups.

The platform simulates realistic consumer opinions by leveraging thousands of synthetic Indian AI agents with fixed demographics, personalities, shopping behavior, and decision-making patterns.

---

# 📌 Problem Statement

Traditional market research is:

- Expensive
- Time-consuming
- Difficult for startups and MSMEs
- Limited by small survey sizes
- Often biased due to human response quality

Many Indian businesses cannot afford professional market research before launching products.

---

# 💡 Our Solution

Aaru India replaces traditional surveys with AI-powered synthetic Indian consumers.

Companies can submit a product, select their target audience, and receive detailed insights generated from thousands of AI personas.

Each AI persona has a permanent profile including:

- Age
- Gender
- City
- Occupation
- Income
- Shopping Behaviour
- Personality Traits
- Brand Loyalty
- Price Sensitivity
- Technology Adoption
- Communication Style

Every AI agent evaluates the product independently to generate unbiased market insights.

---

# 🚀 Features

- Permanent AI Consumer Personas
- AI Product Evaluation
- Synthetic Consumer Research
- Target Audience Filtering
- Product A vs Product B Comparison
- Natural AI Conversations
- Buying Intent Prediction
- Consumer Sentiment Analysis
- Feature Preference Analysis
- PDF Report Generation
- DOCX Report Generation
- English & Hindi Support (MVP)

---

# ⚙️ System Workflow

```
Company
        │
        ▼
Product Submission
        │
        ▼
Target Audience Selection
        │
        ▼
Synthetic Indian Persona Database
        │
        ▼
AI Conversation Engine
        │
        ▼
Analytics Engine
        │
        ▼
Report Generator
        │
        ▼
PDF / DOCX Report
```

---

# 🧠 AI Persona Engine

Every AI persona is permanent.

Example profile:

```
Name
Age
Gender
City
Income
Education
Occupation
Shopping Behaviour
Brand Loyalty
Price Sensitivity
Technology Adoption
Preferred Brands
Social Media Usage
Personality Traits
Communication Style
```

The same persona is reused across different projects while maintaining consistent behaviour.

---

# 🏗 Project Architecture

```
Frontend (Next.js)

        │

FastAPI Backend

        │

Authentication

        │

Persona Database

        │

Conversation Engine

        │

Analytics Engine

        │

Report Generator
```

---

# 🛠 Tech Stack

### Frontend

- Next.js
- React
- Tailwind CSS

### Backend

- FastAPI
- Python

### Database

- SQLite
- PostgreSQL

### AI

- Google Gemini
- Groq
- OpenRouter (Future)

### Reports

- ReportLab
- python-docx

---

# 📂 Folder Structure

```
backend/
frontend/
Personas/
docs/
reports/
assets/
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/raaylucifer1-netizen/OIST-ACM-AOC-TechRegiment.git
```

## Move into Project

```bash
cd OIST-ACM-AOC-TechRegiment
```

## Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file and add your API keys:

```env
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
JWT_SECRET=your_secret
```

Run Backend

```bash
uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:3000
```

---

# 📊 Current MVP

- User Authentication
- Product Submission
- Persona Database
- AI Conversation Engine
- Consumer Simulation
- Analytics
- Report Generation

---

# 🔮 Future Scope

- Multi-language Support
- Advertisement Testing
- Packaging Testing
- Brand Perception Analysis
- Pricing Optimization
- Political Opinion Simulation
- Public Policy Research
- Market Trend Prediction

---

# 👨‍💻 Contributors

**Ravikant Upadhyay**

B.Tech CSE (AI & ML)

Oriental Institute of Science and Technology

---

# 📄 License

This project is intended for educational, research, and innovation purposes.

---

# ⭐ Vision

To build India's first AI-powered synthetic consumer research platform that enables startups, businesses, and organizations to validate ideas, products, and decisions before entering the market using realistic AI-generated Indian consumer personas.
