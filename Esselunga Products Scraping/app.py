import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from utils import keys,Product
import time
import re
import json


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


def login(driver):
    driver.get("https://www.esselungaacasa.it/ecommerce/nav/auth/supermercato/home.html?streetId=30143801#!/negozio/?header=0")
    execute_sec(driver, '//*[@id="gw_username"]', 'input', 'email')
    execute_sec(driver, '//*[@id="gw_password"]', 'input', 'password')
    execute_sec(driver, '//*[@id="rememberme"]', 'click', 'null')
    input("After manually verify captcha press any key to continue + Enter ")
    time.sleep(3)  # 3 sec to load

# Scandisce tutti i prodotti presenti sul sito e li salva su un file di testo


def scan(driver):
    products = {}
    for cat in keys['menu_categ']:

        driver.get("{}{}".format(keys['scrap_categ'], keys['menu_categ'][cat]))
        xpath_n = '//*[@id="pageContent"]/div/div[1]/h2'
        xpath_ul = '/html/body/div[1]/div/div[2]/div[2]/menu-item-product-set/div/div/div[3]/'
        s = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, xpath_n))).text
        n = int(s[s.find("(")+1:s.find(")")])

        print("Scraping {} [{} items] ".format(cat, n))

        #Scraping products
        for idx in range(1, n):
            xpath_base = xpath_ul + 'div[{}]/esselunga-product'.format(idx)

            xpath_id = xpath_base + '/div[2]/div[4]/div[2]/span'
            xpath_name = xpath_base + '/div[2]/div[4]/div[2]/h3/a/span'
            xpath_old_price = xpath_base + '/div[2]/div[5]/div[2]/div/div/esselunga-product-price/p[2]/span[1]'
            xpath_dis_price = xpath_base + '/div[2]/div[5]/div[2]/div/div/esselunga-product-price/p[2]/span[2]'

            while True:
                try:
                    driver.find_element("xpath", xpath_base)
                    break
                except NoSuchElementException:
                    driver.execute_script("window.scrollBy(0,1000);")
            
            id = driver.find_element("xpath", xpath_id).get_attribute("innerHTML")
            name = driver.find_element("xpath", xpath_name).get_attribute("innerHTML")
            norm = driver.find_element("xpath", xpath_old_price).get_attribute("innerHTML")
            disc = driver.find_element("xpath", xpath_dis_price).get_attribute("innerHTML")

            p = Product(id,name,disc != norm,disc)

            try:
                products[cat].append(p)
            except:
                products[cat] = [p]

            if(disc != norm):
                print(" {} discounted from {} to {} ".format(id,norm,disc))
           
        print(products)

    # Fine -> salva sul json tutti i prodotti esistenti
    with open('output.txt', 'w') as filehandle:
        json.dump(products, filehandle)


if __name__ == '__main__':
    options = Options()
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options, service=Service(
        ChromeDriverManager().install()))
    login(driver)
    scan(driver)
