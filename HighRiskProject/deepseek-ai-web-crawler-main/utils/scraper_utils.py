import json
import os
from typing import List, Set, Tuple
import chardet  # Add this import to detect encoding
import logging
import codecs  # Add this import for robust decoding

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)

from models.clinic import Clinic
from utils.data_utils import is_complete_clinic, is_duplicate_clinic

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    # https://docs.crawl4ai.com/core/browser-crawler-config/
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=False,  # Whether to run in headless mode (no GUI)
        verbose=True,  # Enable verbose logging
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy.

    Returns:
        LLMExtractionStrategy: The settings for how to extract data using LLM.
    """
    # https://docs.crawl4ai.com/api/strategies/#llmextractionstrategy
    return LLMExtractionStrategy(
        provider="ollama/deepseek-r1:1.5b",  # Name of the LLM provider
        # api_token=os.getenv("GROQ_API_KEY"),  # API token for authentication
        schema=Clinic.model_json_schema(),  # JSON schema of the data model
        extraction_type="schema",  # Type of extraction to perform
        instruction=(
            "Extract all clinic objects with 'locationName', 'address-street', 'address-city', 'tel', "
            "'distance', 'website', and 'directions' from the"
            "following content."
        ),  # Instructions for the LLM
        input_format="markdown",  # Format of the input content
        verbose=True,  # Enable verbose logging
        preprocessing_rules=[
            # Add preprocessing rules to handle encoding
            lambda content: content.encode('utf-8', errors='ignore').decode('utf-8', errors='replace')
        ]
    )


async def check_no_results(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
) -> bool:
    """
    Checks if the "No Results Found" message is present on the page.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        url (str): The URL to check.
        session_id (str): The session identifier.

    Returns:
        bool: True if "No Results Found" message is found, False otherwise.
    """
    # Fetch the page without any CSS selector or extraction strategy
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )

    if result.success:
        if "No Results Found" in result.cleaned_html:
            return True
    else:
        print(
            f"Error fetching page for 'No Results Found' check: {result.error_message}"
        )

    return False


async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    """
    Fetches and processes a single page of venue data.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        page_number (int): The page number to fetch.
        base_url (str): The base URL of the website.
        css_selector (str): The CSS selector to target the content.
        llm_strategy (LLMExtractionStrategy): The LLM extraction strategy.
        session_id (str): The session identifier.
        required_keys (List[str]): List of required keys in the venue data.
        seen_names (Set[str]): Set of venue names that have already been seen.

    Returns:
        Tuple[List[dict], bool]:
            - List[dict]: A list of processed venues from the page.
            - bool: A flag indicating if the "No Results Found" message was encountered.
    """
    url = f"{base_url}?page={page_number}"
    print(f"Loading page {page_number}...")

    # Check if "No Results Found" message is present
    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True  # No more results, signal to stop crawling

    # Fetch page content with the extraction strategy
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Do not use cached data
            extraction_strategy=llm_strategy,  # Strategy for data extraction
            css_selector=css_selector,  # Target specific content on the page
            session_id=session_id,  # Unique session ID for the crawl
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching page {page_number}: {result.error_message}")
        return [], False

    # Detect and decode content to handle encoding issues
    # raw_content = result.extracted_content.encode('latin1', errors='ignore')  # Encode to bytes
    # detected_encoding = chardet.detect(raw_content)['encoding']  # Detect encoding
    # logging.debug(f"Detected encoding: {detected_encoding}")

    # try:
    #     # Attempt decoding with detected encoding or fallback to utf-8
    #     decoded_content = raw_content.decode(detected_encoding or 'utf-8', errors='replace')
    #     logging.debug(f"Decoded content (first 500 chars): {decoded_content[:500]}...")  # Log first 500 characters
    #     extracted_data = json.loads(decoded_content)  # Parse JSON
    # except (UnicodeDecodeError, json.JSONDecodeError) as e:
    #     logging.error(f"Decoding or JSON parsing failed: {e}")
    #     return [], False

    # Parse extracted content
    extracted_data = json.loads(result.extracted_content)

    if not extracted_data:
        print(f"No clinics found on page {page_number}.")
        return [], False

    # After parsing extracted content
    logging.debug(f"Extracted data: {extracted_data}")

    # Process clinics
    complete_clinics = []
    for clinic in extracted_data:
        # Debugging: Print each clinic to understand its structure
        logging.debug(f"Processing clinic: {clinic}")

        # Ignore the 'error' key if it's False
        if clinic.get("error") is False:
            clinic.pop("error", None)  # Remove the 'error' key if it's False

        if not is_complete_clinic(clinic, required_keys):
            continue  # Skip incomplete clinics

        if is_duplicate_clinic(clinic["locationName"], seen_names):
            logging.info(f"Duplicate clinic '{clinic['locationName']}' found. Skipping.")
            continue  # Skip duplicate clinics

        # Add clinic to the list
        seen_names.add(clinic["locationName"])
        complete_clinics.append(clinic)

    if not complete_clinics:
        print(f"No complete clinics found on page {page_number}.")
        return [], False

    print(f"Extracted {len(complete_clinics)} clinics from page {page_number}.")
    return complete_clinics, False  # Continue crawling
