

#Download the WebDriver for your browser and import the necessary modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Function to open the browser in full-screen mode
def open_browser_in_full_screen(url):
    # Setup Chrome options
    options = Options()
    options.add_argument("--start-maximized")  # Ensures the browser starts maximized
    
    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Open the specified URL
    driver.get(url)
    
    # Wait to make sure the page loads (you can adjust this depending on your network speed)
    time.sleep(3)
    
    # Maximize the window just in case it's not fully expanded
    driver.maximize_window()
    
    print(f"Browser opened in full screen, navigating to {url}")
    
    return driver


#Login Function 
def login(driver, username, password):
    # Locate the username and password fields
    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")
    
    # Enter the credentials
    username_field.send_keys(username)
    password_field.send_keys(password)
    
    # Submit the form
    password_field.send_keys(Keys.RETURN)
    
    # Wait for the login process to complete
    time.sleep(15)

#Close Browser Function
def close_browser(driver):
    driver.quit()

# Function to get the project data from the breakdowns page
def get_projects(driver):
    """
    Scrapes project data from the breakdowns page using Selenium.
    
    Args:
        driver: A Selenium WebDriver instance with the page already loaded.
        
    Returns:
        A dictionary where each key is the project title and the value is another
        dictionary with details about the project.
    """
    projects = {}
    # Find all project rows (each row has the class "element")
    project_rows = driver.find_elements(By.CSS_SELECTOR, "tr.element")
    
    for row in project_rows:
        try:
            # Extract details from each cell in the row.
            date = row.find_element(By.CSS_SELECTOR, "td.bd_date").text.strip()
            title = row.find_element(By.CSS_SELECTOR, "td.bd_title").text.strip()
            type_project = row.find_element(By.CSS_SELECTOR, "td.bd_type").text.strip()
            casting_director = row.find_element(By.CSS_SELECTOR, "td.bd_castdir").text.strip()
            start_date = row.find_element(By.CSS_SELECTOR, "td.bd_start").text.strip()
            union = row.find_element(By.CSS_SELECTOR, "td.bd_union").text.strip()
            
            # Find the title cell and extract the URL from the <a> element within it.
            title_cells = row.find_elements(By.CSS_SELECTOR, "td.bd_title")
            if not title_cells:
                print("No title cell found, skipping row.")
                continue
            title_element = title_cells[0]

            # Extract the URL from the <a> element within the title cell.
            url = title_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            type_project = row.find_element(By.CSS_SELECTOR, "td.bd_type").text.strip()
            casting_director = row.find_element(By.CSS_SELECTOR, "td.bd_castdir").text.strip()
            start_date = row.find_element(By.CSS_SELECTOR, "td.bd_start").text.strip()
            union = row.find_element(By.CSS_SELECTOR, "td.bd_union").text.strip()
           
            # Create a dictionary for the project
            project_details = {
                "date": date,
                "title": title,
                "url": url,
                "type": type_project,
                "casting_director": casting_director,
                "start_date": start_date,
                "union": union
            }
            
            # Store in the projects dictionary using the title as the key.
            projects[title] = project_details
            
        except Exception as e:
            # If any element is not found or an error occurs, print the error and skip this row.
            print(f"Error extracting project data: {e}")
            continue
    
    return projects

# Example usage:
# from selenium import webdriver
# driver = webdriver.Chrome()
# driver.get("https://actorsaccess.com/projects/?view=breakdowns&region=5")
# projects = get_projects(driver)
# print(projects)

def scrape_project_pages(driver, projects):
    """
    For each project in the projects dictionary, navigates to the project's URL
    and scrapes all the text from the page.

    Args:
        driver: A Selenium WebDriver instance.
        projects: A dictionary of projects, each having a "url" key.

    Returns:
        The updated projects dictionary with an additional "page_text" key for each project.
    """
    for title, details in projects.items():
        project_url = details.get("url")
        if not project_url:
            print(f"No URL found for project: {title}")
            continue
        try:
            # Navigate to the project's page
            driver.get(project_url)
            # Wait for the page to load. Adjust the sleep duration as needed.
            time.sleep(1)
            # Scrape all text from the page (for example, the text in the <body> tag)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            # Add the scraped text to the project's details
            details["page_text"] = page_text
            print(f"Scraped text for project: {title}")
        except Exception as e:
            print(f"Error scraping text from {project_url}: {e}")
            details["page_text"] = None
    return projects

# Scrape all pages by clicking the "next" button until the last page is reached.
def scrape_all_pages(driver):
    """
    Iterates through all pages by clicking the "next" button until the last page is reached.
    On each page, it scrapes the projects and then flips to the next page.
    
    Returns:
        A dictionary with all projects scraped from every page.
    """
    all_projects = {}
    page_number = 1
    while True:
        print(f"Scraping page {page_number}...")
        # Scrape projects on the current page.
        projects = get_projects(driver)
        all_projects.update(projects)
        
        try:
            # **UPDATED:** Try to locate the "next page" button by its CSS class.
            next_button = driver.find_element(By.CSS_SELECTOR, "a.aa-projects-next")
            # Check if the next button is disabled (this depends on how the site indicates a disabled state)
            if "disabled" in next_button.get_attribute("class"):
                print("Next button is disabled; reached the last page.")
                break
            
            # Click the next button to go to the next page.
            next_button.click()
            page_number += 1
            time.sleep(1)  # Wait for the new page to load.
        except Exception as e:
            print(f"Error finding or clicking next page: {e}")
            break
    return all_projects

#Main Execution (Use the defined functions to perform the login automation)
if __name__ == "__main__":
    # url = "https://actorsaccess.com/actor/"
    url = "https://actorsaccess.com/projects/?view=breakdowns&region=5"
    username = "jgd12345"
    password = "jded123456789"
    
    # Open the browser and navigate to the login page
    driver = open_browser_in_full_screen(url)
    
    # Perform login
    login(driver, username, password)
    
    projects = get_projects(driver)
    projects = scrape_project_pages(driver, projects)
    all_projects = scrape_project_pages(driver, get_projects)
    print(projects)
    
    # Close the browser
    close_browser(driver)

    from pprint import pprint

# ... after scraping projects
pprint(projects)
