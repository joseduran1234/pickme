

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
from pprint import pprint

import re
from bs4 import BeautifulSoup

import pandas as pd

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
    time.sleep(1)
    
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
    time.sleep(5)

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

# Suggestion : Rename this. This function accesses the url of each project. 
# It does not scrape multiple pages
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
    project_counter = 1
    for title, details in projects.items():
        print('progress = ', 100*project_counter/len(projects), '%')
        project_counter += 1
        project_url = details.get("url")
        if not project_url:
            print(f"No URL found for project: {title}")
            continue
        try:
            # Navigate to the project's page
            driver.get(project_url)
            # Wait for the page to load. Adjust the sleep duration as needed.
            time.sleep(0.5)
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

# Suggestion : rewrite this. Do not include while true. can break.
# Maybe select the first 5 or something?
#def scrape_all_pages(driver):
    """
    Iterates through all pages by clicking the "next" button until the last page is reached.
    On each page, it scrapes the projects and then flips to the next page.
    
    Returns:
        A dictionary with all projects scraped from every page.
    """
    all_projects = {}
    page_number = 1
    while True:
    # UNCOMMENT THIS IF YOU ONLY WANT THE FIRST 5
    # for page_numer in range(1,6):
        print(f"Scraping page {page_number}...")
        # Scrape projects on the current page.
        driver.get('https://actorsaccess.com/projects/?view=breakdowns&region=5&page='+str(page_number))
        projects = get_projects(driver)
        all_projects.update(projects)
        try:
            # **UPDATED:** Try to locate the "next page" button by its CSS class.
            next_button = driver.find_element(By.CSS_SELECTOR, "breakdown_next")
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

# **New function: scrape_page to scrape a single page by page number.**
def scrape_page(driver, page_number):
    url = f"https://actorsaccess.com/projects/?view=breakdowns&region=5&page={page_number}"
    driver.get(url)
    time.sleep(1)  # Wait for the page to load; adjust timing if needed.
    print(f"Scraping page {page_number} at {url}")
    return get_projects(driver)

# #goes through the next page 
# def scrape_all_pages(driver):
#     all_projects = {}
#     page_number = 1
#     while True:
#         projects = scrape_page(driver, page_number)  # Call to scrape_page
#         if not projects:
#             print("No projects found on this page. Reached the last page.")
#             break
#         all_projects.update(projects)
#         page_number += 1
#     return all_projects


def get_last_page_number(driver):
    # Get the current page source from the driver
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # Find the text that matches the pagination pattern, e.g., "Page 1 of 37"
    pagination_text = soup.find(string=re.compile(r"Page\s+\d+\s+of\s+\d+"))
    if pagination_text:
        match = re.search(r"Page\s+\d+\s+of\s+(\d+)", pagination_text)
        if match:
            return int(match.group(1))
    return None

def scrape_all_pages(driver):
    all_projects = {}
    # Determine the last page dynamically.
    last_page = get_last_page_number(driver)
    if last_page is None:
        print("Unable to determine the last page number. Exiting scrape.")
        return all_projects

    page_number = 1
    while page_number <= last_page:
        projects = scrape_page(driver, page_number)
        if not projects:
            print(f"No projects found on page {page_number}. Ending scrape.")
            break
        all_projects.update(projects)
        print(f"Scraped page {page_number} of {last_page}")
        page_number += 1

    return all_projects


def create_excel_from_projects(projects_dict, file_name="scraped_projects.xlsx"):
    """
    Converts a projects dictionary into a pandas DataFrame and writes it to an Excel file.
    
    Args:
        projects_dict (dict): Dictionary where each key is the project title and the value is
                              another dictionary containing project details.
        file_name (str): The output Excel file name. Defaults to "scraped_projects.xlsx".
    
    Returns:
        None. The function writes the Excel file to disk.
    """
    # Convert the projects dictionary into a list of dictionaries.
    # Here, we ensure the project title (key) is also stored in the dictionary.
    data_list = []
    for title, details in projects_dict.items():
        # Add title to details if not already present.
        details["title"] = title
        data_list.append(details)
    
    # Create a DataFrame from the list.
    df = pd.DataFrame(data_list)
    
    # Optionally, reorder the columns.
    # desired_columns = ["title", "date", "url", "type", "casting_director", "start_date", "union", "page_text"]
    desired_columns = ['title', 'casting_director', 'union', 'date', 'start_date', 'type',  'url', 'page_text']
    # Only include columns that are present in the DataFrame.
    columns_to_use = [col for col in desired_columns if col in df.columns]
    df = df[columns_to_use]
    
    # Save the DataFrame to an Excel file.
    df.to_excel(file_name, index=False)
    print(f"Excel file '{file_name}' created with {len(df)} records.")



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
    
    # projects = get_projects(driver)
    # projects = scrape_project_pages(driver, projects)
    # all_projects = scrape_project_pages(driver, projects)

    #project_dictionary = scrape_all_pages(driver)
    # **Phase 2: Scrape listings across all pages using scrape_all_pages.**
    all_project_listings = scrape_all_pages(driver)
    print(f"Total projects scraped from listings: {len(all_project_listings)}")
    all_projects = scrape_project_pages(driver, all_project_listings)
    create_excel_from_projects(all_projects)
    # pprint(all_projects)
    # Close the browser
    close_browser(driver)



# ... after scraping projects
# pprint(projects)
