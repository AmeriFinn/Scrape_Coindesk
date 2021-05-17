# -*- coding: utf-8 -*-
"""
Created on Sat May 15 22:43:39 2021

With this script I will combine two .ipynb files into a .py file that can be more easily
shared and utilized across other scripts. The goal with this is to have a script that can scrape
large news sites and collect all articles published over a desired time period. 

This project started out as a way to collect articles from the markets section of coindesk.com,
but with this script I'd like to have something that can be used to collect articles from a wide
array of news sites. I have tested this out on Bloomber and WSJ to some success, but do not
have a viable working solution yet. 

NOTE: CURRENTLY, THIS SCRIPT ONLY WORKS IF FIREFOX IS INSTALLED...

@author: grega
"""
## Import selenium for web scraping
from selenium import webdriver

## Import standard python libraries
import pandas as pd    # For working with data frames
import re, os          # Regular expressions (re), and standard shell commands (os)
from os import path    # Create paths to save .txt files
import time            # Use .sleep() to make scraping sites smoother
import datetime as dt  # Working with dates in python

## Import the clear_output module for jupyter notebook users
from IPython.display import clear_output

## Expand number of columns and table width for output in spyder
pd.set_option("display.max_columns", 10)
pd.set_option('display.width', 1000)

## Define a generic exception for working with Selenium
## This is not working as intended, but will return to this in the future
class ElementClickInterceptedException(Exception):
    pass

class create_index:
    """
    `create_index` is the module used to open a browser, go to a news site, and collect
    publication titles and hyperlinks. A pandas DataFrame will be created with article titles
    as the index and hyperlink info in the columns.
    
    Parameters
    ----------
    index_site : str
    |    A string denoting the webpage of article links to be scraped.
    |    This should be a specific section of the news site, not the base url.
    
    index_site_home_link : str
    |    A string denoting the home page of the website to be scraped.
    |    e.g. https://www.coindesk.com or https://www.bloomberg.com
        
    extension1 : str
    |    A string denoting the first link extension that may, or may not, need to be included in
    |    the hyperlink for specific articles.
    |    The default is the empty string ("").
        
    extension2 : str
    |    A string denoting the second link extension that may, or may not, need to be included in
    |    the hyperlink for specific articles
    |    The default is the empty string ("").
        
    extension3 : str
    |    A string denoting the third link extension that may, or may not, need to be included in
    |    the hyperlink for specific articles
    |    The default is the empty string ("").
        
    n : int64
    |    An integer denoting the number of times the `more` button will need to be clicked
    |    when expanding the web page to include more articles in the `expand_page` method.
    |    For some news sites, such WSJ, Twitter, Reddit, this needs to be replaced with
    |    functionality that will instead keep scrolling a desired number of page lengthts.
    |    The default is 1000 clicks (or page scrolls in the future).
    
    Methods
    ----------
    `expand_page`
    |    This method will expand the web page a desired number of times to display more articles
    |    on the page. When lengthy periods of time (in excess of 2-3 months), this method will
    |    require thousands of iterations, whether that be clicking a button to expand the page,
    |    or continuing to scroll down the page. The behavior is inconsistent across major outlets,
    |    and with sites that use buttons to expand the page, it is difficult to dynamically locate
    |    a button that will expand the page.
    
    `page_source`
    |    This method will collect all article titles and hyperlinks from the desired web page.
    |    The `expand_page` method should be used first to expand the text corpus that will be
    |    indexed, but it is not a requirement. A pandas DataFrame will be returned as a class
    |    attribute called, `articles`.
    
    `go`
    |    This method will call the prior two methods and provides a slightly faster way
    |    to call the necessary attributes to index a news site.
    
    Attributes
    ----------
    `driver` : Selenium Webbrowser Object
        The selenium webdriver which will be used to scrape the article index.
        
    `articles` : pandas.DataFrame
        A dataframe containing the article titles and hyperlinks to be scraped.
        
    All other parameters passed to the `create_index` class will be appended as attributes.
    """

    def __init__(self, index_site, index_site_home_link,
                 extension1="", extension2="", extension3="", n=1000):
        ## Initiate `Firefox` browser and access the desired website to create an article index for.
        ## Currently, this is really only works perfectly for specific sections of coindesk.com
        ## I also could add functionality to work across multiple browsers such as chrome, edge, safari...
        fp = webdriver.FirefoxProfile()

        ## Open the browser and go to the desired news page to scrape.
        ## This should not be the home page for the website. It should be a specific section
        ## of the news site which itself is their own index of articles related to the desired category.
        driver = webdriver.Firefox(firefox_profile=fp)
        driver.get(index_site)
                
        ## Return the passed inputs as attributes of the `create_index` class
        self.driver               = driver
        self.index_site           = index_site
        self.index_site_home_link = index_site_home_link
        self.extension1           = extension1
        self.extension2           = extension2
        self.extension3           = extension3
        self.n                    = n
        
    def expand_page(self):
        """
        

        Returns
        -------
        None.

        """
        ## Collect the necessary class attributes
        driver = self.driver
        n      = self.n
        
        ## Identify the button to expand the number of articles displayed
        more_btn = driver.find_element_by_css_selector("h3.heading")
        
        ## Notify user of the lengthy process that is about to start
        print(f"The page will now be expanded, {n:,} times, to display more article links.")

        ## Click the `More` button `n` number of times
        for i in range(n):
            ### Notify user of progress due to this being a lengthy process
            clear_output(wait=True)
            print(f"{round(100*i/(n-1),2)}% - {i+1} of {n}")
            
            try:
                #### Try clicking the button
                more_btn.click()
                time.sleep(.9)  # sleep so the page can keep up with clicks
            except:  # Bare except feels wrong... but python doesn't want to recognize this error from selenium...
                #### Otherwise, scroll past the ad box blocking the button and try again
                driver.maximize_window()
                driver.execute_script("window.scrollTo(0, window.scrollY + 225)")

                more_btn.click()
                time.sleep(.9)

    def page_source(self):
        ## Collect the necessary class attributes
        driver               = self.driver
        index_site           = self.index_site
        index_site_home_link = self.index_site_home_link
        extension1           = self.extension1
        extension2           = self.extension2
        extension3           = self.extension3
        
        ## Collect the full html page source data. This will be a MASSIVE string
        page = driver.page_source
        
        ## Define three functions:
        ## - `CustomCheck()` fucntion that will check an article title against a few conditions
        ##    to see if the article collected is one we want to exclude.
        ## - `ArticleIndex()` function that will have a page source passed to it, and return a
        ##    dataframe of all article titles and scrapable link extensions.
        ## - `FullLink` to concatenate columns to form a complete article link
        def CustomCheck(title):
            
            # Define list of links/articles that are collected using the `<a title=.*? href=.+?>` regex
            # but are not actual articles.
            approx_matchs = ['Articles by ', 'articles by']
            exact_matches = ['About', 'Advertise', 'Masthead', 'Ethics Policy', 'Contributors',
                             'Events', 'Terms &amp; Conditions', 'Privacy Policy',
                             "'Newsletters'", 'Newsletters', 'Terms amp; Conditions']
            
            # First check for the approxiamate matches
            for word in approx_matchs:
                if word in title:
                    return True
                    break
            
            # Then check for the exact matches
            for word in exact_matches:
                if word == title:
                    return True
                    break
            
            # If no matches, return False
            return False
        
        def ArticleIndex(page, master_site, extension_1="", extension_2="", extension_3=""):
            ### Find all html elements that contain an `article title` and `href`
            articles = re.findall("<a title=.*? href=.+?>", page)
            
            ### Create empty dictionary that will be used to create the pandas dataframe
            article_links = {}

            ### Loop through the list of articles to collect the article title and link extension
            for art in articles:
                #### First collect the title. Used as key in dictionary
                title = re.search('title=.+?"', art)
                title = title.group(0)

                #### First, clean up the title
                for x in ["title=", "?", "$", "\\", "/", "|", "*", "&", "nbsp", "<", ">"]:
                    title = title.replace(x, "")
        
                    title = title.replace('"', "")
                title = title.replace(':', ";")

                #### Second, collect the link. Stored as value in dictionary
                link = re.search('href=.+?"', art)
                link = link.group(0)

                #### Third, clean up the link
                link = link.replace("href=", "")
                link = link.replace('"', "")

                #### Fourth, Determine if we want to store the link for this article
                if CustomCheck(title) == False:
                    article_links[title] = [master_site, extension_1, extension_2, extension_3, link]

            ### Convert the dictionary to a pandas dataframe
            Articles_df = pd.DataFrame(article_links).T
            Articles_df.columns = ['Master Site', 'Extension_1', 'Extension_2', 'Extension_3', 'Href']
            Articles_df.loc[:, 'Downloaded'] = False

            return Articles_df
        
        def FullLink(lst):
            full_link = ""
            for i in lst:
                full_link += i
                
            return full_link
        
        ## Use `ArticleIndex` to collect the article titles and links displayed on the markets page
        articles = ArticleIndex(page, index_site_home_link, extension1, extension2, extension3)
        ## Apply `FullLink` to create a column with links to scrape
        articles.loc[:, 'FullLink'] = articles.apply(lambda x: FullLink([x['Master Site'], x.Href]), axis=1)
        
        ## Close the web driver
        driver.quit()
        
        self.articles = articles
        
    def go(self):

        self.expand_page()
        self.page_source()
        
        return self

class scrape_index:
    """
    `scrape_index` provides methods for iterating over the DataFrame created from the `create_index`
    class. The articles will be saved as .txt files to a desired folder on the local machine. 
    
    Parameters
    ----------
    articles_df : pandas.DataFrame
    |    A pandas DataFrame that was returned as the .articles attribute from the `create_index`
    |    class. It is necessary for this df to have article titles in the index, and full article
    |    hyperlinks that need to be scraped. Additionally, there needs to be a boolean column
    |    called 'Downloaded' which denotes if the article has already been downloaded.
    
    index_site : str
    |    A string denoting the webpage of article links to be scraped.
    |    This should be a specific section of the news site, not the base url.
    |    For the `scrape_index` class this is really only used as an initial landing spot
    |    for the web driver before individual articles are scraped.
    
    download_folder : str
    |    The local folder path which will be used to save the .txt files.
    |    This should NOT include the sytstem path seperators at the end of the string.
        
    Methods
    ----------
    `scrape`
        This method will open the article on the news site, collect the full HTML page source,
        and clean the page source to grab relevant article elements such as the title, author,
        publishing date/time, and article text. Images, videos, and embedded hyperlinks, will
        be dropped.

    Attributes
    ----------
    `articles` : pandas.DataFrame
        An updated dataframe containing the article titles and hyperlinks to be scraped,
        with the downloaded status.
    
    """
    def __init__(self, articles_df, index_site, download_folder):
        ## Initiate `Firefox` browser and access the desired website to create an article index for.
        ## Currently, this is really only works perfectly for specific sections of coindesk.com
        fp = webdriver.FirefoxProfile()

        ## Open the browser and go to the desired news page to scrape.
        ## This should not be the home page for the website. It should be a specific section
        ## of the news site which itself is their own index of articles related to the desired category.
        driver = webdriver.Firefox(firefox_profile=fp)
        driver.get(index_site)
                
        ## Return the passed inputs as attributes of the `scrape_index` class
        self.driver = driver
        self.articles_df = articles_df
        self.download_folder = download_folder
        
    def scrape(self):
        driver = self.driver
        articles = self.articles_df
        download_folder = self.download_folder
        
        ## Define `clean_title()` to remove characters that can't be included in file names
        def clean_title(title):
            title = title.encode('unicode_escape').decode('ascii')
            
            ### Remove these characters
            for x in [
                r"\\u(.){3,4}", r"'\\u(.){3,4}'", r"\\u",
                "\?", "\\!", "\\$", r"\\", "/", "|",
                "\\*", "&", "nbsp", '<.+?>', '&nbsp;',
                '&amp', "<", ">", '"', "  "
            ]:
        
                title = re.sub(x, '', title)
        
            ### Replace these characters
            for x in ["\\:", "\\;", "\\|", "\\.", "\\'"]:
                title = re.sub(x, '-', title)
            
            return title
        
        ## Define `Collect_Article()` to have a link passed to it and return the article text
        ## contained in that link as a `list`
        def Collect_Article(driver, link):
            try:
                ### Try to open the article
                driver.get(link)
            except:  # Another bare except condition, but Python does not recognize selenium exceptions
                ### If error occurs, no internet connection or the browser connection was broken
                return "No browser has been initiated!"
            
            ### Collect the entire html page source data
            page = driver.page_source
            
            ### Collect all elements that match article text or header parameters.
            ### This allows ads and other garbage to be easily excluded.
            article_text = re.findall('<div class="article-hero-headline">.*?</h1>|' + \
                                      '<h5 class="heading">.*?</h5>|' + \
                                      '<div class="article-hero-datetime">.*?</time>|' + \
                                      'class="article-pharagraph">.*?</p>|' + \
                                      'class="article-list">.*?</ul>|' + \
                                      '<p>.*?</p>|' + '<p class="head2">.*?</p>|' + \
                                      '<p dir="ltr">.*?</p>|' + \
                                      '<p style="null.*?>.*?</p>|' + \
                                      'class="article-heading">.+?</h2>', page)
            
            ### Iterate over the collected article to clean it up a bit
            cleaned_article = []
            for line in article_text:
                #### Replace the html text that was used to collect article text
                line    = line.encode('unicode_escape').decode('ascii')
                
                #### Replace very specific article elements
                cleaned = line.replace('<div class="article-hero-headline">', 'Title: ')
                cleaned = cleaned.replace('<h5 class="heading">', 'Author: ')
                cleaned = cleaned.replace('<div class="article-hero-datetime">', 'Datetime: ')
                
                #### Replace article header's and non-ascii characters
                for x in ['class="article-pharagraph">', 'class="article-heading">', 
                          'class="article-list">', '<.+?>', '&nbsp;', '&amp',
                          r"\\u(.){4}", r"'\\u(.){4}'",
                          'Please consider using a different web browser for better experience.',
                          'Sign up for our newsletters', 'Image via', 'Shutterstock', 
                          'This report has been updated.']:
                    cleaned = re.sub(x, ' ', cleaned)  

                #### Append the cleaned paragraph to the storage list
                cleaned = cleaned.replace(' .', '.')
                cleaned_article.append(cleaned.replace('  ', ' ').strip())
            
            cleaned_article = [line for line in cleaned_article if line != '']
            
            return cleaned_article
        
        ## Define `Write_TXT()` to process a list of strings and convert that list into a .txt file
        def Write_TXT(article, title, download_folder):
            ### The following three variables could be inputs for the function.
            ### Will keep these as local variables for now.
            file_name = f"{title}.txt"
            full_name = os.path.join(download_folder, file_name)
            # Save the article as a .txt file
            with open(full_name, 'w') as f:
                #for item in article:
                f.write("\n".join(article))
                f.close()
        
        ## Define Collect_Corpus() to have the dataframe created from ArticleIndex()
        ## (with FullLink applied) passed to this function, where the FullLink column will be
        ## iterated over to collect the article text into a dictionary.
        def Collect_Corpus(Articles_df):
            ### Define storage dictionary and iterating variables
            # corpus = {}
            i, n = 0, Articles_df.shape[0]
            start = dt.datetime.now()
            
            ### Iterate over Articles_df
            for title, link in zip(Articles_df.index, Articles_df.FullLink):
                i += 1
                
                #### Due to this being a lengthy/costly loop, notify the user of what
                #### iteration and article the function is on
                if i % 5 == 0:
                    clear_output(wait=True)
                    timer = dt.datetime.now()
                    print(f"{round(100*i/n,2)}% - {i} of {n} | {str(timer-start)}")
                print(f"{i} of {n}")
                print(f"Collecting: {title}")
                
                #### Download the article if it is not already downloaded
                if Articles_df.loc[title, 'Downloaded'] == False:
                
                    ##### Collect the article text from the link and store in the dictionary
                    article = Collect_Article(driver, link)
                    # corpus[title] = article

                    try:
                        ###### Try writing the collected article to a text file
                        Write_TXT(article, title, download_folder)
                        Articles_df.loc[title, 'Downloaded'] = True
                    
                    except:
                        ###### If that fails, try one more time and then move on.
                        try:
                            article = Collect_Article(link)
                            for x in ["?", "!", "$", "\\", "/", "|", "*", "&", "nbsp", "<", ">"]:
                                title = title.replace(x, "")
        
                            # corpus[title] = article
                            time.sleep(1)
                            Write_TXT(article, title, download_folder)
                            Articles_df.loc[title, 'Downloaded'] = True
                        except:
                            print(f"{title} could not be downloaded. Trying Again")
                        
                    ##### Let browser catch up
                    time.sleep(.75)
                    
                else:
                    #### Notify user if the article was already downloaded
                    print(f"{title} already downloaded!")
                    
            return Articles_df
        
        ## Use `clean_title` to clean up the articles_df index
        articles.index = [clean_title(x) for x in articles.index]
        
        ## Check if the article has already been saved as a .txt file to the desired local folder
        articles.loc[:, 'Downloaded'] = False
        for title in articles.index:
            file_name = f"{title}.txt"
            full_name = os.path.join(download_folder, file_name)
            if path.exists(full_name):
                articles.loc[title, 'Downloaded'] = True
                
        ## Drop the rows that do not contain enough hyperlink info to collect an article
        articles.dropna(axis=0, how = 'any', thresh=2, inplace=True)
        
        ## Now collect and save the articles
        articles = Collect_Corpus(articles)

        ## Close the web driver
        driver.quit()
        
        ## Replace the articles attribute with the updated df, which includes download status
        self.articles = articles

# Test out the `create_index` class
index_site = "https://www.coindesk.com/category/markets"
index_site_home_link = "https://www.coindesk.com"
extension1, extension2 = "/category", "/markets"

ci = create_index(index_site, index_site_home_link, n=15)
ci.go()

articles = ci.articles
articles

# Now test out the scraping class
download_folder = "<Insert local folder address w/ no path sep's at the end of the string>"

si = scrape_index(articles, index_site, download_folder)

si.scrape()
