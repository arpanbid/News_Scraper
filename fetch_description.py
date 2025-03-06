#%%

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
import time
import requests
from lxml import html
import pandas as pd
import sqlite3
import os

#%% setup selenium driver

def init_driver():
    driver_path = "C:/Users/BidA/Documents/PY/WebDrivers/msedgedriver.exe"
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument('headless')
    service = Service(executable_path=driver_path)
    driver = webdriver.Edge(service=service, options=edge_options)
    return driver

#%%
def read_links_file():
    today_str = date.today().strftime("%y%m%d")
    input_file_path = os.path.join("input", f"news_links_{today_str}.xlsx")
    df = pd.read_excel(input_file_path, sheet_name='Sheet1')
    return df



#%%
def read_db():
    conn = sqlite3.connect('news.db')
    df_db = pd.read_sql_query("SELECT * FROM news", conn)
    conn.close()
    return df_db

def write_db(result_pd):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()     # Create a cursor object

    # Create the table with an auto-incrementing primary key if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        value INTEGER
    )
    ''')

    # Append the new data to the existing table
    result_pd.to_sql('news', conn, if_exists='append', index=False)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("New rows have been added to the existing database.")


#%%

def fetch_description(url, driver):

    # Try to find the main content using common patterns
    possible_selectors = [
        "//*[contains(@class, 'entry-content')]//p",  # WordPress-like content class
        "//article//p",                               # Inside <article>
        "//*[contains(@class, 'content')]//p",        # Divs with 'content' class
        "//*[contains(@class, 'post-body')]//p",      # Blogger-like content class
        "//div[contains(@id, 'main')]//p",            # Generic main div
    ]

    article_text = ""

    if "bleepingcomputer" in url:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'}
        response = requests.get(url, headers=headers)
        time.sleep(3)
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            paragraphs = tree.xpath("//article//p")
            for i in range(len(paragraphs)):
                p = paragraphs[i].text_content().strip()
                article_text = article_text + p
            
            dates = tree.xpath("//*[contains(@class, 'date' )][1]")
            if dates:
                date = dates[0].text_content().strip()

            return article_text, date

    driver.get(url)
    time.sleep(3)


    # Loop through selectors and extract text from the first matching element
    try:
        for selector in possible_selectors:
            paragraphs = driver.find_elements(By.XPATH, selector)
            if paragraphs:
                article_text = "\n".join([p.text for p in paragraphs if p.text.strip()])
                break  # Stop if we find content
    except Exception as e:
        article_text = ""
        print(f"Error: {e}")
    try:
        date = driver.find_element(By.XPATH, '//*[contains(@class, "date" )][1] | //time[1] | //*[contains(@class, "published")]').text.strip()
    except:
        date = ""

    if "securityweek" in url:
        paragraphs = driver.execute_script("""
        return Array.from(document.querySelectorAll('[class*="post-body"] p')).map(el => el.innerText);
    """)
        article_text = "\n".join([p for p in paragraphs if p.strip()])
        date = driver.find_element(By.XPATH, '//time[@class="post-date updated"]').text.strip()

    return article_text, date

#%%
driver = init_driver()



df = read_links_file()
df_db = read_db()

list_of_dict =[]
shuffled_df = df.sample(frac=1).reset_index(drop=True)

for index, row in shuffled_df[:10].iterrows():     
    url= row["href"]

    if url not in df_db["url"].values and (not any(item["url"] == url for item in list_of_dict)): #added the second and
        print(f'Fetching URL {str(index)} of {str(len(df))}: {url}')
        article_text, date = fetch_description(url, driver)
        if row["date"]!="na":
            date = row["date"]
            try:
                date = pd.to_datetime(date, errors='coerce').strftime('%Y-%m-%d')
            except:
                print(f"Error in getting date in URL: {url}. \n putting todays date as publication date.")
                date = pd.Timestamp.today().strftime('%Y-%m-%d')

        article_dict = {
            "title": row['title'], 
            "company_name": row['company_name'],
            "url": url,
            "description": article_text,
            "publication_date": date if date else pd.Timestamp.today().strftime('%Y-%m-%d'),
            "extracted_date" : pd.Timestamp.today()


        }
        list_of_dict.append(article_dict)
    else:
        print(f'URL available in DB {str(index)} of {str(len(df))}: {url}')

#%%
result_pd = pd.DataFrame(list_of_dict)
#%%
result_pd['publication_date'] = result_pd['publication_date'].str.replace('Published', '')
result_pd['publication_date'] = pd.to_datetime(result_pd['publication_date'])
result_pd['extracted_date'] = pd.to_datetime(result_pd['extracted_date'])
print(f"Total news fetched {len(result_pd)}")
result_pd.to_excel("result.xlsx", index=False)

#%%
driver.quit()
#%%
write_db(result_pd)    

#%%
print(result_pd)





    


# # %%
# driver = init_driver()
# #%%
# url= "https://www.bleepingcomputer.com/news/security/microsoft-hackers-steal-emails-in-device-code-phishing-attacks/"
# article_text, date = fetch_description(url, driver)
# print(article_text if article_text else "No article content found.")
# print(date if date else "No article content found.")

# #%%
# # Close the browser
# driver.quit()

# #%%

# %%


