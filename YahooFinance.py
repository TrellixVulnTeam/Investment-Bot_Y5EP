# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import pandas as pd
import urllib.request as ur
from bs4 import BeautifulSoup
import warnings

from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from lxml import html
import lxml
import numpy as np
import pandas as pd

# Begin yahoo_income_statement(ticker)
# =============================================================================


def get_income_statement(ticker):
    # file path access local html
    filename1 = r'D:\ahmad\python\web\INDF.JK.html'

    # opening file in firefox browser
    driver = webdriver.Chrome(r"C:\Users\Frank\chromedriver.exe")
    # --| Parse or automation
    driver.get('https://finance.yahoo.com/quote/' + ticker + '/financials?p=' + ticker)
    sleep(5)

    # clicking "Expand All"
    btnclick = driver.find_elements(By.XPATH, "//*[@id='Col1-1-Financials-Proxy']/section/div[2]/button")
    btnclick[0].click()

    # parsing into lxml
    tree = html.fromstring(driver.page_source)

    # searching table financial data
    table_rows = tree.xpath("//div[contains(@class, 'D(tbr)')]")

    # Ensure that some table rows are found
    assert len(table_rows) > 0

    parsed_rows = []

    for table_row in table_rows:
        parsed_row = []
        el = table_row.xpath("./div")

        none_count = 0

        for rs in el:
            try:
                (text,) = rs.xpath('.//span/text()[1]')
                parsed_row.append(text)
            except ValueError:
                parsed_row.append(np.NaN)
                none_count += 1

        if (none_count < 4):
            parsed_rows.append(parsed_row)

    df = pd.DataFrame(parsed_rows)

    return df


# End yahoo_income_statement(ticker)
# =============================================================================


# Begin yahoo_balance_sheet(ticker):
# =============================================================================


def get_balance_sheet(ticker):
    # file path access local html
    filename1 = r'D:\ahmad\python\web\INDF.JK.html'

    # opening file in firefox browser
    driver = webdriver.Chrome(r"C:\Users\Frank\chromedriver.exe")
    # --| Parse or automation
    driver.get('https://finance.yahoo.com/quote/' + ticker + '/balance-sheet?p=' + ticker)
    sleep(5)

    # clicking "Expand All"
    btnclick = driver.find_elements(By.XPATH, "//*[@id='Col1-1-Financials-Proxy']/section/div[2]/button")
    btnclick[0].click()

    # parsing into lxml
    tree = html.fromstring(driver.page_source)

    # searching table financial data
    table_rows = tree.xpath("//div[contains(@class, 'D(tbr)')]")

    # Ensure that some table rows are found
    assert len(table_rows) > 0

    parsed_rows = []

    for table_row in table_rows:
        parsed_row = []
        el = table_row.xpath("./div")

        none_count = 0

        for rs in el:
            try:
                (text,) = rs.xpath('.//span/text()[1]')
                parsed_row.append(text)
            except ValueError:
                parsed_row.append(np.NaN)
                none_count += 1

        if (none_count < 4):
            parsed_rows.append(parsed_row)

    df = pd.DataFrame(parsed_rows)

    return df


# End yahoo_balance_sheet(ticker):
# =============================================================================


# Begin yahoo_cash_flow(ticker)
# =============================================================================


def get_cash_flow(ticker):
    # file path access local html
    filename1 = r'D:\ahmad\python\web\INDF.JK.html'

    # opening file in firefox browser
    driver = webdriver.Chrome(r"C:\Users\Frank\chromedriver.exe")
    # --| Parse or automation
    driver.get('https://finance.yahoo.com/quote/' + ticker + '/cash-flow?p=' + ticker)
    sleep(5)

    # clicking "Expand All"
    btnclick = driver.find_elements(By.XPATH, "//*[@id='Col1-1-Financials-Proxy']/section/div[2]/button")
    btnclick[0].click()

    # parsing into lxml
    tree = html.fromstring(driver.page_source)

    # searching table financial data
    table_rows = tree.xpath("//div[contains(@class, 'D(tbr)')]")

    # Ensure that some table rows are found
    assert len(table_rows) > 0

    parsed_rows = []

    for table_row in table_rows:
        parsed_row = []
        el = table_row.xpath("./div")

        none_count = 0

        for rs in el:
            try:
                (text,) = rs.xpath('.//span/text()[1]')
                parsed_row.append(text)
            except ValueError:
                parsed_row.append(np.NaN)
                none_count += 1

        if (none_count < 4):
            parsed_rows.append(parsed_row)

    df = pd.DataFrame(parsed_rows)

    return df

def get_units(ticker):
    # file path access local html
    filename1 = r'D:\ahmad\python\web\INDF.JK.html'

    # opening file in firefox browser
    driver = webdriver.Chrome(r"C:\Users\Frank\chromedriver.exe")
    # --| Parse or automation
    driver.get('https://finance.yahoo.com/quote/' + ticker + '/cash-flow?p=' + ticker)
    sleep(5)

    units_list = driver.find_elements(By.XPATH, "//*[@id='Col1-1-Financials-Proxy']/section/div[2]/span")[0].text.split(' ')

    currency = ''
    units = ''
    if (units_list[0] == 'Currency'):
        currency = units_list[2][:-1]
        units = units_list[6]
    elif (units_list[0] == 'All'):
        currency = 'USD'
        units = units_list[3]

    return units, currency

# End yahoo_cash_flow(ticker)
# =============================================================================