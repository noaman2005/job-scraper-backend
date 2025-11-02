# 🌐 Smart Job Scraper Backend

FastAPI backend for resume parsing and Indeed job scraping using Selenium.

## ✨ Features

- **PDF Resume Parsing** - Extract IT skills from PDF resumes
- **Indeed Job Scraping** - Automated job scraping with Selenium
- **Headless Chrome** - Runs without visible browser window
- **Anti-Detection** - Bypasses bot detection measures
- **Image Optimization** - Disables image loading for faster scraping
- **CORS Enabled** - Works seamlessly with React frontend
- **Interactive API Docs** - Built-in Swagger UI for testing endpoints

## 🛠️ Prerequisites

- Python 3.11+
- Chrome/Chromium browser
- ChromeDriver (matching your Chrome version)
- pip (Python package manager)

## 📦 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/noaman2005/job-scraper-backend.git
cd job-scraper-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify ChromeDriver
```bash
chromedriver --version
```

## 🚀 Running the Backend

### Start Development Server
```bash
uvicorn main:app --reload --port 8000
```

Server will be available at: **http://localhost:8000**

### Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Extract Keywords from PDF
```bash
POST /extract_keywords
Body: file (PDF upload)

Response:
{
  "keywords": ["python", "react", "docker"],
  "extracted_text_sample": "..."
}
```

### Scrape Jobs from Indeed
```bash
POST /scrape_jobs
Body: {
  "keywords": ["python", "react"],
  "location": "Mumbai"
}

Response:
{
  "jobs": [
    {
      "title": "Python Developer",
      "company": "TechCorp",
      "link": "https://indeed.com/..."
    }
  ]
}
```

```

## 🤝 Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `selenium` - Web scraping
- `PyPDF2` - PDF parsing
- `python-multipart` - File uploads
