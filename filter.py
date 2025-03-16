# The goal of this file is to take the spreadsheet scraped roles and to return some output to determine which are good roles for a 
# specific actor.
# How will we do this? 
# 1. We have a google form with info on the actor (Still need to determine all the characteristics we want to check)
# 2. We will take the information from the google form into a string
# 3. We will use that string as a unique descriptor of that actor
# 4. We will compare that descriptor (of an actor), with the data of each role in scraped roles (excel spreadsheet)
# 5. We will use ChatGPT to make this comparison
# 6. We need to determine an output for this filtering process (probably create a new spreadsheet).
# FUNCTIONS (DATA IN AND OUT):
#  INPUT                                                            OUTPUT
#  GOOGLE FORM                                                  ->  unique descriptor (python string)
#  Unique descriptor (string) + role data (excel)               ->  Match Percentage (float)    (using ChatGPT)
#  Match percentage                                                 New spreadsheet


from selinium import *
import openai


# Definitely need to rework this when we get a google form final version
def get_actor_descriptor_from_google_form(form_filename):
    """
    Example function to read data from a file containing Google Form responses 
    (CSV, XLSX, or otherwise) and convert it to a single descriptor string.

    You must adapt this function to your real data format.
    Below is just a placeholder example for demonstration.
    """
    # Example: Suppose the Google Form responses are in a CSV with columns 
    # ["Timestamp", "Name", "Age", "Gender", "Ethnicity", "Skills", "Notes"]
    try:
        df_form = pd.read_csv(form_filename)
        # Or if it's Excel: df_form = pd.read_excel(form_filename)

        # Let's just pick the first row as the "actor" we care about:
        row = df_form.iloc[0]

        # Combine the relevant data into one descriptor string
        descriptor = (
            f"Name: {row.get('Name','')}, "
            f"Age: {row.get('Age','')}, "
            f"Gender: {row.get('Gender','')}, "
            f"Ethnicity: {row.get('Ethnicity','')}, "
            f"Skills: {row.get('Skills','')}, "
            f"Additional Info: {row.get('Notes','')}"
        )
        return descriptor

    except Exception as e:
        print(f"Error reading form data: {e}")
        return ""


###############################################################################
# 8) USE CHATGPT TO COMPARE DESCRIPTOR WITH ROLE DESCRIPTION & RETURN PERCENT
###############################################################################

# I think this needs almost no changes.
def get_match_percentage(actor_descriptor, role_description):
    """
    Uses the ChatGPT (OpenAI) API to compare the actor descriptor with a role 
    description and return a match percentage (0 to 100).
    This is a demonstration prompt. You should refine it to meet your needs.
    """
    # Construct a prompt that instructs ChatGPT to output a numeric percentage
    prompt = (
        "Given the following actor description and a character/role description, "
        "estimate how well the actor matches the role. "
        "Respond with a single integer between 0 and 100.\n\n"
        f"Actor Description: {actor_descriptor}\n"
        f"Role Description: {role_description}\n"
        "Match Percentage:"
    )

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # or whichever model you prefer
            prompt=prompt,
            max_tokens=3,      # We only need a short integer response
            temperature=0.3
        )
        # Attempt to parse an integer from the response
        text_out = response.choices[0].text.strip()
        # Remove any stray non-digit characters
        digits = re.findall(r"\d+", text_out)
        if digits:
            match_value = int(digits[0])
            # Clip it between 0 and 100 if needed
            match_value = max(0, min(100, match_value))
            return float(match_value)
        else:
            # If we can’t parse a number, default to 0 or some fallback
            return 0.0
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return 0.0


###############################################################################
# 9) CREATE A NEW SPREADSHEET WITH MATCH PERCENTAGES
###############################################################################

def create_matched_spreadsheet(scraped_roles_file, actor_descriptor, output_file="matched_roles.xlsx"):
    """
    Reads the scraped roles Excel, adds a 'match_percentage' column using the ChatGPT
    function, and writes out a new Excel.
    """
    df_roles = pd.read_excel(scraped_roles_file)

    match_percentages = []
    for idx, row in df_roles.iterrows():
        role_desc = str(row.get("role_description", ""))
        match_score = get_match_percentage(actor_descriptor, role_desc)
        match_percentages.append(match_score)

    df_roles["match_percentage"] = match_percentages
    df_roles.to_excel(output_file, index=False)
    print(f"Created new spreadsheet '{output_file}' with match_percentage for each role.")


###############################################################################
# 10) MAIN EXECUTION
###############################################################################

if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # STEP A: Scrape roles (if you haven’t already).
    #         If you already have a 'scraped_roles.xlsx', you can skip scraping.
    # -------------------------------------------------------------------------
    url = "https://actorsaccess.com/projects/?view=breakdowns&region=5"
    username = "your_username"
    password = "your_password"

    # Toggle this to True if you only want a quick test scrape:
    test_mode = True

    driver = open_browser_in_full_screen(url)
    login(driver, username, password)

    if test_mode:
        # Scrape only the first 2 pages
        limited_project_listings = test_scrape_limited_pages(driver, num_pages=2)
        all_projects = scrape_project_pages(driver, limited_project_listings)
        create_excel_from_roles(all_projects, file_name="test_scraped_roles.xlsx")
    else:
        # Full multi-page scrape
        all_project_listings = scrape_all_pages(driver)
        all_projects = scrape_project_pages(driver, all_project_listings)
        create_excel_from_roles(all_projects, file_name="all_scraped_roles.xlsx")

    close_browser(driver)

    # -------------------------------------------------------------------------
    # STEP B: Get actor descriptor from Google Form
    #         (Adapt the function to your real data file.)
    # -------------------------------------------------------------------------
    form_file = "sample_form.csv"  # Replace with your actual form file
    actor_descriptor = get_actor_descriptor_from_google_form(form_file)

    # -------------------------------------------------------------------------
    # STEP C: Use ChatGPT to compute match percentages & create new spreadsheet
    # -------------------------------------------------------------------------
    # If you tested with "test_scraped_roles.xlsx", pass that in:
    create_matched_spreadsheet(
        scraped_roles_file="test_scraped_roles.xlsx",
        actor_descriptor=actor_descriptor,
        output_file="matched_roles.xlsx"
    )

    print("Done.")