import time
import random
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


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
        self.agent_rotation_threshold = 5  # Change user agent every 5 actions

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

        chromium_path = "/usr/bin/chromium"
        chromedriver_path = "/usr/bin/chromedriver"

        chrome_options = Options()

        chrome_options.add_argument(
            f"user-agent={self.user_agents[self.current_agent_index]}"
        )
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument(
            "--start-maximized"
        )  # Important for pixel-based interactions

        # Set download directory
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if platform.system() == "Linux":
            chrome_options.binary_location = chromium_path
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver

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

            # Update user agent
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": self.user_agents[self.current_agent_index]},
            )
            print(
                f"Rotated to user agent: {self.user_agents[self.current_agent_index][:30]}..."
            )

    def navigate_to_website(self):
        """Navigate to the INSSE website."""
        print("Navigating to INSSE website...")
        self.driver.get(
            "http://statistici.insse.ro:8077/tempo-online/#/pages/tables/insse-table"
        )
        time.sleep(3)  # Allow page to fully load
        print("Successfully loaded INSSE homepage")

    def navigate_to_table_by_path(self, path_elements):
        """
        Navigate through the categories to a specific table based on the elements in the path.

        Args:
            path_elements: List of strings representing the menu items to click
        """
        try:
            print(f"Navigating through path: {path_elements}")

            for element in path_elements:
                self._random_delay()

                # Try to find the element by text
                try:
                    xpath = f"//*[contains(text(), '{element}')]"
                    menu_item = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    menu_item.click()
                    print(f"Clicked on '{element}'")
                except (TimeoutException, NoSuchElementException):
                    print(
                        f"Could not find element '{element}' by text, trying alternative approach"
                    )

                    # If we couldn't find the element by text, use JavaScript to find elements
                    # that might contain the text in any attribute or content
                    script = """
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {
                      var element = allElements[i];
                      if (element.textContent.includes(arguments[0])) {
                        element.scrollIntoView();
                        return element;
                      }
                    }
                    return null;
                    """
                    element_found = self.driver.execute_script(script, element)

                    if element_found:
                        self.driver.execute_script(
                            "arguments[0].click();", element_found
                        )
                        print(f"Found and clicked '{element}' using JavaScript")
                    else:
                        print(
                            f"Failed to find element '{element}' even with JavaScript"
                        )

                self._maybe_rotate_user_agent()
                time.sleep(2)  # Wait for page transition

            print("Navigation completed successfully")
            return True
        except Exception as e:
            print(f"Error during navigation: {e}")
            return False

    def navigate_to_table_by_search(self, table_code):
        """
        Search for a specific table by its code.

        Args:
            table_code: String representing the table code (e.g., "POP105A")
        """
        try:
            print(f"Searching for table: {table_code}")

            # Wait for the page to be fully loaded
            time.sleep(3)

            # Try to find the search field
            search_fields = self.driver.find_elements(By.XPATH, "//input[@type='text']")
            search_field = None

            # Find the search field that's visible
            for field in search_fields:
                if field.is_displayed():
                    search_field = field
                    break

            if search_field:
                search_field.clear()
                search_field.send_keys(table_code)
                print(f"Entered search term: {table_code}")
                self._random_delay()

                # Try to find and click a button or element that might be the search button
                search_buttons = self.driver.find_elements(By.XPATH, "//button")
                for button in search_buttons:
                    if button.is_displayed() and (
                        "search" in button.get_attribute("class").lower()
                        or "cauta" in button.get_attribute("class").lower()
                    ):
                        button.click()
                        print("Clicked search button")
                        time.sleep(2)
                        break

                # Now try to find the table in the results
                table_elements = self.driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{table_code}')]"
                )
                for element in table_elements:
                    if element.is_displayed():
                        element.click()
                        print(f"Found and clicked on table: {table_code}")
                        time.sleep(3)  # Wait for table to load
                        return True

                print(f"Could not find table {table_code} in search results")
            else:
                print("Could not find search field")

            return False
        except Exception as e:
            print(f"Error during table search: {e}")
            return False

    def select_parameter(self, checkbox):
        """Select all parameters for a table."""
        try:
            print("Selecting parameter")

            # Wait for the checkboxes to be present
            checkboxes = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//input[@type='checkbox']")
                )
            )
            # Check all checkboxes that are visible and unchecked

            if checkbox.is_displayed() and not checkbox.is_selected():
                try:
                    self._random_delay()
                    checkbox.click()
                    self._maybe_rotate_user_agent()
                except Exception as e:
                    print(e)
                    # If direct click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", checkbox)

            print(f"Selected {checkbox.text} parameter")

        except Exception as e:
            print(f"Error selecting parameters: {e}")
            return False

    def click_cauta_button(self):
        """Attempt to click the cauta button"""
        try:
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Cauta')]")
                )
            )

            search_button.click()

            # Optional: Add a delay to observe the action

            print("Clicked CAUTA button")
            time.sleep(random.randint(3, 5))  # Longer wait for results to load
            return True
        except Exception as e:
            print(f"Error clicking cauta button: {e}")
            return False

    def click_table_code_button(self, table_code):
        """Attempt to click the cauta button"""
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(text(), '{table_code}')]")
                )
            )
            search_button.click()
            print(f"Clicked {table_code} button")
            time.sleep(random.randint(3, 5))  # Longer wait for results to load
            return True
        except Exception as e:
            print(f"Error clicking table code button: {e}")
            return False

    def click_download_button(self):
        """Attempt to click the download button using multiple methods."""
        try:
            print("Attempting to download data...")

            # Method 1: Try to find buttons with download-related classes or text
            download_buttons = self.driver.find_elements(
                By.XPATH,
                "//img[@alt='Export to CSV']",
            )

            for button in download_buttons:
                if button.is_displayed():
                    self._random_delay()
                    button.click()
                    print("Clicked on download button")
                    self._maybe_rotate_user_agent()
                    time.sleep(3)

            print("Could not find download button using standard methods")
            return False
        except Exception as e:
            print(f"Error during download: {e}")
            return False

    def iterate_and_download_table(self, table_code):
        checkboxes = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//th//input[@type='checkbox']")
            )
        )
        categories = []
        # Check all checkboxes that are visible and unchecked
        for checkbox in checkboxes:
            if checkbox.is_displayed() and not checkbox.is_selected():
                categories.append(checkbox)
        print("NUMBER OF CATEGORIES IS: ", len(categories))
        always_check_category = categories[-2]
        for cat in categories[:-2]:
            try:
                self._random_delay()
                print("Clicking column Category:")
                cat.click()
                self._random_delay()
                print("Clicking Periods Category: ")
                always_check_category.click()
                # click cauta button
                self.click_cauta_button()
                # Download the data
                self.click_download_button()
                self.click_table_code_button(table_code)
                self._maybe_rotate_user_agent()

            except:
                # If direct click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", checkbox)

    def scrape_table(self, table_code, pixel_coords=None):
        """
        Complete process to scrape a specific table.

        Args:
            table_code: The code of the table to scrape
            pixel_coords: Optional dictionary of pixel coordinates for various UI elements
        """
        self.navigate_to_website()

        # Try navigation methods in order of preference
        success = False
        # Method 2: Try to navigate by predefined path
        if not success:
            path = [
                "A. STATISTICA SOCIALA",
                "POPULATIE SI STRUCTURA DEMOGRAFICA",
                "POPULATIA REZIDENTA",
                table_code,
            ]
            success = self.navigate_to_table_by_path(path)

        table_download_success = self.iterate_and_download_table(table_code)

        print(f"Scraping of table {table_code} completed")
        return True

    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            self.driver.quit()
            print("Browser closed")


def scrape_multiple_tables(table_codes, pixel_coordinates=None):
    """
    Scrape multiple tables from INSSE.

    Args:
        table_codes: List of table codes to scrape
        pixel_coordinates: Optional dictionary of pixel coordinates
    """
    scraper = INSSEScraper()

    try:
        for table_code in table_codes:
            print(f"\n--- Starting scrape of table {table_code} ---")
            scraper.scrape_table(table_code, pixel_coordinates)
            time.sleep(3)  # Wait between tables
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    # List of tables to scrape
    tables = ["POP105A", "POP106A", "POP109A"]

    # You may need to adjust these coordinates based on your screen resolution
    # These are example values and should be calibrated for your specific setup
    pixel_coords = {
        "search_box": {"x": 700, "y": 325},
        "search_button": {"x": 150, "y": 425},
        "table_result": {"x": 500, "y": 390},
        "column_selectors": [
            {"x": 170, "y": 430},  # Age groups
            {"x": 340, "y": 430},  # Sex
            {"x": 510, "y": 430},  # Residence
            {"x": 680, "y": 430},  # Regions
            {"x": 850, "y": 430},  # Years
        ],
        "download_button": {"x": 150, "y": 535},
        "csv_format": {"x": 185, "y": 535},
    }

    scrape_multiple_tables(tables, pixel_coords)
