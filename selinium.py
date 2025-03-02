

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
            
            # Create a dictionary for the project
            project_details = {
                "date": date,
                "title": title,
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

    print(get_projects(driver))
    
    # Close the browser
    close_browser(driver)