#%%
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.chrome.service import Service
import time
from datetime import date
from base_logger import logger
import os
from tqdm import tqdm
from config import *
from dateutil import parser


# Set up Chrome WebDriver
def setup_driver():
    try:
        #driver_path = DRIVER_PATH
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument('headless')
        #service = Service(executable_path=driver_path)
        driver = webdriver.Edge( options=edge_options)
        return driver
    except Exception as e:
        logger.error(f"Error setting up Chrome WebDriver: {str(e)}")
        return None

#%%
def scrape_data(driver, url, source_name, title_xpath, date_xpath, href_xpath, short_description_xpath):
    print("Scraping data from: ", url)
    
    #to scrape data using requests and lxml
    if "bleepingcomputer" in url or "cyware.com" in url:
        import requests
        from lxml import html

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'}
        response = requests.get(url, headers=headers)
        time.sleep(3)
        
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            try:
                titles = tree.xpath(title_xpath)
            except:
                if title_xpath or title_xpath != "":
                    logger.error(f"Error scraping title from {url}")
                    error_log = {"url": url, "result": "Unable to scrape title"}
                    unscraped_urls.append(error_log)

            try:
                dates = tree.xpath(date_xpath)
            except:
                if title_xpath or title_xpath != "":
                    logger.error(f"Error scraping date from {url}")
                    error_log = {"url": url, "result": "Unable to scrape date"}
                    unscraped_urls.append(error_log)

            try:
                hrefs = tree.xpath(href_xpath)
            except:
                if href_xpath or href_xpath != "":
                    logger.error(f"Error scraping href from {url}")
                    error_log = {"url": url, "result": "Unable to scrape href"}
                    unscraped_urls.append(error_log)
            
            try:
                short_descriptions = tree.xpath(short_description_xpath)
            except:
                if short_description_xpath or short_description_xpath != "":
                    logger.error(f"Error scraping short description from {url}")
                    error_log = {"url": url, "result": "Unable to scrape short description"}
                    unscraped_urls.append(error_log)
                
            
           
            if len(titles) == len(hrefs):
                pass
            else:
                logger.error(f"Error scraping {url}: Length of titles, dates, hrefs, and short_descriptions do not match")
                error_log = {"url": url, "result": "Length of titles, dates, hrefs, and short_descriptions do not match"}
                unscraped_urls.append(error_log)
                return
        else:
            logger.error(f"Error scraping {url}: {response.status_code}")
            return
    
    #to scrape data using selenium and jscript
    elif "securityweek" in url:
        driver.get(url)
        time.sleep(4)
        try:
            links_and_text = driver.execute_script("""
                return Array.from(document.querySelectorAll('h2.zox-s-title2')).map(h2 => {
                    const parentLink = h2.closest('a');  // Find the closest <a> parent element
                    return {
                        text: h2.innerText,
                        href: parentLink ? parentLink.href : null  // Get the href if the <a> exists
                    };
                });
            """)

            for item in links_and_text:
                if item['href'] and item['href']!="":
                    scraped_data.append({
                            'url': url,
                            'title': item['text'],
                            'date': "na",
                            'href': item['href'],
                            'short_description': "na",
                            'source_name': source_name
                        })
            scrapped_urls.append({"url": url, "result": "Articles Fetched"})
            logger.info(f"Appended URL: {url}")
            return
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            error_log = {"url": url, "result": str(e)}
            unscraped_urls.append(error_log)
            return

    #to scrape data using selenium and xpath - Default scraping method
    else:
        driver.get(url)
        time.sleep(3)  # Wait for the page to load
    
        # Try to find elements for title, date, href, and short_description using the XPaths

        try:
            titles = driver.find_elements(By.XPATH, title_xpath)
        except Exception as e:
            if title_xpath and title_xpath!="":
                logger.error(f"Error scraping {url} and {title_xpath}: {e}")
                error_log = {"url": url, "result": str(e)}
                unscraped_urls.append(error_log)

        try:
            dates = driver.find_elements(By.XPATH, date_xpath)
        except Exception as e:
            if date_xpath and date_xpath!="":
                logger.error(f"Error scraping {url} and {date_xpath}: {e}")
                error_log = {"url": url, "result": str(e)}
                unscraped_urls.append(error_log)

        try:    
            hrefs = driver.find_elements(By.XPATH, href_xpath)
        except Exception as e:
            if href_xpath and href_xpath!="":
                logger.error(f"Error scraping {url} and {href_xpath}: {e}")
                error_log = {"url": url, "result": str(e)}
                unscraped_urls.append(error_log)
            
        try:    
            short_descriptions = driver.find_elements(By.XPATH, short_description_xpath)
        except Exception as e:
            if short_description_xpath and short_description_xpath!="":
                logger.error(f"Error scraping {url} and {short_description_xpath}: {e}")
                error_log = {"url": url, "result": str(e)}
                unscraped_urls.append(error_log)
        

    if len(titles) == len(hrefs):
        pass
    else:
        logger.error(f"Error scraping {url}: Length of titles, dates, hrefs, and short_descriptions do not match")
        error_log = {"url": url, "result": "Length of titles, dates, hrefs, and short_descriptions do not match"}
        unscraped_urls.append(error_log)
        return
        
    for i in range(len(titles)):
        
        title = titles[i].text.strip()
        
        try:
            date = parser.parse(dates[i].text, fuzzy=True).strftime("%Y-%m-%d")
        except:
            date = "na"
        
        try:
            if hasattr(hrefs[i], 'get_attribute'):  
                href = hrefs[i].get_attribute('href')  # Selenium WebElement
            else:
                href = hrefs[i].get('href')  # lxml HtmlElement
        except: 
            href = "na"
        
        #try:
        #href = hrefs[i].get('href')
        #except:
        #    href = "na"
        try:
            short_description = short_descriptions[i].text
        except:
            short_description = "na"
        
        scraped_data.append({
            'url': url,
            'source_name': source_name,
            'title': title,
            'date': date,
            'href': href,
            'short_description': short_description
        })
    
    logger.info(f"Appended URL: {url}")
    scrapped_urls.append({"url": url, "result": "Articles Fetched"})


if __name__ == "__main__": 
    logger.info("Starting the scraping process...")

    try:
        input_xpath_file = os.path.join("input", INPUT_FILE_NAME)
        df = pd.read_excel(input_xpath_file, sheet_name=INPUT_FILE_SHEET_NAME)
        df = df.fillna("")
    except Exception as e:
        logger.error(f"Error reading Input Excel file {input_xpath_file}: {str(e)}")
    
    # Set up the Chrome WebDriver
    driver = setup_driver()
    scraped_data = []
    unscraped_urls = []
    scrapped_urls = []
    

    if driver is not None:
        # Iterate through the rows in the DataFrame and scrape data
        for index, row in tqdm(df.iterrows(), total=len(df)): #remove iloc later
            url = row['url']
            source_name = f'{str(row["Source"]).strip()}_{str(row["Priority"]).strip()}'
            title_xpath = row['title']
            date_xpath = row['date']
            href_xpath = row['href']
            short_description_xpath = row['short_description']

            scrape_data(driver, url, source_name, title_xpath, date_xpath, href_xpath, short_description_xpath)

        # Convert the scraped data to a pandas DataFrame
        scraped_df = pd.DataFrame(scraped_data)

        # Save the data to a new Excel file
        today_str = date.today().strftime("%y%m%d")
        output_file_name = f"news_links_{today_str}.xlsx"
        print(output_file_name)
        sb_output_path = os.path.join("output", output_file_name) #Check Path
        print(sb_output_path)
        scraped_df.to_excel(sb_output_path, index=False)

        #scrapped and unscraped URLs log
        scrapped = {item['url']: item['result'] for item in scrapped_urls}
        unscrapped = {item['url']: item['result'] for item in unscraped_urls}
        
        logger.info(f"Scrapped URLs: {scrapped}")
        print("Scrapped URLs: ", scrapped)
        print("Unscrapped URLs: ", unscrapped)
        logger.info(f"Unscrapped URLs: {unscrapped}")   


        # Clean up and close the driver
        driver.quit()
        print(f"Scraping completed and data saved to {output_file_name}")
    
    else:
        print("Error setting up Chrome WebDriver.")
        logger.error("Error setting up Chrome WebDriver.")