# ANTORDRISHTI

**A Robust Framework for Image Forgery Detection in Questioned Document Analysis**

---

## Overview

Antordrishti is a professional standalone desktop forensic application for questioned document analysis and image forgery detection. Built as a true Windows desktop application using Python and PyQt5.

## Current Stage: UI / Desktop Application

This is the **frontend-only** implementation. The forensic analysis backend, machine learning models, OCR engines, and database layer are **not yet implemented**.

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| UI Framework | PyQt5 5.15+ |
| Styling | QSS (centralized theme) |
| PDF Rendering | PyMuPDF 1.23+ |
| Image Support | Pillow 10.0+ |
| Icons | qtawesome 1.3+ |

## Installation

```bash
# Navigate to the project
cd antordrishti

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Project Architecture

```
antordrishti/
├── main.py                  # Entry point
├── app/                     # Application core (theme, constants, resources)
├── ui/                      # UI components
│   ├── main_window.py       # Main window orchestrator
│   ├── menu_bar.py          # Complete menu system (10 menus)
│   ├── toolbar.py           # Main toolbar
│   ├── status_bar.py        # Status bar
│   ├── navigation/          # Left sidebar
│   ├── viewer/              # Document viewer, tools, layers
│   ├── inspector/           # Right inspector panels
│   ├── pages/               # All workspace pages (15+)
│   ├── dialogs/             # Professional dialogs
│   └── widgets/             # Reusable widget library
├── models/                  # Data models (case, document, evidence, finding)
├── services/                # File, document, hash services
├── engines/                 # Stub analysis engines
└── styles/                  # QSS stylesheet
```

## Implemented UI Modules

- **Dashboard** — Quick actions, system status, recent items
- **Document Analysis** — Full document viewer with zoom, pan, rotate, layers
- **Error Level Analysis (ELA)** — Controls and visualization workspace
- **Metadata Sanitization** — Tabbed metadata tables with actions
- **OCR & Text Extraction** — Language/mode selection, results area
- **Watermark Detection** — Type selection, detection actions
- **Image Forensics** — 6 tabbed analysis categories
- **Document Forensics** — 7 tabbed analysis categories
- **Source Camera Analysis** — Camera info and sensor analysis
- **Noise Pattern Analysis** — Extraction, statistics, region comparison
- **Forgery Detection** — Passive (5 types) and Active (2 types)
- **Illumination Analysis** — Light direction and consistency
- **Evidence Manager** — Evidence table with context menus
- **Evidence Fusion** — Combined analysis assessment
- **Report Generator** — Professional report preview
- **Batch Processing** — File table with progress tracking
- **Settings** — 8 configuration tabs

## Backend Modules (Intentionally Not Connected)

| Module | Status | Integration Point |
|--------|--------|-------------------|
| Forgery Detection Engine | Stub | `engines/forgery_engine.py` |
| OCR Engine | Stub | `engines/forgery_engine.py:OCREngine` |
| Metadata Analysis Engine | Stub | `engines/forgery_engine.py:MetadataEngine` |
| Report Generation Engine | Stub | `engines/forgery_engine.py:ReportEngine` |
| Database Layer | Not Created | Future `database/` package |
| Deep Learning Models | Not Created | Future integration via PyTorch |

## Where to Connect Future Components

### Forensic Algorithms (OpenCV, scikit-image)
Connect in `engines/` — each engine inherits from `BaseEngine` and sets `_connected = True` when the backend is ready.

### PyTorch / Deep Learning Models
Create a `models_ml/` package. Wire into the forgery engine. The UI already shows "Analysis engine not connected" and will activate when engines report `is_connected = True`.

### OCR Backend (Tesseract/PaddleOCR)
Implement `OCREngine.run()` in `engines/forgery_engine.py`. The OCR page is ready with language and mode selection.

### SQLite / Database
Create a `database/` package with SQLAlchemy or direct SQLite. Connect to `models/` dataclasses for persistence. The case, evidence, and findings models are ready.

### Metadata Extraction (ExifTool, PIL)
Implement `MetadataEngine.run()`. The metadata page has tabbed tables ready to populate.

## Key Design Decisions

- **Light theme only** — Professional forensic workstation aesthetic
- **No fake results** — All analysis shows "Not Analysed" or "Engine not connected"
- **Evidence preservation** — UI distinguishes Original/Working Copy/Processed/Finding
- **Modular architecture** — Each page, panel, and engine is independently replaceable
- **Signal/slot architecture** — Clean decoupling between UI components

## License

Development Build — Not for production use.
