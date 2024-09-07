import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML
from playwright.async_api import async_playwright
from tqdm.notebook import tqdm
import time
import csv
from PIL import Image
import requests
import asyncio
import os
import re
import logging

# Configure logging
logging.basicConfig(
    filename='court_navigator.log',  # Log to this file
    level=logging.INFO,              # Log all INFO level and above
    format='%(asctime)s - %(levelname)s - %(message)s',  # Include timestamp
)

class CourtNavigator:
    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None

    async def setup(self):
        logging.info("Starting Playwright and launching browser.")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        await self.page.goto(self.url)
        await self.page.locator('#validateError button').click()
        logging.info("Browser launched and initial page setup completed.")

    async def get_districts(self):
        logging.info("Getting district options.")
        district_options = self.page.locator("#sess_dist_code option")
        district_count = await district_options.count()
        logging.info(f"Found {district_count} district options.")

        for district_i in range(district_count):
            logging.info(f"Processing district {district_i + 1}.")
            district_option = district_options.nth(district_i)
            district_text = await district_option.text_content()
            district_name_for_filename = district_text.lower().strip().replace(" ", "_")
            time.sleep(3)
            district_value = await district_option.get_attribute('value')

            if any(substring in district_name_for_filename for substring in ['select', 'select_district']):
                logging.info("Skipping 'Select District' option.")
                continue
            else:
                logging.info(f"Selected district: {district_text}.")
                return district_value
            
    async def download_act_codes(self, output_file='act_codes.csv'):
        # Locate the dropdown options
        act_options = self.page.locator('#actcode option')
        act_count = await act_options.count()

        # Prepare a list to hold the options
        act_list = []

        # Loop through each option and extract text and value
        for i in range(act_count):
            option = act_options.nth(i)
            act_text = await option.text_content()
            act_value = await option.get_attribute('value')

            # Append the act information to the list
            act_list.append({'Act Name': act_text, 'Act Code': act_value})

        # Write the list to a CSV file
        with open(output_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Act Name', 'Act Code'])
            writer.writeheader()
            writer.writerows(act_list)

        print(f"Act codes successfully downloaded to {output_file}")

    async def get_court_complexes(self):
        logging.info("Getting court complex options.")
        complex_options = self.page.locator("#court_complex_code option")
        complex_count = await complex_options.count()
        logging.info(f"Found {complex_count} court complex options.")
        court_complex_names = []
        court_complex_codes = []

        time.sleep(2)

        for complex_i in range(complex_count):
            logging.info(f"Processing court complex {complex_i + 1}.")
            complex_option = complex_options.nth(complex_i)
            complex_text = await complex_option.text_content()
            court_complex_name = complex_text.lower().strip().replace(" ", "_")
            complex_value = await complex_option.get_attribute('value')

            if any(substring in court_complex_name for substring in ["select_court_complex", "select"]):
                logging.info("Skipping 'Select Court Complex' option.")
                continue
            else:
                court_complex_names.append(court_complex_name)
                court_complex_codes.append(complex_value)
                logging.info(f"Added court complex: {court_complex_name}.")

        return court_complex_names, court_complex_codes
    
    async def extract_ipc_related_codes(self):
        # Locate all options in the #actcode dropdown
        act_options = self.page.locator('#actcode option')
        act_count = await act_options.count()

        # Regex pattern to match "Indian Penal Code", "IPC", or "I.P.C."
        ipc_regex = re.compile(r'^(I.P.C|IPC|Indian Penal Code)\b.*$', re.IGNORECASE)

        # List to hold IPC-related options
        ipc_related_options = []

        for i in range(act_count):
            option = act_options.nth(i)
            act_text = await option.text_content()
            logging.info(f"ACT TEXT :  {act_text}")

            # Check if the option matches the IPC regex
            if ipc_regex.search(act_text):
                logging.info(f"REGEX MATCHED")
                ipc_related_options.append(act_text)

        # Logging the IPC-related options
        logging.info(f"All IPC-related codes: {ipc_related_options}")
        print(f"All IPC-related codes: {ipc_related_options}")
        return ipc_related_options
        

    async def navigate_state(self):
        logging.info("Navigating state options.")
        state_options = self.page.locator("#sess_state_code option")
        state_count = await state_options.count()
        logging.info(f"Found {state_count} state options.")

        print("State Options Available:")
        for state_i in range(state_count):
            state_option = state_options.nth(state_i)
            state_text = await state_option.text_content()
            print(f"State {state_i + 1}: {state_text}")
            logging.info(f"State {state_i + 1}: {state_text}")

        for state_i in range(state_count):
            logging.info(f"Processing state {state_i + 1}.")
            state_option = state_options.nth(state_i)
            state_value = await state_option.get_attribute('value')
            state_text = await state_option.text_content()
            state_name_for_filename = state_text.lower().strip().replace(" ", "_")
            time.sleep(3)

            if any(substring in state_text for substring in ['select', 'state', 'select_state']):
                logging.info("Skipping 'Select State' option.")
                continue
            else:
                logging.info(f"Selected state: {state_text}.")
                await self.page.locator('#sess_state_code').select_option(state_value)
                time.sleep(1.5)

                district_value = await self.get_districts()
                if district_value:
                    logging.info(f"Selected district value: {district_value}.")
                    await self.page.locator('#sess_dist_code').select_option(district_value)
                    time.sleep(3)

                    court_names, court_codes = await self.get_court_complexes()
                    if court_codes:
                        for idx, i in enumerate(court_codes):
                            logging.info(f"Selecting court complex with code: {i}.")
                            await self.page.locator('#court_complex_code').select_option(i)
                            time.sleep(2)
                            
                            court_name = court_names[idx]
                            await self.page.locator('//*[@id="act-tabMenu"]').click()
                            time.sleep(2)
                            
                            act_code_selector = '#actcode'

                            act_options = self.page.locator("#actcode option")
                            act_count = await act_options.count()
                            logging.info(f"Found {act_count} act options.")
                            if act_count == 1:
                                logging.info("Only 'Select Act Type' option found, skipping.")
                                continue
                            
                            await self.download_act_codes()
                            
                            ipc_related_codes = await self.extract_ipc_related_codes()
                            #later add this into the loop 
                            print(ipc_related_codes[0])
                            await self.page.locator('#actcode').select_option(ipc_related_codes[0])
                            
                            time.sleep(2.5)
                            await self.page.locator('#under_sec').fill('302')
                            time.sleep(2)
                            await self.page.locator('#radPAct').click()
                            print(f"I have hit page")
                            captcha = input('enter captcha here: ')

                            await self.page.locator('#act_captcha_code').fill(captcha)
                            
                            logging.info("Captcha entered")
                            time.sleep(2.5)

                            await self.page.locator('#frm_act > div:nth-child(5) > div.col-md-auto > button').click()
                            
                            logging.info("Button clicked")
                            await self.page.wait_for_load_state()
                            time.sleep(2.5)
                            # extract html of the page
                            page_content = await self.page.content()

                            await self.page.wait_for_timeout(5000)
                            
                            break
                break

    async def close(self):
        logging.info("Closing the browser.")
        await self.browser.close()
        await self.playwright.stop()
        logging.info("Browser closed.")

async def main():
    url = 'https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus'
    navigator = CourtNavigator(url)

    try:
        await navigator.setup()
        await navigator.navigate_state()
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        await navigator.close()

if __name__ == "__main__":
    asyncio.run(main())
