# ExcelToMif

> Convert Excel files to MIF (Maker Interchange Format) format.

## Project Structure

```
ExcelToMif/
├── execution/          # Deterministic Python scripts
├── directives/         # SOPs in Markdown
├── .tmp/               # Intermediate files (gitignored)
├── requirements.txt    # Python dependencies
├── .env.template       # Environment variable template
└── README.md
```

## Setup

```powershell
# Create and activate venv (stored outside project)
python -m venv D:\.venvs\ExcelToMif
D:\.venvs\ExcelToMif\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Venv location

`D:\.venvs\ExcelToMif\`

## Portable dist location

`D:\.dist\ExcelToMif\`

## Python version

Python 3.13+
