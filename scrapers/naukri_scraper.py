# scrapers/naukri_scraper.py
from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time

class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com"""
    
    def __init__(self):
        super().__init__()
        self.platform = "Naukri"
    
    def scrape(self, keywords, location):
        """Scrape jobs from Naukri.com"""
        self.setup_driver()
        all_jobs = []
        
        try:
            for keyword in keywords:
                search_url = f"https://www.naukri.com/{keyword.replace(' ', '-')}-jobs-in-{location.replace(' ', '-')}"
                print(f"\n🔍 [{self.platform}] Searching: {search_url}")
                self.driver.get(search_url)
                time.sleep(7)  # Naukri loads slowly
                
                page_source = self.driver.page_source
                print(f"[{self.platform}] Page loaded, length: {len(page_source)} bytes")
                
                # Naukri CSS selectors
                jobs = []
                try:
                    jobs = self.driver.find_elements(By.CSS_SELECTOR, "a.title")
                    print(f"[{self.platform}] Found {len(jobs)} jobs with 'a.title'")
                except Exception as e:
                    print(f"[{self.platform}] Selector failed: {str(e)}")
                
                # Alternative selector
                if len(jobs) == 0:
                    try:
                        jobs = self.driver.find_elements(By.CSS_SELECTOR, "article.jobTuple a.title")
                        print(f"[{self.platform}] Found {len(jobs)} jobs with alternative selector")
                    except:
                        pass
                
                # Get companies
                try:
                    companies = self.driver.find_elements(By.CSS_SELECTOR, "a.comp-name")
                    print(f"[{self.platform}] Found {len(companies)} companies")
                except:
                    companies = []
                
                # Extract job data
                for i in range(min(len(jobs), 20)):  # Limit to 20 per keyword
                    try:
                        title = jobs[i].text.strip()
                        link = jobs[i].get_attribute("href")
                        
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
            import traceback
            traceback.print_exc()
        
        finally:
            self.close()
        
        print(f"\n📊 [{self.platform}] Total jobs found: {len(all_jobs)}")
        return all_jobs
