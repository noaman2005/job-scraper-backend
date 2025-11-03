# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Import scrapers
from scrapers import IndeedScraper, NaukriScraper, LinkedInScraper

app = FastAPI()

IT_KEYWORDS = [
    "python", "java", "c++", "javascript", "typescript", "html", "css",
    "react", "node.js", "django", "flask", "php", "mysql", "mongodb", "sql",
    "aws", "azure", "linux", "docker", "kubernetes", "git", "github",
    "machine learning", "data analysis", "data science", "pandas", "numpy",
    "frontend", "backend", "full stack", "ui", "ux", "api", "rest api",
    "agile", "scrum", "testing"
]

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://ai-job-scraper.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text().lower()
    return text

@app.post("/extract_keywords")
async def extract_keywords(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        tmp_name = tmp.name

    try:
        text = extract_text_from_pdf(tmp_name)
        keywords = [k for k in IT_KEYWORDS if re.search(r'\b' + re.escape(k.lower()) + r'\b', text)]
    finally:
        import os
        os.unlink(tmp_name)

    return {
        "keywords": keywords,
        "extracted_text_sample": text[:500]
    }

@app.post("/scrape_jobs")
async def scrape_jobs(payload: dict):
    keywords = payload.get("keywords")
    location = payload.get("location")
    platforms = payload.get("platforms", ["indeed"])  # Get platforms from frontend
    
    if not keywords or not location:
        raise HTTPException(status_code=400, detail="Keywords and location required")
    
    if not platforms or len(platforms) == 0:
        raise HTTPException(status_code=400, detail="At least one platform must be selected")
    
    # Normalize platform names to lowercase
    platforms = [p.lower() for p in platforms]
    
    print(f"\n🚀 Starting scraping from platforms: {platforms}")
    print(f"📍 Location: {location}")
    print(f"🔑 Keywords: {keywords}")
    
    # Map platform names to scraper classes
    scraper_map = {
        "indeed": IndeedScraper,
        "naukri": NaukriScraper,
        "linkedin": LinkedInScraper
    }
    
    # Filter to only valid platforms that user selected
    valid_platforms = []
    for p in platforms:
        if p in scraper_map:
            valid_platforms.append(p)
        else:
            print(f"⚠️ Unknown platform: {p}")
    
    if not valid_platforms:
        raise HTTPException(status_code=400, detail="No valid platforms selected")
    
    print(f"✅ Valid platforms to scrape: {valid_platforms}")
    
    # Scrape concurrently using ThreadPoolExecutor
    def scrape_platform(platform_name):
        print(f"\n[THREAD] Starting scrape for: {platform_name}")
        try:
            scraper_class = scraper_map[platform_name]
            scraper = scraper_class()
            jobs = scraper.scrape(keywords, location)
            print(f"[THREAD] Finished scrape for {platform_name}: {len(jobs)} jobs")
            return jobs
        except Exception as e:
            print(f"❌ Error scraping {platform_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    # Run scrapers in parallel (only for selected platforms)
    print(f"\n🔄 Running {len(valid_platforms)} scraper(s) in parallel...")
    with ThreadPoolExecutor(max_workers=len(valid_platforms)) as executor:
        results = list(executor.map(scrape_platform, valid_platforms))
    
    # Combine all results
    all_jobs = []
    for jobs in results:
        all_jobs.extend(jobs)
    
    print(f"\n🎉 Total jobs scraped from {len(valid_platforms)} platform(s): {len(all_jobs)}")
    
    return {"jobs": all_jobs}

