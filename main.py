from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import re
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

app = FastAPI()

IT_KEYWORDS = [
    "python", "java", "c++", "javascript", "typescript", "html", "css",
    "react", "node.js", "django", "flask", "php", "mysql", "mongodb", "sql",
    "aws", "azure", "linux", "docker", "kubernetes", "git", "github",
    "machine learning", "data analysis", "data science", "pandas", "numpy",
    "frontend", "backend", "full stack", "ui", "ux", "api", "rest api",
    "agile", "scrum", "testing"
]

# Allow local frontend to connect
origins = [
    "http://localhost:3000",
    "http://localhost:5173"  # React dev server origin
    # add other origins if needed
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

def extract_resume_keywords(file_path):
    text = extract_text_from_pdf(file_path)
    return [k for k in IT_KEYWORDS if re.search(r'\\b' + re.escape(k.lower()) + r'\\b', text)]


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
        "extracted_text_sample": text[:500]  # return first 500 chars for inspection
    }




@app.post("/scrape_jobs")
async def scrape_jobs(payload: dict):
    keywords = payload.get("keywords")
    location = payload.get("location")
    if not keywords or not location:
        raise HTTPException(status_code=400, detail="Keywords and location required")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    """
    })
    
    all_jobs = []

    try:
        for keyword in keywords:
            search_url = f"https://www.indeed.com/jobs?q={keyword}&l={location.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(5)

            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            jobs = driver.find_elements(By.CSS_SELECTOR, "a.jcs-JobTitle")
            companies = driver.find_elements(By.CSS_SELECTOR, "span.companyName")

            for i in range(len(jobs)):
                title = jobs[i].text.strip()
                link = jobs[i].get_attribute("href")
                company = companies[i].text.strip() if i < len(companies) else "N/A"
                if title and link:
                    all_jobs.append({"title": title, "company": company, "link": link})
    finally:
        driver.quit()

    return {"jobs": all_jobs}
