import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML
#from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from tqdm.notebook import tqdm
import time
import pdb
import csv
from PIL import Image
import requests
import asyncio
import os
import re

url = 'https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus'
# class Navigator(self):
#     def init


async def setup():
    playwright = await async_playwright().start()
    # THIS LINE OPENS & SETS UP THE BROWSER
    browser = await playwright.chromium.launch(headless = False)
    page = await browser.new_page()
    
    # THIS LINE LOADS THE PAGE
    await page.goto(url)
    
    # THIS LINE REMOVES THE VALIDATION ERROR which asks you to select state, district and court complex
    await page.locator('#validateError button').click()
    
    # THIS CODE GETS THE LIST OF ALL THE STATE OPTIONS AVAILABLE 
    state_options = page.locator("#sess_state_code option")
    print(state_options)
    
async def get_districts():
    print('im here')
    #get the list of all district option for the selecged state
    district_options = page.locator("#sess_dist_code option")
    district_count = await district_options.count()
    print(district_count)
    print(district_options)
    for district_i in range(district_count):
                #get the locator for each district
                district_option = district_options.nth(district_i)
                print(district_option)
                #get the name
                district_text = await district_option.text_content()
                #format name of state to lowercase and replace space with underscore character
                district_name_for_filename = district_text.lower().strip().replace(" ", "_")
                time.sleep(3)
                print(district_name_for_filename)
                #get the district code
                district_value = await district_option.get_attribute('value')
                print(district_value)
                
                #again let's check by substring and not district code 
                if any(substring in district_name_for_filename for substring in ['select', 'select_district']):
                    print('Select State found')
                    continue
                else: 
                    #return the district_value list here so we can navigate districts in the main loop and not over here everytime 
                    return(district_value)
                
async def get_court_complexs():
    complex_options = page.locator("#court_complex_code option")
    complex_count = await complex_options.count()
    court_complex_names = []
    court_complex_codes = []

    time.sleep(2)
    print('im in courts function')

    for complex_i in range(complex_count):
        #get all court options 
        complex_option = complex_options.nth(complex_i)
        #get court name
        complex_text = await complex_option.text_content()
        #format name of court to lowercase and replace space with underscore character
        court_complex_name = complex_text.lower().strip().replace(" ", "_")
        #get court code
        print(court_complex_name)
        complex_value = await complex_option.get_attribute('value')
        print(complex_value)
        if any(substring in court_complex_name for substring in ["select_court_complex", "select"]):
            continue  # this will skip the "select court complex" option
        else: 
            court_complex_names.append(court_complex_name)
            court_complex_codes.append(complex_value)
    
    return court_complex_names, court_complex_codes

async def navigate_state(state_count):

    for state_i in range(state_count):
            #get the locator frame for the states by the state number
            state_option = state_options.nth(state_i)
            #get the number of each state from the playwright locator 
            state_value = await state_option.get_attribute('value')
            #get the name of each state collected from the state number above
            state_text = await state_option.text_content()
            #format name of state to lowercase and replace space with underscore character
            state_name_for_filename = state_text.lower().strip().replace(" ", "_")
            time.sleep(3)
            
            #This has deprecated - now the Select State option is 0. To fix this, check for presence of substring. 
            if any(substring in state_text for substring in ['select', 'state', 'select_state']):
                    print('Select State found')
                    continue
            else:
                    print("State found let's navigate")
                    # Following line fills in the state option 
                    await page.locator('#sess_state_code').select_option(state_value)
                    time.sleep(1.5)
                    #now let's collect the district data within each state:
                    district_value = await get_districts() 
                    print("district filled in: ", district_value)
                    if district_value: 
                            #let's fill in the district value 
                            #fill in the district value
                            time.sleep(2)
                            await page.locator('#sess_dist_code').select_option(district_value)
                            time.sleep(3)
                            
                            court_names, court_codes = await get_court_complexs()
                            if court_codes != []:
                                    for idx, i in enumerate(court_codes):
                                            #fill in the court code:    
                                            print("court code filled: ", i)     
                                            await page.locator('#court_complex_code').select_option(i)
                                            time.sleep(2)
                                            
                                            court_name = court_names[idx]
                                            print(court_name)
                                            # now let's navigate to the ACT tab to filter by IPC ACT 
                                            
                                            # THIS LINE REMOVES THE VALIDATION ERROR which asks you to select state, district and court complex
                                            await page.locator('//*[@id="act-tabMenu"]').click()
                                            #await page.locator('#validateError button').click()
                                            time.sleep(2)
                                            
                                            print('here here here')
                                            # FILL IN THE ACT TYPE 
                                            #Make sure that the Act Type dropdown is not empty like in Sitapur's Biswan Court Complex
                                            act_options = page.locator("#actcode option")
                                            print(act_options)
                                            act_count = await act_options.count()
                                            if act_count == 1:
                                                    continue #Skip this turn if dropdown only has "Select Act Type" option WHY?!?!?!?
                                            
                                            # Look for "Indian Penal Code" or "IPC" or "I.P.C." (case-insensitive search)
                                            options = page.locator('#actcode').get_by_text(re.compile(r'\bIndian Penal Code', re.IGNORECASE))
                                            print('option: ', options)
                                            all_codes = options.all_text_contents()
                                            print("All codes: ", all_codes)
                                            #act_value = await .get_attribute('value')
                                            #print('act_val: ', act_value)
                                            
                                            break
            break
                
        
                