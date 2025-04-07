import requests
import ssl
from trafilatura import extract
import logging
import asyncio
import httpx

input_search_query='who won the latest us election'

HOST = 'brd.superproxy.io'
PORT = 33335

BRIGHT_DATA_SERP_USERNAME = 'brd-customer-hl_f6f5fe18-zone-serp_api1'
BRIGHT_DATA_SERP_PASSWORD = 'b9q8vlsnf38n'

BRIGHT_DATA_SERP_PROXY_URL = f'http://{BRIGHT_DATA_SERP_USERNAME}:{BRIGHT_DATA_SERP_PASSWORD}@{HOST}:{PORT}'

BRIGHT_DATA_SERP_PROXIES = {
    'http': BRIGHT_DATA_SERP_PROXY_URL,
    'https': BRIGHT_DATA_SERP_PROXY_URL
}

BRIGHT_DATA_SCRAPING_USERNAME = 'brd-customer-hl_f6f5fe18-zone-web_unlocker1'
BRIGHT_DATA_SCRAPING_PASSWORD = '94a5d1wlxc0e'

BRIGHT_DATA_SCRAPING_PROXY_URL = f'http://{BRIGHT_DATA_SCRAPING_USERNAME}:{BRIGHT_DATA_SCRAPING_PASSWORD}@{HOST}:{PORT}'

BRIGHT_DATA_SCRAPING_PROXIES = {
    'http://': BRIGHT_DATA_SCRAPING_PROXY_URL,
    'https://': BRIGHT_DATA_SCRAPING_PROXY_URL
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

total_search_results_count=0
total_successful_scraping=0
total_successful_webpage_text_extraction=0

httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)

async def search(search_query):
    url = f"https://www.google.com/search?q={search_query}&brd_json=1"

    try:
        logging.info("Getting Search Results...")
        response = (requests.get(url, proxies=BRIGHT_DATA_SERP_PROXIES, verify=False)).json()
        search_results=response['organic']
        logging.info("Successfully obtained Search Results!")
        search_result_urls=[search_result['link'] for search_result in search_results]
        logging.info(f"Obtained Search Result URLS:{search_result_urls}")
        return {'search_results':search_results,'search_result_urls':search_result_urls}
    
    except Exception as e:
        logging.exception(e)

async def url_scraper(url):
    try:
       logging.info(f"Scraping {url}")

       async with httpx.AsyncClient(proxies=BRIGHT_DATA_SCRAPING_PROXIES,verify=ssl_context,timeout=200) as client:
            raw_html_content = (await client.get(url)).text

       logging.info(f"Successfully Scraped {url}")

       actual_webpage_content=extract(raw_html_content)

       if actual_webpage_content!=None:
        logging.info(f"Successfully Extracted the Text Content from {url}")
       else:
        logging.error(f"Extracting Text Content Failed from {url}")
        actual_webpage_content=""

       return {'raw_html_content':raw_html_content,'actual_webpage_content':actual_webpage_content,'url':url}

    except Exception as e:
        logging.error(f"Scraping {url} Failed")
        logging.exception(e)   

serp_api_response=asyncio.run(search(input_search_query))
search_result_urls=serp_api_response['search_result_urls']


async def main_scraper():
    scraping_tasks_list=[]
    async with asyncio.TaskGroup() as tg:
        for url in search_result_urls:
            scraping_task=tg.create_task(url_scraper(url))
            scraping_tasks_list.append(scraping_task)
    scraped_results=[scraping_task.result() for scraping_task in scraping_tasks_list]
    return scraped_results

scraped_results=asyncio.run(main_scraper())

scraped_content_for_llm=""
for i in scraped_results:
    scraped_content_for_llm="Content:"+scraped_content_for_llm+i['actual_webpage_content']+"\nSource:"+i['url']+"\n\n"


print('\nNo of Pages Scraped:',len(scraped_results))
# print(scraped_content_for_llm)  # Final Scraped Content which can be used by the LLM




