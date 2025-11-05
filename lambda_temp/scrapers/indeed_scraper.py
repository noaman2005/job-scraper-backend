# scrapers/indeed_scraper.py
from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time

class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com"""
    
    def __init__(self):
        super().__init__()
        self.platform = "Indeed"
    
    def scrape(self, keywords, location):
        """Scrape jobs from Indeed"""
        self.setup_driver()
        all_jobs = []
        
        try:
            for keyword in keywords:
                search_url = f"https://www.indeed.com/jobs?q={keyword}&l={location.replace(' ', '+')}"
                print(f"\n🔍 [{self.platform}] Searching: {search_url}")
                self.driver.get(search_url)
                time.sleep(5)
                
                page_source = self.driver.page_source
                print(f"[{self.platform}] Page loaded, length: {len(page_source)} bytes")
                
                # Try multiple selectors
                jobs = []
                try:
                    jobs = self.driver.find_elements(By.CSS_SELECTOR, "a.jcs-JobTitle")
                    if len(jobs) > 0:
                        print(f"[{self.platform}] Found {len(jobs)} jobs with 'a.jcs-JobTitle'")
                except:
                    pass
                
                if len(jobs) == 0:
                    try:
                        jobs = self.driver.find_elements(By.CSS_SELECTOR, "h2.jobTitle a")
                        print(f"[{self.platform}] Found {len(jobs)} jobs with 'h2.jobTitle a'")
                    except:
                        pass
                
                if len(jobs) == 0:
                    try:
                        jobs = self.driver.find_elements(By.CSS_SELECTOR, "a[data-jk]")
                        print(f"[{self.platform}] Found {len(jobs)} jobs with 'a[data-jk]'")
                    except:
                        pass
                
                # Get companies
                try:
                    companies = self.driver.find_elements(By.CSS_SELECTOR, "span.companyName")
                    print(f"[{self.platform}] Found {len(companies)} companies")
                except:
                    companies = []
                
                # Extract job data
                for i in range(len(jobs)):
                    try:
                        title = jobs[i].text.strip()
                        link = jobs[i].get_attribute("href")
                        
                        if link and not link.startswith("http"):
                            link = "https://www.indeed.com" + link
                        
                        company = companies[i].text.strip() if i < len(companies) else "N/A"
                        
                        if title and link:
                            all_jobs.append({
                                "title": title,
                                "company": company,
                                "link": link,
                                "platform": self.platform
                            })
                            print(f"  ✅ {title} — {company}")
                    except Exception as e:
                        print(f"  ⚠️ Error extracting job {i}: {str(e)}")
        
        except Exception as e:
            print(f"❌ [{self.platform}] Error: {str(e)}")
        
        finally:
            self.close()
        
        print(f"\n📊 [{self.platform}] Total jobs found: {len(all_jobs)}")
        return all_jobs
