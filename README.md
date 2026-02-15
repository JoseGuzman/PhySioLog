# 🏃‍♂️ PhysioLog: Personal Health Tracker

A personal health tracking dashboard to visualize weight, body composition, nutrition, sleep, and activity metrics with an elegant dark-themed interface.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![UV](https://img.shields.io/badge/UV-Package%20Manager-purple)
![Flask](https://img.shields.io/badge/Flask-3.0-green)

## ✨ Features

- 🎨 **Dark Theme Interface** - Modern sidebar navigation with purple accents
- 📊 **Interactive Visualizations** - Plotly charts with time range selectors
- 📈 **Track Multiple Metrics** - Weight, body fat, calories, steps, and sleep
- 📉 **7-Day Moving Averages** - See trends clearly
- 📝 **Easy Data Entry** - Simple web form
- 📁 **CSV/TSV Import** - Import historical data
- 💾 **SQLite Database** - All data stored locally

## 🎯 Interface

### Navigation

- **TRACK Section**
  - 📊 Overview - Statistics cards + data entry form
  - 📈 Visualizations - 4 interactive charts with moving averages
- **MANAGE Section** (coming soon)
  - Data management features

### Charts

1. **Weight Trend** - Daily weight + 7-day average
2. **Body Fat Trend** - Daily body fat % + 7-day average
3. **Daily Steps** - Bar chart + 7-day average
4. **Sleep Total** - Sleep hours + 7-day average

All charts include time range selectors: Last 30 days, Last 90 days, All

## 📋 Prerequisites

- Python 3.11 or higher
- Git (optional, for version control)

## 🚀 Installation

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
git clone https://github.com/yourusername/physiolog.git
cd physiolog

# OR download and extract ZIP, then:
cd physiolog
```

### Step 3: Install Dependencies

```bash
uv sync
```

This command will:

- Create a virtual environment in `.venv/`
- Install Flask, SQLAlchemy, and pandas
- Create a `uv.lock` file for reproducible builds

⏱️ **Takes ~2 seconds** (compared to ~45 seconds with pip!)

### Step 4: Prepare Your Data (Optional)

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

### Step 5: Import Your Data (Optional)

```bash
uv run python scripts/import_data.py data/health_data.csv
```

You should see:

```bash
📊 Importing data from data/health_data.csv...
📋 Found columns: ['Date', 'Weight (kg)', 'Body Fat (%)', ...]
✓ Import complete!
  • Added: 114 entries
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

Open your web browser and navigate to:

**<http://localhost:5000>**

🎉 You should now see your health tracking dashboard!

## 📖 Usage

### Viewing Your Data

The **Overview** page displays:

- **Statistics Cards**: Average weight, body fat, calories, steps, total entries
- **Data Entry Form**: Add new daily entries

The **Visualizations** page displays:

- **4 Interactive Charts**: Weight, Body Fat, Steps, Sleep
- **7-Day Moving Averages**: Smoothed trend lines
- **Time Range Selectors**: View Last 30 days, 90 days, or All data

### Adding New Entries

1. Go to the Overview page
2. Fill in the form with your daily metrics
3. Click "Add Entry"
4. View updated statistics immediately!

### Re-importing Data

If you have new data to import:

```bash
uv run python scripts/import_data.py data/new_data.csv
```

The script will skip existing entries and only add new ones.

## 🎨 Customization

### Change Theme Colors

Edit `templates/base.html` to customize colors:

```css
/* Primary purple accent */
background: #8b5cf6;

/* Dark backgrounds */
background: #1a1a1a;  /* Main background */
background: #252525;  /* Card background */
background: #0f0f0f;  /* Sidebar background */

/* Borders */
border: 1px solid #cccccc;  /* Light grey borders */
```

## 📁 Project Structure

```bash
├── LICENSE
├── README.md
├── __pycache__
│   ├── app.cpython-312.pyc
│   ├── config.cpython-312.pyc
│   └── wsgi.cpython-39.pyc
├── app.py
├── data
│   └── health_data.csv
├── docs
│   ├── AI_CONTEXT.md
│   ├── API_test.md
│   ├── API_test.pdf
│   ├── ChatGPT_instructions.md
│   └── codex.md
├── instance
│   └── physiolog.db
├── main.py
├── physiolog
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes_api.py
│   ├── routes_web.py
│   └── services.py
├── physiolog.egg-info
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── requires.txt
│   └── top_level.txt
├── pyproject.toml
├── scripts
│   ├── __init__.py
│   └── import_data.py
├── static
│   ├── css
│   └── js
├── templates
│   ├── base.html
│   ├── coach.html
│   ├── entry.html
│   ├── login.html
│   ├── overview.html
│   ├── test.html
│   └── trends.html
├── tests
│   ├── __pycache__
│   └── test_services.py
├── utils
│   └── __init__.py
├── uv.lock
└── wsgi.py
```

## � Production Deployment

### Run Locally with Gunicorn

Gunicorn is a production-grade WSGI server. To run locally:

```bash
uv run gunicorn -w 2 -b 127.0.0.1:8000 app:app
```

Then open your browser to <http://127.0.0.1:8000>

### Run on EC2 (Public Binding)

To deploy on AWS EC2 with Gunicorn binding to all interfaces:

```bash
uv run gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

**Important:** Make sure your EC2 security group allows inbound traffic on port 8000.

### Recommended Gunicorn Configuration

For production environments, use this configuration with additional logging and timeout settings:

```bash
uv run gunicorn app:app \
  -w 2 \
  -b 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --timeout 60
```

**Parameters explained:**

- `-w 2` → 2 worker processes (adjust based on CPU cores)
- `-b 0.0.0.0:8000` → Bind to all interfaces on port 8000
- `--access-logfile -` → Log access to stdout
- `--error-logfile -` → Log errors to stdout
- `--timeout 60` → Prevent premature worker restarts (seconds)

## 🐳 Docker Deployment (Coming Soon)

Preparing for containerized deployment on AWS:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "app:app", "-w 2", "-b 0.0.0.0:8000"]
```

## � Environment Variables

### Local Development

Create a `.env` file in the project root:

```bash
SECRET_KEY=super-secret-key
FLASK_DEBUG=True
SQLALCHEMY_DATABASE_URI=sqlite:///physiolog.db
```

Ensure your `.env` file is added to `.gitignore` to keep secrets out of version control.

### Production (EC2)

For production environments, set environment variables directly:

```bash
export SECRET_KEY="production-secret"
export FLASK_DEBUG="False"
export SQLALCHEMY_DATABASE_URI="postgresql://user:password@db-endpoint:5432/physiolog"
```

Or pass them to Gunicorn:

```bash
SECRET_KEY="production-secret" FLASK_DEBUG="False" uv run gunicorn app:app -w 2 -b 0.0.0.0:8000
```

## �🔧 Common Commands

### Run the Application

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

### Update All Packages

```bash
uv sync --upgrade
```

## 🐛 Troubleshooting

### UV command not found

After installation, restart your terminal. If still not working:

```bash
# macOS/Linux
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```

### Port 5000 already in use

```bash
# Find and kill the process
lsof -i :5000
kill -9 <PID>

# Or use a different port (edit app.py, last line)
```

### Database is locked

```bash
# Stop the app (Ctrl+C) and delete the database
rm physiolog.db

# Re-import your data
uv run python scripts/import_data.py data/health_data.csv
```

## 🔒 Data Privacy

Your health data stays **local**:

- Stored in `physiolog.db` (SQLite database)
- Never sent to any server
- You have complete control

## 🎯 Deployment Roadmap

- [ ] Docker containerization
- [ ] AWS deployment (Lightsail/ECS)
- [ ] PostgreSQL support
- [ ] Export functionality (CSV/Excel)
- [ ] Additional charts (correlations, trends)
- [ ] Mobile-responsive improvements
- [ ] User authentication

## 📄 License

MIT License - Feel free to use and modify!

## 🙏 Acknowledgments

Built with:

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Plotly](https://plotly.com/javascript/) - Interactive charts
- [UV](https://github.com/astral-sh/uv) - Fast package manager
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

---

**Happy tracking!** 💪📊
