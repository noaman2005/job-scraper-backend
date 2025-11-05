# scrapers/linkedin_scraper.py
from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs"""
    
    def __init__(self):
        super().__init__()
        self.platform = "LinkedIn"
    
    def scrape(self, keywords, location):
        """Scrape jobs from LinkedIn"""
        self.setup_driver()
        all_jobs = []
        
        try:
            for keyword in keywords:
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
                print(f"\n🔍 [{self.platform}] Searching: {search_url}")
                self.driver.get(search_url)
                
                # Wait for job cards to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.base-card"))
                    )
                except:
                    print(f"[{self.platform}] Timeout waiting for job cards")
                
                time.sleep(5)  # Give extra time for dynamic content
                
                page_source = self.driver.page_source
                print(f"[{self.platform}] Page loaded, length: {len(page_source)} bytes")
                
                # Find all job cards
                job_cards = []
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.base-card")
                    print(f"[{self.platform}] Found {len(job_cards)} job cards")
                except Exception as e:
                    print(f"[{self.platform}] Failed to find job cards: {str(e)}")
                
                # Extract job data from cards
                for i in range(min(len(job_cards), 25)):  # Increased limit to 25
                    try:
                        card = job_cards[i]
                        
                        # Method 1: Try to get link first (always works)
                        link = None
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                            link = link_elem.get_attribute("href")
                        except:
                            pass
                        
                        # Method 2: Get title from aria-label (most reliable)
                        title = None
                        try:
                            # LinkedIn stores job title in aria-label of the full link
                            link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                            aria_label = link_elem.get_attribute("aria-label")
                            if aria_label:
                                # aria-label format: "Job Title at Company"
                                title = aria_label.split(" at ")[0].strip()
                        except:
                            pass
                        
                        # Method 3: Try h3 title
                        if not title:
                            try:
                                title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                                title = title_elem.text.strip()
                            except:
                                pass
                        
                        # Method 4: Try span.sr-only
                        if not title:
                            try:
                                title_elem = card.find_element(By.CSS_SELECTOR, "span.sr-only")
                                title = title_elem.text.strip()
                            except:
                                pass
                        
                        # Get company
                        company = "N/A"
                        try:
                            company_elem = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
                            company = company_elem.text.strip()
                        except:
                            try:
                                company_elem = card.find_element(By.CSS_SELECTOR, "a.hidden-nested-link")
                                company = company_elem.text.strip()
                            except:
                                # Last resort: try to extract from aria-label
                                try:
                                    link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                                    aria_label = link_elem.get_attribute("aria-label")
                                    if aria_label and " at " in aria_label:
                                        company = aria_label.split(" at ")[-1].strip()
                                except:
                                    pass
                        
                        # Only add if we have both title and link
                        if title and link:
                            all_jobs.append({
                                "title": title,
                                "company": company,
                                "link": link,
                                "platform": self.platform
                            })
                            print(f"  ✅ {title} — {company}")
                        elif link and not title:
                            print(f"  ⚠️ Skipped job {i}: Could not extract title (link exists)")
                            
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
