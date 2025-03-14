from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

import re
from bs4 import BeautifulSoup, NavigableString

import pandas as pd

###############################################################################
# BROWSER & LOGIN
###############################################################################

def open_browser_in_full_screen(url):
    """
    Opens a Chrome browser in full-screen mode and navigates to the given URL.
    """
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(1)
    driver.maximize_window()
    print(f"Browser opened in full screen, navigating to {url}")
    return driver

def login(driver, username, password):
    """
    Logs into the site by filling out username and password fields 
    and pressing RETURN on the password field.
    """
    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")
    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(5)
    print("Login process completed.")


def close_browser(driver):
    """
    Closes the Selenium browser.
    """
    driver.quit()

###############################################################################
# SCRAPING BREAKDOWNS LISTING
###############################################################################

def get_projects(driver):
    """
    Scrapes basic project data (title, date, etc.) from the current breakdowns page.
    Returns a dictionary: { project_title: project_details, ... }
    """
    projects = {}
    # Find all project rows (each row has the class "element")
    project_rows = driver.find_elements(By.CSS_SELECTOR, "tr.element")
    
    for row in project_rows:
        try:
            date = row.find_element(By.CSS_SELECTOR, "td.bd_date").text.strip()
            title = row.find_element(By.CSS_SELECTOR, "td.bd_title").text.strip()
            type_project = row.find_element(By.CSS_SELECTOR, "td.bd_type").text.strip()
            casting_director = row.find_element(By.CSS_SELECTOR, "td.bd_castdir").text.strip()
            start_date = row.find_element(By.CSS_SELECTOR, "td.bd_start").text.strip()
            union = row.find_element(By.CSS_SELECTOR, "td.bd_union").text.strip()
            # Extract the URL from the <a> element in bd_title
            title_cells = row.find_elements(By.CSS_SELECTOR, "td.bd_title")
            if not title_cells:
                print("No title cell found, skipping row.")
                continue
            title_element = title_cells[0]
            url = title_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            # Create a dictionary for the project
            project_details = {
                "date": date,
                "title": title,
                "url": url,
                "type": type_project,
                "casting_director": casting_director,
                "start_date": start_date,
                "union": union,
            }
            # Store by project title
            projects[title] = project_details
        except Exception as e:
            print(f"Error extracting project data: {e}")
            continue
    
    return projects


def scrape_page(driver, page_number):
    """
    Navigates to a specific page in the breakdowns listing (by page_number),
    and returns all projects on that page using get_projects().
    """
    url = f"https://actorsaccess.com/projects/?view=breakdowns&region=5&page={page_number}"
    driver.get(url)
    time.sleep(1)  # Wait for the page to load
    print(f"Scraping page {page_number} at {url}")
    return get_projects(driver)


def get_last_page_number(driver):
    """
    Tries to detect pagination info from the phrase 'Page X of Y' on the page 
    and returns Y (the last page number) as an integer. 
    If not found, returns None.
    """
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    pagination_text = soup.find(string=re.compile(r"Page\s+\d+\s+of\s+\d+"))
    if pagination_text:
        match = re.search(r"Page\s+\d+\s+of\s+(\d+)", pagination_text)
        if match:
            return int(match.group(1))
    return None


def scrape_all_pages(driver):
    """
    Uses get_last_page_number(driver) to find how many pages exist, then loops
    through them all, calling scrape_page() each time. Merges all found projects
    into one big dictionary.
    """
    all_projects = {}
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

###############################################################################
# ROLE-PARSING LOGIC
###############################################################################

def extract_roles_with_description(html):
    """
    Extracts roles from the breakdown page HTML.
    Each role is found by <a class="breakdown-open-add-role">ROLE NAME</a>.
    Then we collect the text that follows (until the next <p>) as the description.
    
    Returns a list of dicts: [ {"role": "ROLE NAME", "description": "..."} , ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    roles_info = []
    
    for anchor in soup.find_all("a", class_="breakdown-open-add-role"):
        role_name = anchor.get_text(strip=True)
        description = ""
        # The immediate <br> after the anchor is where the role's text starts.
        br = anchor.find_next("br")
        if br:
            sibling = br.next_sibling
            while sibling and (not hasattr(sibling, "name") or sibling.name != "p"):
                if isinstance(sibling, NavigableString):
                    text = sibling.strip()
                    if text:
                        description += text + " "
                else:
                    text = sibling.get_text(strip=True)
                    if text:
                        description += text + " "
                sibling = sibling.next_sibling
            description = description.strip()
        roles_info.append({"role": role_name, "description": description})
    return roles_info

###############################################################################
# SCRAPE PROJECT PAGES & PARSE ROLES
###############################################################################

def scrape_project_pages(driver, projects):
    """
    For each project in 'projects', navigates to the project's URL, pulls the HTML,
    extracts the text, and parses out roles. Stores the roles in details["roles"].
    
    Returns the updated 'projects' dict, with an added "page_text" and "roles" key.
    """
    project_counter = 1
    num_projects = len(projects)
    for title, details in projects.items():
        print(f"Scraping project page for '{title}' ({project_counter}/{num_projects})")
        project_counter += 1

        project_url = details.get("url")
        if not project_url:
            print(f"No URL found for project: {title}")
            details["page_text"] = None
            details["roles"] = []
            continue

        try:
            driver.get(project_url)
            time.sleep(1)  # Adjust as needed
            page_html = driver.page_source  # full HTML
            page_text = driver.find_element(By.TAG_NAME, "body").text

            details["page_text"] = page_text
            # Parse roles from the HTML
            roles = extract_roles_with_description(page_html)
            details["roles"] = roles

            print(f"Found {len(roles)} roles for '{title}'")

        except Exception as e:
            print(f"Error scraping text/roles from {project_url}: {e}")
            details["page_text"] = None
            details["roles"] = []

    return projects

###############################################################################
# CREATE EXCEL - ONE ROW PER ROLE
###############################################################################

def create_excel_from_roles(projects_dict, file_name="scraped_roles.xlsx"):
    """
    Creates an Excel spreadsheet with ONE ROW PER ROLE.
    Flattens all roles across all projects. Each row includes:
      - Project-level data (title, casting_director, union, date, start_date, type, url, page_text)
      - Role-level data (role name, role description).
    """
    rows = []
    for project_title, details in projects_dict.items():
        # Pull out project-level fields
        casting_director = details.get("casting_director", "")
        union_status = details.get("union", "")
        proj_date = details.get("date", "")
        start_date = details.get("start_date", "")
        proj_type = details.get("type", "")
        proj_url = details.get("url", "")
        page_text = details.get("page_text", "")

        # The roles we parsed
        roles = details.get("roles", [])
        
        # If no roles are found, optionally add a single row with blank role data
        if not roles:
            rows.append({
                "project_title": project_title,
                "role_name": "",
                "role_description": "",
                "casting_director": casting_director,
                "union": union_status,
                "date": proj_date,
                "start_date": start_date,
                "type": proj_type,
                "url": proj_url,
                "page_text": page_text
            })
        else:
            # One row per role
            for r in roles:
                rows.append({
                    "project_title": project_title,
                    "role_name": r.get("role", ""),
                    "role_description": r.get("description", ""),
                    "casting_director": casting_director,
                    "union": union_status,
                    "date": proj_date,
                    "start_date": start_date,
                    "type": proj_type,
                    "url": proj_url,
                    "page_text": page_text
                })

    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # Reorder columns as desired
    desired_columns = [
        "project_title", "role_name", "role_description",
        "casting_director", "union", "date", "start_date",
        "type", "url", "page_text"
    ]
    columns_to_use = [c for c in desired_columns if c in df.columns]
    df = df[columns_to_use]

    # Save to Excel
    df.to_excel(file_name, index=False)
    print(f"Excel file '{file_name}' created with {len(df)} role records.")

###############################################################################
# OPTIONAL: SCRAPE LIMITED PAGES FOR TESTING
###############################################################################

def test_scrape_limited_pages(driver, num_pages=2):
    """
    Scrapes only the first 'num_pages' pages for testing purposes.
    Returns a dict of {title: details} for those pages.
    """
    test_projects = {}
    for i in range(1, num_pages + 1):
        print(f"Scraping test page {i}...")
        projects = scrape_page(driver, i)
        test_projects.update(projects)
        time.sleep(1)
    print(f"Total test projects scraped: {len(test_projects)}")
    return test_projects

###############################################################################
# MAIN EXECUTION
###############################################################################

if __name__ == "__main__":
    url = "https://actorsaccess.com/projects/?view=breakdowns&region=5"
    username = "jgd12345"
    password = "jded123456789"

    # Set True for scraping just a few pages (test run); False for full scrape
    test_mode = True

    # 1) Open the browser & log in
    driver = open_browser_in_full_screen(url)
    login(driver, username, password)

    # 2) Gather listings
    if test_mode:
        # Scrape only the first 2 pages, as an example
        limited_project_listings = test_scrape_limited_pages(driver, num_pages=2)
        print(f"Total projects scraped from limited run: {len(limited_project_listings)}")

        # Then visit each project page, parse roles
        all_projects = scrape_project_pages(driver, limited_project_listings)

        # Create the Excel with one row per role
        create_excel_from_roles(all_projects, file_name="test_scraped_roles.xlsx")

    else:
        # Full multi-page scrape
        all_project_listings = scrape_all_pages(driver)
        print(f"Total projects scraped from all pages: {len(all_project_listings)}")

        # Then visit each project page, parse roles
        all_projects = scrape_project_pages(driver, all_project_listings)

        # Create the Excel with one row per role
        create_excel_from_roles(all_projects, file_name="all_scraped_roles.xlsx")

    # 3) Close the browser
    close_browser(driver)