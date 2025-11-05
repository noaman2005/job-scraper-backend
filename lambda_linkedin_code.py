# Backup reference - real code is in AWS Lambda Console
import json
import sys
sys.path.append('/var/task')

from scrapers import LinkedInScraper

def lambda_handler(event, context):
    try:
        keywords = event.get('keywords')
        location = event.get('location')
        scraper = LinkedInScraper()
        jobs = scraper.scrape(keywords, location)
        return {'statusCode': 200, 'jobs': jobs}
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}
