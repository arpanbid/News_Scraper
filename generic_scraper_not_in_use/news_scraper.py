#%%
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

def normalize_url(url, base_url):
    if url.startswith(('http', 'www.')):
        return url  # Absolute URL, return as is
    else:
        return urljoin(base_url, url)  # Convert relative URL to absolute

def init_driver():
    # Initialize the Edge WebDriver
    options = webdriver.EdgeOptions()
    #options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Edge(options=options)
    return driver

#%%
def process_page(driver, url):
    driver.get(url)
    time.sleep(2)

    #extract base url
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    elements = soup.find_all(['div', 'ul', 'ol', 'section', 'article', 'li'])
    scored_elements = []

    for el in elements:
        children = el.find_all(recursive=False)
        if len(children) > 2:  # Focus on repetitive child structures
            target_el = el  # Preserve original element
            xpath = ''
            current_el = el

            while current_el and current_el.parent:
                siblings = list(current_el.parent.find_all(current_el.name, recursive=False))
                if len(siblings) > 1:
                    index = siblings.index(current_el) + 1  # XPath index starts at 1
                    xpath = f"/{current_el.name}[{index}]" + xpath
                else:
                    xpath = f"/{current_el.name}" + xpath  # No brackets for unique elements

                current_el = current_el.parent

            xpath = f"//{xpath.lstrip('/')}"  # Ensure correct starting point

            try:
                selenium_el = driver.find_element(By.XPATH, xpath)
                size = driver.execute_script("return arguments[0].getBoundingClientRect();", selenium_el)
                area = size['width'] * size['height']
                score = area * (len(children) ** 2)
                scored_elements.append((score, selenium_el))
            except Exception as e:
                print(f"Error processing XPath {xpath}: {e}")
                continue

    
    # Calculate the area of a Selenium element
    scored_elements.sort(reverse=True, key=lambda x: x[0])

    if scored_elements:
        # Get the top-scoring Selenium WebElement
        top_element = scored_elements[0][1]

        # Extract text content
        text_content = top_element.text

        # Extract inner HTML content
        html_content = top_element.get_attribute('innerHTML')

        # Extract outer HTML (including the element itself)
        outer_html = top_element.get_attribute('outerHTML')

        #print("Top Element Text:\n", text_content)
        #print("\nTop Element Inner HTML:\n", html_content)
    else:
        print("No scored elements found.")


    # Get all links in the top scored element

    soup_content = BeautifulSoup(html_content, 'html.parser')

    # Find all <a> tags with an href attribute
    page_links = [a['href'] for a in soup_content.find_all('a', href=True)]

    # Print unique links from all extracted links
    page_links = list(set(page_links))


    #for link in page_links:
    #    print(link)





    #  prioritize H tags

    heading_links = []

    for tag in ['h1', 'h2', 'h3']:
        # Find <a> tags within heading tags
        heading_links.extend(tag.find_all('a', href=True) for tag in soup_content.find_all(tag))

    # If heading links exist, extract them; else extract all links
    if heading_links:
        # Flatten the list and extract href and text
        links = [(normalize_url(a['href'], base_url), a.get_text(strip=True)) for group in heading_links for a in group]
        print("Links Found in Headings (H1, H2, H3):")
    else:
        # Fallback: Extract all links in the content
        links = [(normalize_url(a['href'], base_url), a.get_text(strip=True)) for a in soup_content.find_all('a', href=True)]
        print("All Links Found:")

    # Display the extracted links and their text
    for url, text in links:
        print(f"Title: {text} | URL: {url}")

    return links



#%%
driver = init_driver()

#%%
driver.switch_to.window(driver.window_handles[-1])
driver.maximize_window()


#%%
data = []
with open("links.txt", "r") as file:
    urls = file.readlines()
    for url in urls:
        links = process_page(driver, url.strip())

        for i in links:
            data.append({"source": url, "link":i[0] })

    




# %%
driver.quit()

# %%
links = process_page(driver, "https://investor.dzsi.com/investor-news/default.aspx")
for i in links:
    data.append({"source": url, "link":i[0] })

# %%
import pandas as pd
df = pd.DataFrame(data)
df

# %%
df.to_excel("news1.xlsx", sheet_name="data", index=False)
# %%
