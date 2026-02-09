# 🏃‍PhySioLove: Personal health tracker

A personal health tracking dashboard to visualize weight, body composition, nutrition, sleep, and activity metrics.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![UV](https://img.shields.io/badge/UV-Package%20Manager-purple)
![Flask](https://img.shields.io/badge/Flask-3.0-green)

## Features

- 📊 Interactive visualizations with Plotly
- 📈 Track weight, body fat, calories, steps, and sleep
- 📝 Easy data entry via web form
- 📁 Import data from CSV/TSV files
- 🎨 Beautiful, responsive dashboard

## Prerequisites

- Python 3.11 or higher
- Git (optional, for version control)

## Installation

### Step 1: Install UV

UV is a blazing-fast Python package manager (10-100x faster than pip!).

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Alternative: Install with pip

```bash
pip install uv
```

#### Verify Installation

After installation, **restart your terminal** and verify:

```bash
uv --version
```

You should see something like: `uv 0.x.x`

### Step 2: Clone or Download Project

```bash
# If using Git
git clone https://github.com/joseguzman/physiolove.git
cd physiolove

# OR download and extract ZIP, then:
cd physiolove
```

### Step 3: Install Dependencies

```bash
uv sync
uv pip install -e .
```

This command will:

- Create a virtual environment in `.venv/`
- Install Flask, SQLAlchemy, and pandas
- Create a `uv.lock` file for reproducible builds

⏱️ **Takes ~2 seconds** (compared to ~45 seconds with pip!)

### Step 4: Prepare Your Data

Place your health data CSV or TSV file in the `data/` folder:

```bash
cp ~/path/to/your/health_data.csv data/
```

**Expected CSV format:**

Your file should have these columns (names are flexible):

- Date
- Weight (kg)
- Body Fat (%)
- Calories
- Steps
- Sleep total (h)
- Sleep Quality
- Observations

### Step 5: Import Your Data

```bash
uv run python scripts/import_data.py data/health_data.csv
```

You should see, for example:

```bash
📊 Importing data from data/health_data.csv...

📋 Found columns: ['Date', 'Weight (kg)', 'Body Fat (%)', ...]

📌 Mapped columns: {'date': 'Date', 'weight': 'Weight (kg)', ...}

✓ Import complete!
  • Added: 114 entries
  • Skipped: 0 entries
  • Errors: 0 entries
  • Total in database: 114
```

### Step 6: Run the Application

```bash
uv run python app.py
```

You should see:

```bash
✓ Database initialized

🏃‍♂️ Health Tracker Starting...
📊 Visit: http://localhost:5000
```

### Step 7: Open in Browser

Open your web browser and navigate to:<http://localhost:5000>

🎉 You should now see your health tracking dashboard!

## Usage

### Viewing Your Data

The dashboard displays:

- **Statistics Cards**: Average weight, body fat, calories, steps, total entries
- **Weight & Body Fat Chart**: Interactive line chart showing trends over time
- **Steps Chart**: Bar chart of daily step counts

### Adding New Entries

Scroll to the bottom of the page and use the form to add new daily entries:

1. Select the date
2. Fill in your metrics (weight, body fat, calories, steps, sleep)
3. Click "Add Entry"
4. Charts update automatically!

### Re-importing Data

If you have new data to import:

```bash
uv run python scripts/import_data.py data/new_data.csv
```

The script will skip existing entries and only add new ones.

## Common Commands

### Run the Application

This will create the virtual environment if not already created:

```bash
uv run python app.py
```

### Import Data

```bash
uv run python scripts/import_data.py data/your_file.csv
```

### Add a New Package

```bash
uv add package-name
```

### Add a Development Package

```bash
uv add --dev pytest
```

### Update All Packages

```bash
uv sync --upgrade
```

## Project Structure

```bash
physiolove/
├── app.py                  # Main Flask application
├── pyproject.toml          # Project configuration & dependencies
├── uv.lock                 # Locked dependency versions
├── .venv/                  # Virtual environment (auto-created)
├── templates/
│   └── index.html         # Dashboard HTML
├── scripts/
│   └── import_data.py     # Data import script
├── data/
│   └── health_data.csv    # Your health data (gitignored)
├── utils/
│   └── __init__.py
└── health_tracker.db      # SQLite database (auto-created)
```

## Troubleshooting

### UV command not found

After installation, restart your terminal. If still not working:

```bash
# macOS/Linux
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc

# Windows
# Add %USERPROFILE%\.cargo\bin to your PATH
```

### Port 5000 already in use

```bash
# Find and kill the process
lsof -i :5000
kill -9 <PID>

# Or use a different port (edit app.py, last line)
```

### Import errors (KeyError: 'Date')

The script will show you the actual column names in your file. Make sure your CSV/TSV has a column with "date" in the name.

### Database is locked

```bash
# Stop the app (Ctrl+C) and delete the database
rm health_tracker.db

# Re-import your data
uv run python scripts/import_data.py data/health_data.csv
```

### Import encoding errors

Make sure your file is UTF-8 encoded:

```bash
# Check encoding
file -I data/health_data.csv

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

## Why UV?

UV is a modern Python package manager that's:

- ⚡ **10-100x faster** than pip
- 🔒 **More reliable** with automatic lock files
- 🎯 **Easier to use** - no virtual environment activation needed
- 🚀 **Future-proof** - built in Rust, actively maintained

### UV vs pip

| Task | pip | UV |
| :--- | :--- | :--- |
| Install deps | `pip install -r requirements.txt` (45s) | `uv sync` (2s) |
| Activate venv | `source venv/bin/activate` | Not needed |
| Run script | `python app.py` | `uv run python app.py` |
| Add package | `pip install pkg` + manual `requirements.txt` | `uv add pkg` (automatic) |

## Development

### Running Tests (when added)

```bash
uv run pytest
```

### Code Formatting (when added)

```bash
uv run black .
```

## Data Privacy

Your health data stays **local**:

- Stored in `health_tracker.db` (SQLite database)
- Never sent to any server
- You have complete control

## Next Steps

Want to enhance your tracker? Consider adding:

- 📊 More charts (nutrition breakdown, sleep analysis, correlations)
- 📤 Export functionality (download data as CSV/Excel)
- 🔐 Password protection
- 🐳 Docker containerization
- ☁️ Cloud deployment
- 📱 Mobile-responsive design

## License

MIT License - Feel free to use and modify!

## Support

Having issues?

1. Check the [Troubleshooting](#troubleshooting) section
2. Make sure UV is properly installed: `uv --version`
3. Verify your data file is in the correct format
4. Check that Python 3.11+ is installed: `python --version`

## Acknowledgments

Built with:

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Plotly](https://plotly.com/javascript/) - Interactive charts
- [UV](https://github.com/astral-sh/uv) - Fast package manager
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

---

**Happy tracking!** 💪📊
