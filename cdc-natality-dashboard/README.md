# CDC Provisional Natality Dashboard (2025)

An interactive Streamlit analytics dashboard designed for undergraduate business analytics students to explore geographic, monthly, and sex-based differences in provisional US birth counts.

## Directory Structure
```
├── app.py                      # Main application orchestrator
├── requirements.txt            # Python dependencies
├── README.md
├── data/
│   └── Provisional_Natality_2025_CDC1.csv  # 2025 Natality Dataset
└── src/
    ├── __init__.py
    ├── components.py           # Header, KPIs, and sidebar state controls
    ├── data_loader.py          # Data ingestion, caching, and validation
    └── visuals.py              # Accessible Plotly visualizations
```

## Setup & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```
