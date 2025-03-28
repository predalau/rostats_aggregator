import time
import random
import os
import platform
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime


class INSSEScraper:
    def __init__(self, download_dir=None):
        # List of user agents to rotate through
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71",
        ]
        self.current_agent_index = 0
        self.agent_rotation_count = 0
        self.agent_rotation_threshold = 5

        # Setup download directory
        if download_dir is None:
            self.download_dir = os.path.join(os.getcwd(), "insse_downloads")
        else:
            self.download_dir = download_dir

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Initialize the driver
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 30)
        self.actions = ActionChains(self.driver)

    def _setup_driver(self):
        """Set up and return a Chrome WebDriver with configured options."""
        chrome_options = Options()
        chrome_options.add_argument(
            f"user-agent={self.user_agents[self.current_agent_index]}"
        )
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--start-maximized")

        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if platform.system() == "Linux":
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromedriver")
        else:
            service = Service(ChromeDriverManager().install())

        return webdriver.Chrome(service=service, options=chrome_options)

    def _random_delay(self):
        """Wait for a random time between 0.1 and 0.5 seconds."""
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)

    def _maybe_rotate_user_agent(self):
        """Rotate user agent if rotation threshold is reached."""
        self.agent_rotation_count += 1
        if self.agent_rotation_count >= self.agent_rotation_threshold:
            self.agent_rotation_count = 0
            self.current_agent_index = (self.current_agent_index + 1) % len(
                self.user_agents
            )
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": self.user_agents[self.current_agent_index]},
            )
            print(
                f"Rotated to user agent: {self.user_agents[self.current_agent_index][:30]}..."
            )

    def _generate_filename(self, table_code, selected_columns):
        """Generate filename emphasizing the feature over time."""
        # Filter out PERIOADE for the feature name part
        features = [col for col in selected_columns if col != "PERIOADE"]
        feature_str = "_".join([col[:4] for col in features])[:25]
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{table_code}_{feature_str}_OVER_TIME_{timestamp}.csv"

    def _click_table_button(self, table_code):
        """Clicks the table button reliably even if obscured"""
        try:
            # 1. Find the button using precise XPath
            button_xpath = f"//div[@class='historyBarButton']/button[./span[contains(text(), '{table_code}')]]"
            btn = self.wait.until(
                EC.presence_of_element_located((By.XPATH, button_xpath))
            )

            # 2. Scroll the button into center view (not just into view)
            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    behavior: 'auto',
                    block: 'center',
                    inline: 'center'
                });
            """,
                btn,
            )

            # 3. Wait until clickable with explicit timeout
            self.wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))

            # 4. Use JavaScript click to bypass overlay interception
            self.driver.execute_script("arguments[0].click();", btn)

            # 5. Add small delay to ensure action completes
            self._random_delay()

            print(f"✓ Successfully clicked {table_code} button (JS click)")
            return True

        except Exception as e:
            print(f"✗ Critical error clicking {table_code}: {str(e)}")
            return False

    def _click_home_button(self):
        """Clicks the home button reliably even if obscured"""
        try:
            # 1. Find the button using precise XPath
            button_xpath = f"//div[@class='historyBarButton']/button[./span[contains(text(), 'home')]]"
            btn = self.wait.until(
                EC.presence_of_element_located((By.XPATH, button_xpath))
            )

            # 2. Scroll the button into center view (not just into view)
            self.driver.execute_script(
                """
                    arguments[0].scrollIntoView({
                        behavior: 'auto',
                        block: 'center',
                        inline: 'center'
                    });
                """,
                btn,
            )

            # 3. Wait until clickable with explicit timeout
            self.wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))

            # 4. Use JavaScript click to bypass overlay interception
            self.driver.execute_script("arguments[0].click();", btn)

            # 5. Add small delay to ensure action completes
            self._random_delay()

            print(f"✓ Successfully clicked Home button (JS click)")
            return True

        except Exception as e:
            print(f"✗ Critical error clicking Home: {str(e)}")
            return False

    def _rename_downloaded_file(self, expected_filename):
        """Renames the most recently downloaded file to our naming convention"""
        # Wait for download to complete (adjust timing as needed)
        time.sleep(3)

        try:
            # Get list of files in download directory sorted by modification time
            files = glob.glob(os.path.join(self.download_dir, "*"))
            files.sort(key=os.path.getmtime, reverse=True)

            if not files:
                print("✗ No files found in download directory")
                return False

            # Get the most recent file (should be our download)
            newest_file = files[0]

            # Generate new filename with full path
            new_path = os.path.join(self.download_dir, expected_filename)

            # Rename the file
            os.rename(newest_file, new_path)
            print(f"✓ Renamed file to: {expected_filename}")
            return True

        except Exception as e:
            print(f"✗ Error renaming file: {str(e)}")
            return False

    def navigate_to_website(self):
        """Navigate to the INSSE website."""
        print("\n=== Initializing scraping session ===")
        print("Navigating to INSSE website...")
        self.driver.get(
            "http://statistici.insse.ro:8077/tempo-online/#/pages/tables/insse-table"
        )
        time.sleep(3)
        print("✓ Successfully loaded INSSE homepage")

    def navigate_to_table_by_path(self, path_elements):
        """Navigate through the categories to a specific table."""
        print(f"\nNavigating through path: {' > '.join(path_elements)}")
        for element in path_elements:
            self._random_delay()
            try:
                xpath = f"//*[contains(text(), '{element}')]"
                menu_item = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                menu_item.click()
                print(f"✓ Clicked on '{element}'")
            except Exception:
                print(
                    f"⚠ Could not find element '{element}', attempting JavaScript fallback"
                )
                element_found = self.driver.execute_script(
                    """
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {
                        if (allElements[i].textContent.includes(arguments[0])) {
                            allElements[i].scrollIntoView();
                            return allElements[i];
                        }
                    }
                    return null;
                """,
                    element,
                )
                if element_found:
                    self.driver.execute_script("arguments[0].click();", element_found)
                    print(f"✓ Found and clicked '{element}' using JavaScript")
                else:
                    print(f"✗ Failed to find element '{element}'")
                    return False
            self._maybe_rotate_user_agent()
            time.sleep(2)
        return True

    def get_column_names(self):
        """Get names of all available columns."""
        try:
            headers = self.driver.find_elements(
                By.XPATH, "//th[contains(@class, 'label')]"
            )
            return [header.text.strip() for header in headers if header.text.strip()]
        except Exception as e:
            print(f"Error getting column names: {e}")
            return []

    def select_columns(self, columns_to_select):
        """Select specific columns for download, always including PERIOADE."""
        # Add PERIOADE if not already present
        columns_to_select = list(set(columns_to_select + ["PERIOADE"]))
        print(
            f"\nSelecting columns (always including PERIOADE): {', '.join(columns_to_select)}"
        )

        selected_columns = []
        checkboxes = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//th//input[@type='checkbox']")
            )
        )
        available_columns = self.get_column_names()

        # Verify PERIOADE exists before proceeding
        if "PERIOADE" not in available_columns:
            print("⚠ CRITICAL: PERIOADE column not found in table headers")
            return False

        for checkbox, header in zip(checkboxes, available_columns):
            if header in columns_to_select and checkbox.is_displayed():
                try:
                    if not checkbox.is_selected():
                        checkbox.click()
                        selected_columns.append(header)
                        print(f"✓ Selected column: {header}")
                        self._random_delay()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    selected_columns.append(header)
                    print(f"✓ Selected column (JS fallback): {header}")

        # Double-check PERIOADE was selected
        if "PERIOADE" not in selected_columns:
            print("✗ FATAL: Failed to select PERIOADE column")
            return False

        return selected_columns

    def execute_search(self):
        """Click the search button."""
        try:
            search_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Cauta')]")
                )
            )
            search_button.click()
            print("✓ Executed search")
            time.sleep(random.randint(3, 5))
            return True
        except Exception as e:
            print(f"Error clicking search button: {e}")
            return False

    def download_data(self, filename):
        """Download the data as CSV."""
        try:
            download_buttons = self.driver.find_elements(
                By.XPATH, "//img[@alt='Export to CSV']"
            )
            for button in download_buttons:
                if button.is_displayed():
                    button.click()
                    print(f"✓ Triggered download for {filename}")
                    self._rename_downloaded_file(filename)
                    return True
            print("✗ Could not find download button")
            return False
        except Exception as e:
            print(f"Error during download: {e}")
            return False

    def scrape_table(self, table_config):
        """
        Scrape a table with given configuration.

        Args:
            table_config: Dictionary containing:
                - table_code: Table identifier
                - path: Navigation path as list
        """
        print(f"\n=== Starting scrape for table {table_config['table_code']} ===")

        if not self.navigate_to_table_by_path(table_config["path"]):
            print(f"✗ Failed to navigate to table {table_config['table_code']}")
            return False

        # Get all available columns
        all_columns = self.get_column_names()
        if not all_columns:
            print("✗ No columns found in table")
            return False

        # Filter out PERIOADE and non-data columns
        data_columns = [
            col
            for col in all_columns
            if col not in ["PERIOADE", "", " ", " UM: NUMAR PERSOANE "]
            and not col.startswith("_")
        ]

        print(f"Found {len(data_columns)} data columns to process")

        results = []
        for column in data_columns:
            print(f"\n--- Processing column: {column} ---")

            try:
                # Select current column + PERIOADE
                selected = self.select_columns([column])
                if not selected:
                    continue

                if not self.execute_search():
                    continue

                # Generate filename with column name
                filename = self._generate_filename(
                    table_config["table_code"], [column, "PERIOADE"]
                )

                if not self.download_data(filename):
                    continue

                # Click table button to reset selection
                self._click_table_button(table_config["table_code"])
                time.sleep(2)

                results.append(column)
                print(f"✓ Successfully processed {column}")

            except Exception as e:
                print(f"✗ Failed processing {column}: {str(e)}")

        print(f"\nProcessed {len(results)}/{len(data_columns)} columns successfully")
        print("Clicking HOME button...")
        self._click_home_button()
        return len(results) > 0

    def scrape_multiple_tables(self, table_configs):
        """Scrape multiple tables with given configurations."""
        self.navigate_to_website()

        results = {}
        for config in table_configs:
            start_time = time.time()
            success = self.scrape_table(config)
            elapsed = time.time() - start_time
            results[config["table_code"]] = {
                "success": success,
                "time_seconds": round(elapsed, 2),
            }

        print("\n=== Scraping Summary ===")
        for table_code, result in results.items():
            status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
            print(f"{status} - {table_code} ({result['time_seconds']}s)")

        return results

    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            self.driver.quit()
            print("\n=== Browser closed ===")


if __name__ == "__main__":
    # Example configuration for multiple tables
    TABLE_CONFIGS = [
        {
            "table_code": "POP105A",
            "path": ["1. POPULATIA REZIDENTA", "POP105A"],
        },
        {
            "table_code": "POP106A",
            "path": ["1. POPULATIA REZIDENTA", "POP106A"],
        },
        {
            "table_code": "POP109A",
            "path": ["1. POPULATIA REZIDENTA", "POP109A"],
        },
        {
            "table_code": "POP109A",
            "path": ["2. POPULATIA DUPA DOMICILIU", "POP107A"],
        },
    ]

    scraper = INSSEScraper()
    try:
        scraper.scrape_multiple_tables(TABLE_CONFIGS)
    except Exception as e:
        print(f"\n!!! Critical error: {e}")
    finally:
        scraper.close()
