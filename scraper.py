import os
import re
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pyairtable import Api
from dotenv import load_dotenv

print(">>> [1/10] Memulai eksekusi skrip scraper.py...")

# Load environment variables
print(">>> [2/10] Membaca file .env untuk mengambil kredensial...")
load_dotenv()

# Configure Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)

# Airtable Configuration
AIRTABLE_ACCESS_TOKEN = os.getenv("AIRTABLE_ACCESS_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

print(">>> [3/10] Memeriksa kredensial di file .env...")
if not all([AIRTABLE_ACCESS_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME]):
    error_msg = "ERROR: Kredensial Airtable tidak lengkap di file .env!"
    print(error_msg)
    logging.error(error_msg)
    exit(1)

print(">>> [4/10] Kredensial lengkap. Mencoba koneksi ke Airtable...")
try:
    api = Api(AIRTABLE_ACCESS_TOKEN)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    print(">>> [4/10] Setup Airtable API object berhasil.")
except Exception as e:
    print(f"ERROR: Gagal mengatur koneksi Airtable: {e}")
    exit(1)


def clean_data(text: str) -> str:
    """Clean extracted text by removing extra whitespaces."""
    if text:
        return " ".join(text.split()).strip()
    return ""

def format_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if url and not url.startswith("http"):
        return "https://" + url
    return url

def accept_cookies(page):
    """Handle Google Maps cookie consent pop-up if it appears."""
    try:
        print(">>> [7/10] Sedang mengecek apakah ada pop-up Cookie...")
        # Common selectors for Google consent buttons
        consent_button = page.locator("button:has-text('Accept all'), button:has-text('Setuju')")
        if consent_button.is_visible(timeout=3000):
            consent_button.click()
            print(">>> [7/10] Pop-up Cookie ditemukan dan sudah diklik.")
            logging.info("Cookie consent accepted.")
        else:
            print(">>> [7/10] Tidak ada pop-up cookie.")
    except Exception as e:
        print(f">>> [7/10] Error kecil saat cek cookie (diabaikan): {e}")


def scrape_google_maps(keyword: str, location: str, max_results: int = 10):
    """Scrape Google Maps for a keyword in a location and save to Airtable."""
    search_query = f"{keyword} di {location}"
    print(f"\n>>> [5/10] Memulai proses scraping untuk kata kunci: '{search_query}'")
    logging.info(f"Starting scrape for: {search_query}")

    print(">>> [6/10] Sedang meluncurkan browser (Playwright)... Pastikan Playwright sudah terinstall.")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            print(">>> [6/10] Browser Chromium berhasil dibuka.")
            
            context = browser.new_context(locale="id-ID")
            page = context.new_page()

            print(">>> [6/10] Membuka URL Google Maps...")
            page.goto("https://www.google.com/maps", timeout=60000)
            print(">>> [6/10] Halaman Google Maps berhasil dimuat.")
            
            accept_cookies(page)

            # Search
            print(">>> [8/10] Mengetikkan kata kunci pencarian di kolom search box...")
            search_box = page.locator('input#searchboxinput, input.searchboxinput, input[name="q"]')
            search_box.wait_for(state="visible", timeout=30000)
            search_box.fill(search_query)
            page.keyboard.press("Enter")

            # Wait for results panel to load
            print(">>> [8/10] Menunggu panel hasil di sebelah kiri untuk muncul...")
            try:
                page.wait_for_selector('div[role="feed"]', timeout=20000)
                print(">>> [8/10] Panel hasil berhasil dimuat!")
                logging.info("Results panel loaded.")
            except PlaywrightTimeoutError:
                print("ERROR: Panel hasil tidak muncul dalam 20 detik atau koneksi lambat.")
                logging.warning("Results panel not found. Maybe no results or different UI.")
                return

            scraped_data = []
            
            # Target the feed for scrolling and item extraction
            feed = page.locator('div[role="feed"]')
            
            print(">>> [9/10] Memulai penarikan data...")
            while len(scraped_data) < max_results:
                # Wait a bit for elements to settle
                page.wait_for_timeout(2000)
                
                # Get current items in the view
                items = feed.locator('.hfpxzc').all()
                
                if not items:
                    print(">>> [9/10] Tidak ada item (atau tidak ada lagi item) yang ditemukan di panel kiri.")
                    break

                for item in items[len(scraped_data):]:
                    if len(scraped_data) >= max_results:
                        break

                    try:
                        print(f"\n>>> [9/10] Membuka data detail tempat ke-{len(scraped_data)+1} ...")
                        # Click the item to load details on the left panel
                        item.click()
                        page.wait_for_timeout(2000) # Wait for details to populate

                        # Extract details
                        name_locator = page.locator('h1.DUwDvf.lfPIob')
                        name = clean_data(name_locator.inner_text() if name_locator.count() > 0 else "")

                        address_locator = page.locator('button[data-item-id="address"] .fontBodyMedium')
                        address = clean_data(address_locator.inner_text() if address_locator.count() > 0 else "")
                        
                        phone_locator = page.locator('button[data-tooltip="Salin nomor telepon"], button[data-tooltip="Copy phone number"]').first
                        phone = clean_data(phone_locator.inner_text() if phone_locator.count() > 0 else "")

                        website_locator = page.locator('a[data-item-id="authority"]')
                        website = clean_data(website_locator.get_attribute('href') if website_locator.count() > 0 else "")
                        
                        rating_locator = page.locator('div.F7nice > span > span[aria-hidden="true"]').first
                        rating = clean_data(rating_locator.inner_text() if rating_locator.count() > 0 else "")

                        if name:
                            data = {
                                "Name": name,
                                "Address": address,
                                "Phone": phone,
                                "Website": format_url(website),
                                "Rating": rating
                            }
                            print(f">>> [9/10] Berhasil mengekstrak: {name}")
                            scraped_data.append(data)
                            logging.info(f"Scraped: {name}")
                            
                            # Upsert to Airtable
                            print(f">>> [10/10] Bersiap mengirim data '{name}' ke Airtable...")
                            upsert_to_airtable(data)
                        else:
                            print(f">>> [9/10] Gagal mendapatkan nama tempat (skipped).")
                            
                    except Exception as e:
                        print(f"ERROR: Terjadi kesalahan saat menarik detail info: {e}")
                        logging.error(f"Error extracting an item: {e}", exc_info=True)

                # Scroll down
                try:
                    print(f">>> [9/10] Menggeser/Scroll halaman ke bawah (sudah dapat: {len(scraped_data)} data)...")
                    feed.hover()
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(3000)
                    
                    # Check if reached the end
                    end_text = page.locator("text='Anda telah mencapai akhir daftar', text='You\'ve reached the end of the list'")
                    if end_text.is_visible():
                        print(">>> [9/10] Sudah mencapai bagian paling bawah pencarian Google Maps.")
                        logging.info("Reached the end of the list.")
                        break
                except Exception as e:
                     print(f"ERROR: Terjadi kesalahan saat auto-scroll: {e}")
                     logging.error(f"Error scrolling: {e}")
                     break

            print(f">>> [INFO] Selesai scraping! Total data terkumpul: {len(scraped_data)}")
            logging.info(f"Finished scraping. Total collected: {len(scraped_data)}")

        except Exception as e:
            print(f"ERROR FATAL KETIKA MENJALANKAN PLAYWRIGHT/BROWSER: {e}")
            logging.error(f"A critical error occurred: {e}", exc_info=True)
        finally:
            if 'browser' in locals():
                print(">>> [INFO] Menutup browser...")
                browser.close()

def upsert_to_airtable(data: dict):
    """Insert or update a record in Airtable to prevent duplicates based on Name and Phone/Address."""
    try:
        name = data.get("Name")
        if not name:
            return
            
        formula = f"{{Name}} = '{name}'"
        existing_records = table.all(formula=formula)
        
        if existing_records:
            record_id = existing_records[0]['id']
            table.update(record_id, data)
            print(f">>> [10/10] BERHASIL: Data '{name}' sudah ada (Updated).")
            logging.info(f"Updated record in Airtable: {name}")
        else:
            table.create(data)
            print(f">>> [10/10] BERHASIL: Data '{name}' adalah entri baru (Inserted).")
            logging.info(f"Inserted new record in Airtable: {name}")

    except Exception as e:
        print(f"ERROR: Gagal menyimpan data '{data.get('Name')}' ke Airtable: {e}")
        logging.error(f"Error saving to Airtable for {data.get('Name')}: {e}", exc_info=True)


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Test the scraper
    print("\n" + "="*50)
    print("TESTING GOOGLE MAPS SCRAPER BOT")
    print("="*50)
    scrape_google_maps(keyword="kedai kopi", location="Jakarta Selatan", max_results=5)
    print("="*50)
    print("PROGRAM SELESAI")
    print("="*50)
