import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from db_logic import db_init, insert_recipe, recipe_exits
from utils import keys
import time
from datetime import datetime
from threading import Timer
import re
import json

recipes = {}

# wait the xpath element appear then execute task (less latency)

def execute_sec(driver, xpath, type, key):
    el = driver.find_element("xpath", xpath)
    while (not el):
        el = driver.find_element("xpath", xpath)
        time.sleep(1)
    if (type == 'input'):
        el.send_keys(keys[key])
    if (type == 'click'):
        el.click()
    return


def scan(driver):
    driver.get("https://www.giallozafferano.it")

    # Banner cookies
    try:
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="ameConsentUI"]/div/div[2]/button[1]'))).click()
    except TimeoutException:
        pass

    for cat in keys['recipe_categ']:
        n_page = -1
        driver.get("{}/page1/{}".format(keys['scrap_page'], cat))
        time.sleep(3)
        while (True):

            n_page += 1
            time.sleep(2)

            idx = 0
            while (True):
                try:
                    idx += 1
                    xpath_recipe_name = '/html/body/div[2]/main/div/div/article[{}]/div[2]/h2/a'.format(idx)
                    recipe_name = driver.find_element("xpath", xpath_recipe_name).get_attribute("innerHTML")
                    recipe_link = driver.find_element("xpath", xpath_recipe_name).get_attribute("href")
                    if(not recipe_exits(recipe_name)): 
                        recipe_scrap(recipe_name,recipe_link)
                        driver.back()

                except NoSuchElementException:
                    break

            try:
                if (n_page == 0):
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
                        (By.XPATH, '/html/body/div[2]/main/div/div/div[6]/a/span[2]'))).click()
                else:
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
                        (By.XPATH, '/html/body/div[2]/main/div/div/div[6]/a[2]/span[2]'))).click()
            except TimeoutException:
                break
            except ElementClickInterceptedException:
                # ci sta la pubblicità.. DC
                time.sleep(15)
                continue

        with open('{}.txt'.format(cat), 'w') as filehandle:
            json.dump(recipes, filehandle, indent=4)


def recipe_scrap(name,link):
    driver.get(link)
    # Get recipe presentation
    xpath_pres = '//*[@id="gz-raccomandatore-trigger"]/div/div/div[2]/p'
    pres = driver.find_element("xpath", xpath_pres).text

    # Get recipe info
    infos = []
    idx = 0
    while (True):
        try:
            idx += 1
            xpath_info = '/html/body/div[2]/main/div[1]/div[3]/div[3]/div[2]/div/ul/li[{}]/span[2]'.format(idx)
            infos.append(driver.find_element("xpath", xpath_info).text)
        except NoSuchElementException:
            break

    # Get ingredients
    ingrs = []
    idx = 0
    while (True):
        try:
            idx += 1
            xpath_ingredient = '//*[@id="gz-raccomandatore-trigger"]/div/div/div[3]/dl/dd[{}]'.format(idx)
            ingrs.append(driver.find_element("xpath", xpath_ingredient).text)
        except NoSuchElementException:
            break

    # Get steps etc.
    insert_recipe(name,link,pres,infos,ingrs,[])



if __name__ == '__main__':
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--blink-settings=imagesEnabled=false')
    driver = webdriver.Chrome(options=options, service=Service(
        ChromeDriverManager().install()))
    db_init()

    scan(driver)
