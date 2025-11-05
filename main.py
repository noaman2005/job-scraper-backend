# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import re
import tempfile
import asyncio
import json
import os

# Import scrapers (for local testing)
from scrapers import IndeedScraper, NaukriScraper, LinkedInScraper

app = FastAPI()

# Toggle between local and Lambda
LOCAL_DEV = os.getenv("LOCAL_DEV", "true").lower() == "true"

if not LOCAL_DEV:
    import boto3
    lambda_client = boto3.client('lambda', region_name='us-east-1')

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
    "https://draws-hunting-immediately-wherever.trycloudflare.com",
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
        os.unlink(tmp_name)

    return {
        "keywords": keywords,
        "extracted_text_sample": text[:500]
    }

# ===== LOCAL SCRAPING (for testing) =====
def scrape_platform_local(platform_name, keywords, location):
    """Run scraper locally"""
    print(f"\n[LOCAL] Starting scrape for: {platform_name}")
    try:
        scraper_map = {
            "indeed": IndeedScraper,
            "naukri": NaukriScraper,
            "linkedin": LinkedInScraper
        }
        scraper_class = scraper_map[platform_name]
        scraper = scraper_class()
        jobs = scraper.scrape(keywords, location)
        print(f"[LOCAL] Finished scrape for {platform_name}: {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"❌ Error scraping {platform_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# ===== LAMBDA SCRAPING =====
def invoke_lambda_scraper(platform_name, keywords, location):
    """Call Lambda function"""
    print(f"\n[LAMBDA] Invoking {platform_name}Scraper...")
    try:
        response = lambda_client.invoke(
            FunctionName=f'{platform_name.capitalize()}Scraper',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'keywords': keywords,
                'location': location
            })
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        jobs = payload.get('jobs', [])
        print(f"[LAMBDA] Finished {platform_name}: {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"❌ Error invoking Lambda for {platform_name}: {str(e)}")
        return []

@app.post("/scrape_jobs")
async def scrape_jobs(payload: dict):
    keywords = payload.get("keywords")
    location = payload.get("location")
    platforms = payload.get("platforms", ["indeed"])
    
    if not keywords or not location:
        raise HTTPException(status_code=400, detail="Keywords and location required")
    
    if not platforms or len(platforms) == 0:
        raise HTTPException(status_code=400, detail="At least one platform must be selected")
    
    platforms = [p.lower() for p in platforms]
    
    print(f"\n🚀 Starting scraping from platforms: {platforms}")
    print(f"📍 Location: {location}")
    print(f"🔑 Keywords: {keywords}")
    print(f"🔧 Mode: {'LOCAL' if LOCAL_DEV else 'LAMBDA'}")
    
    scraper_map = {
        "indeed": IndeedScraper if LOCAL_DEV else None,
        "naukri": NaukriScraper if LOCAL_DEV else None,
        "linkedin": LinkedInScraper if LOCAL_DEV else None
    }
    
    valid_platforms = [p for p in platforms if p in scraper_map]
    
    if not valid_platforms:
        raise HTTPException(status_code=400, detail="No valid platforms selected")
    
    print(f"✅ Valid platforms to scrape: {valid_platforms}")
    
    # Run scrapers
    all_jobs = []
    
    if LOCAL_DEV:
        # Local mode: use ThreadPoolExecutor
        print(f"\n🔄 Running {len(valid_platforms)} scraper(s) locally in parallel...")
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=len(valid_platforms)) as executor:
            results = list(executor.map(
                lambda p: scrape_platform_local(p, keywords, location),
                valid_platforms
            ))
        
        for jobs in results:
            all_jobs.extend(jobs)
    else:
        # Lambda mode: invoke functions
        print(f"\n🔄 Invoking {len(valid_platforms)} Lambda function(s)...")
        
        for platform in valid_platforms:
            jobs = invoke_lambda_scraper(platform, keywords, location)
            all_jobs.extend(jobs)
    
    print(f"\n🎉 Total jobs scraped: {len(all_jobs)}")
    
    return {"jobs": all_jobs}
