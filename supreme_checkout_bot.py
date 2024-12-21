import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import random
from selenium.webdriver.common.action_chains import ActionChains

# Webhook-URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1320068511388930108/-tWaD_VjRVZRSf0J_Bd-C3Elftx_2QXroEICssfzUQ4bIAkBOK_u_4_P9diSl_Yhuanb"

# def setup_webdriver():
#     chrome_options = Options()

#     # Dein eigenes Chrome-Profil verwenden
#     user_data_dir = "/Users/tobiasmankel/Library/Application Support/Google/Chrome"  # Pfad zu deinem Chrome-Profil
#     chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

#     # Wähle das gewünschte Profil, falls du mehrere hast
#     chrome_profile = "Profile 10"  
#     chrome_options.add_argument(f"--profile-directory={chrome_profile}")

#     # User-Agent ändern (optional)
#     user_agent = (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/96.0.4664.45 Safari/537.36"
#     )
#     chrome_options.add_argument(f"user-agent={user_agent}")

#     # Standard Webdriver-Optionen
#     # chrome_options.add_argument("--headless")  # Headless-Modus deaktivieren, wenn GUI benötigt wird
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")

#     # Webdriver initialisieren
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     return driver

def setup_webdriver():
    chrome_options = Options()

    # User-Agent ändern
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/96.0.4664.45 Safari/537.36"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")  # Setze einen echten User-Agent

    # Standard Webdriver-Optionen
    # chrome_options.add_argument("--headless")  # Deaktiviere für GUI-Tests
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Webdriver initialisieren
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def send_to_discord(message, embed=None):
    """Sendet eine Nachricht an Discord über die Webhook-URL."""
    data = {"content": message}
    if embed:
        data["embeds"] = [embed]
    
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Nachricht erfolgreich an Discord gesendet.")
    else:
        print(f"Fehler beim Senden an Discord: {response.status_code}, {response.text}")

def locate_product_by_multiple_keywords(driver, website, primary_keyword, secondary_keywords):
    try:
        # Website aufrufen
        driver.get(website)

        wait = WebDriverWait(driver, 10)

        # Suche nach allen `<img>`-Elementen mit relevanten Produktinformationen
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        print(f"{len(img_elements)} <img>-Tags auf der Seite gefunden.")

        # Extrahiere alle `alt`-Attribute (Produktnamen)
        all_alts = [img.get_attribute("alt") for img in img_elements if img.get_attribute("alt")]
        print("Alle gefundenen 'alt'-Attribute:")

        # Filtere Produkte mit dem primären Schlagwort
        print(f"Suche nach Produkten mit dem primären Schlagwort: '{primary_keyword}'")
        filtered_primary = [alt for alt in all_alts if primary_keyword.lower() in alt.lower()]
        print(f"{len(filtered_primary)} Produkte mit dem primären Schlagwort gefunden.")
        print(filtered_primary)

        if not filtered_primary:
            print(f"Keine Produkte mit dem primären Schlagwort '{primary_keyword}' gefunden.")
            return False

        # Filtere weiter nach den sekundären Schlagwörtern
        print("Filtere weiter nach sekundären Schlagwörtern...")
        for alt in filtered_primary:
            print(f"Überprüfe Produkt: {alt}")

            # Überprüfen, ob das Produkt alle sekundären Schlagworte enthält
            if all(keyword.lower() in alt.lower() for keyword in secondary_keywords):
                print(f"Produkt gefunden: {alt}")

                # Suche das zugehörige `<a>`-Element basierend auf dem Bild-Alt-Attribut
                matching_element = driver.find_element(
                    By.XPATH,
                    f"//img[@alt='{alt}']/ancestor::a[contains(@data-testid, 'react-router-link')]"
                )

                # Scrollen und das `<a>`-Element anklicken
                driver.execute_script("arguments[0].scrollIntoView(true);", matching_element)
                time.sleep(1)

                try:
                    matching_element.click()
                except Exception as e:
                    print(f"Fehler beim Anklicken des Produkts: {e}")
                    # Fallback: Klick per JavaScript
                    driver.execute_script("arguments[0].click();", matching_element)

                return True

        print("Kein Produkt gefunden, das alle Bedingungen erfüllt.")
        return False

    except Exception as e:
        print(f"Fehler beim Lokalisieren des Produkts: {e}")
        return False
    
def locate_product_add_to_chart_check_out(driver, website, primary_keyword, secondary_keywords):
    wait = WebDriverWait(driver, 10)
    try:
        # Schritt 1: Produkt finden
        product_found = locate_product_by_multiple_keywords(driver, website, primary_keyword, secondary_keywords)
        if not product_found:
            send_to_discord("Kein Produkt gefunden, das alle Bedingungen erfüllt.")
            driver.quit()
            return

        try:
            # Schritt 2: Größen-Dropdown finden
            dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//select[@data-testid='size-dropdown']"))
            )
            options = dropdown.find_elements(By.TAG_NAME, "option")  # Alle <option>-Elemente im Dropdown
            available_sizes = [option.text.strip() for option in options]  # Extrahiere die verfügbaren Größen
            print("Verfügbare Größen:", available_sizes)

            # Schritt 3: Zufällige oder priorisierte Größe auswählen
            if available_sizes:
                select = Select(dropdown)
                sizes_priority = ["Large", "Medium", "XLarge", "Small"]  # Prioritätsliste der Größen

                size_selected = None
                for size in sizes_priority:
                    try:
                        select.select_by_visible_text(size)
                        size_selected = size
                        print(f"Größe {size} ausgewählt.")
                        break
                    except Exception:
                        print(f"Größe {size} nicht verfügbar. Versuche die nächste Größe.")

                if size_selected:
                    # Dropdown-Ereignis auslösen
                    driver.execute_script("""
                        let selectElement = arguments[0];
                        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
                    """, dropdown)

                    print(f"Größe {size_selected} im Dropdown ausgewählt.")
                else:
                    print("Keine gewünschte Größe verfügbar.")
                    send_to_discord("Keine verfügbare Größe gefunden.")
                    driver.quit()
                    return

            else:
                print("Keine verfügbaren Größen im Dropdown gefunden.")
                send_to_discord("Keine verfügbaren Größen im Dropdown gefunden.")
                driver.quit()
                return

            # Schritt 4: "Add to Cart"-Button klicken
            add_to_cart_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='add-to-cart-button']"))
            )
            add_to_cart_button.click()
            print("Produkt erfolgreich in den Warenkorb gelegt.")

            checkout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/checkout' and @aria-label='Supreme Checkout']")))
            checkout_button.click()
            ##CAPTCHA lösen
        



        except Exception as e:
            print(f"Fehler beim Auswählen der Größe oder Hinzufügen zum Warenkorb: {e}")
            send_to_discord(f"Fehler: {e}")
            driver.quit()

    except Exception as e:
        print(f"Fehler beim Lokalisieren des Produkts: {e}")
        send_to_discord(f"Fehler: {e}")
    

if __name__ == "__main__":
    # Webdriver starten
    driver = setup_webdriver()

    # URL und Schlüsselwörter
    supreme_url = "https://eu.supreme.com/collections/new"
    primary_keyword = "Spyder"
    secondary_keywords = ["Technical"]

    # Produkt suchen und in den Warenkorb legen
    locate_product_add_to_chart_check_out(driver, supreme_url, primary_keyword, secondary_keywords)

    time.sleep(10)
    driver.quit()


