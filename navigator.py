import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML
from playwright.async_api import async_playwright
import asyncio
import csv
import re
import logging
from PIL import Image
import requests
import pytesseract
from db import (
    get_database_connection_details,
    connect_to_database,
    create_table,
    insert_data,
)
from db2 import (
    create_connection,
    create_table,
    insert_data,
    query_table,
    custom_query,
    create_district_table,
    create_court_table,
    save_html_to_db,
    save_codes_to_db,
    create_html_table,
    fetch_first_two_rows,
    drop_table,
)
import os
import datetime as dt
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

# Configure logging
logging.basicConfig(
    filename="court_navigator.log",  # Log to this file
    level=logging.INFO,  # Log all INFO level and above
    format="%(asctime)s - %(levelname)s - %(message)s",  # Include timestamp
)

# TO-DO: Add section number as a parameter


class CourtNavigator:
    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None
        self.state_options = None
        self.district_options = None
        self.complex_options = None
        self.complex_2_options = None
        self.connection = None
        self.date = dt.datetime.now().strftime("%Y-%m-%d %H:%M %p")

    async def load_page(self):
        await self.page.goto(self.url)
        if await self.page.locator("#validateError button").is_visible():
            await self.page.locator("#validateError button").click()
        logging.info("Page loaded successfully.")

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def setup(self):
        logging.info("Starting Playwright and launching browser.")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        await self.page.goto(self.url)
        if await self.page.locator("#validateError button").is_visible():
            await self.page.locator("#validateError button").click()
        logging.info("Browser launched and initial page setup completed.")

    async def setup_options(self):
        logging.info("Setting up options.")
        self.state_options = self.page.locator("#sess_state_code option")
        self.district_options = self.page.locator("#sess_dist_code option")
        self.complex_options = self.page.locator("#court_complex_code option")
        self.complex_2_options = self.page.locator("#court_complex_code option")
        logging.info("Options setup completed.")

    async def get_districts(self):
        logging.info("Getting district options.")
        district_options = self.page.locator("#sess_dist_code option")
        await self.page.wait_for_selector("#sess_dist_code", state="visible")
        await asyncio.sleep(5)  # Ensure content is fully loaded
        district_count = await district_options.count()
        logging.info(f"Found {district_count} district options.")

        for district_i in range(district_count):
            logging.info(f"Processing district {district_i + 1}.")
            district_option = district_options.nth(district_i)
            district_text = await district_option.text_content()
            district_name_for_filename = district_text.lower().strip().replace(" ", "_")
            await asyncio.sleep(3)
            district_value = await district_option.get_attribute("value")

            if any(
                substring in district_name_for_filename
                for substring in ["select", "select_district"]
            ):
                logging.info("Skipping 'Select District' option.")
                continue
            else:
                logging.info(f"Selected district: {district_text}.")
                return district_value

        logging.error("No valid district found.")
        return None

    async def download_act_codes(self, output_file="act_codes.csv"):
        logging.info("Downloading act codes.")
        act_options = self.page.locator("#actcode option")
        await self.page.wait_for_selector("#actcode", state="visible")
        await asyncio.sleep(5)  # Ensure content is fully loaded

        act_count = await act_options.count()
        logging.info(f"Found {act_count} act options.")

        act_list = []
        for i in range(act_count):
            option = act_options.nth(i)
            act_text = await option.text_content()
            act_value = await option.get_attribute("value")
            act_list.append({"Act Name": act_text, "Act Code": act_value})

        with open(output_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Act Name", "Act Code"])
            writer.writeheader()
            writer.writerows(act_list)

        logging.info(f"Act codes successfully downloaded to {output_file}")

    async def get_court_complexes(self):
        logging.info("Getting court complex options.")
        complex_options = self.page.locator("#court_complex_code option")
        await self.page.wait_for_selector("#court_complex_code", state="visible")
        await asyncio.sleep(5)  # Ensure content is fully loaded

        complex_count = await complex_options.count()
        logging.info(f"Found {complex_count} court complex options.")
        court_complex_names = []
        court_complex_codes = []

        for complex_i in range(complex_count):
            logging.info(f"Processing court complex {complex_i + 1}.")
            complex_option = complex_options.nth(complex_i)
            complex_text = await complex_option.text_content()
            court_complex_name = complex_text.lower().strip().replace(" ", "_")
            complex_value = await complex_option.get_attribute("value")

            if any(
                substring in court_complex_name
                for substring in ["select_court_complex", "select"]
            ):
                logging.info("Skipping 'Select Court Complex' option.")
                continue
            else:
                court_complex_names.append(court_complex_name)
                court_complex_codes.append(complex_value)
                logging.info(f"Added court complex: {court_complex_name}.")

        return court_complex_names, court_complex_codes

    async def extract_ipc_related_codes(self):
        logging.info("Extracting IPC-related codes.")
        if await self.page.locator("#validateError button").is_visible():
            await self.page.locator("#validateError button").click()

        if await self.page.locator("#actcode").is_visible():
            act_options = self.page.locator("#actcode option")
            await self.page.wait_for_selector("#actcode", state="visible")
            await asyncio.sleep(5)  # Ensure content is fully loaded

            act_count = await act_options.count()
            logging.info(f"Found {act_count} act options.")

            ipc_regex = re.compile(
                r"^(I.P.C|IPC|Indian Penal Code)\b.*$", re.IGNORECASE
            )
            ipc_related_options = []

            for i in range(act_count):
                if await self.page.locator("#validateError button").is_visible():
                    await self.page.locator("#validateError button").click()

                option = act_options.nth(i)
                if await self.page.locator("#validateError button").is_visible():
                    await self.page.locator("#validateError button").click()

                act_text = await option.text_content()
                logging.info(f"ACT TEXT: {act_text}")

                if ipc_regex.search(act_text):
                    logging.info(f"REGEX MATCHED: {act_text}")
                    ipc_related_options.append(act_text)

            logging.info(f"All IPC-related codes: {ipc_related_options}")
            return ipc_related_options

    async def process_act_codes(self, section_number="302"):
        logging.info("Processing act codes.")
        ipc_related_codes = await self.extract_ipc_related_codes()

        if ipc_related_codes:
            first_ipc_code = ipc_related_codes[0]
            logging.info(f"Selecting IPC-related code: {first_ipc_code}.")
            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            await self.page.locator("#actcode").select_option(value=first_ipc_code)
            await asyncio.sleep(5)  # Increased wait time after selecting option

            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            await self.page.locator("#under_sec").fill("302")
            await asyncio.sleep(5)  # Increased wait time after filling field

            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            await self.page.locator("#radPAct").click()
            logging.info("Clicked the page.")
            # captcha = input("Enter captcha here: ")

            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            answer = await self.fix_captcha()
            await asyncio.sleep(5)  # Increased wait time after filling captcha
            await self.page.locator("#act_captcha_code").fill(answer)
            await asyncio.sleep(60)  # Increased wait time after filling captcha
            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            logging.info("Captcha entered.")

            # TO-DO - Add a check for the captcha error message

            await asyncio.sleep(5)  # Increased wait time after filling captcha

            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            await self.page.locator(
                "#frm_act > div:nth-child(5) > div.col-md-auto > button"
            ).click()
            logging.info("Submit button clicked.")

            if await self.page.locator("#validateError button").is_visible():
                await self.page.locator("#validateError button").click()

            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)  # Increased wait time after page load

            page_content = await self.page.content()
            await self.page.wait_for_timeout(5000)
            # print("Page content from processing code:", page_content)
            return page_content
        else:
            logging.error("No IPC-related codes found.")
            return None

    async def fix_captcha(self):
        if await self.page.locator("#validateError button").is_visible():
            await self.page.locator("#validateError button").click()

        if await self.page.locator("#div_captcha_act #captcha_image").is_visible():
            captcha_image = await self.page.locator(
                "#div_captcha_act #captcha_image"
            ).screenshot(type="png")
            with open("files/captcha.png", "wb") as fp:
                # print("Saved as captcha.png")
                fp.write(captcha_image)
            image = Image.open("files/captcha.png")
            # image
            answer = pytesseract.image_to_string(image).strip()
            print("Captcha answer:", answer)
            return answer
        else:
            logging.error("No captcha image found.")
            return None

    async def process_state(self, state_option):
        logging.info("Processing state.")
        state_value = await state_option.get_attribute("value")
        state_text = await state_option.text_content()
        state_name_for_filename = state_text.lower().strip().replace(" ", "_")
        await asyncio.sleep(5)  # Ensure UI is stable

        if any(
            substring in state_text for substring in ["select", "state", "select_state"]
        ):
            logging.info("Skipping 'Select State' option.")
            return False
        else:
            logging.info(f"Selected state: {state_text}.")
            await self.page.locator("#sess_state_code").select_option(state_value)
            await asyncio.sleep(5)  # Wait after selecting state

            district_value = await self.get_districts()
            if district_value:
                logging.info(f"Selected district value: {district_value}.")
                await self.page.locator("#sess_dist_code").select_option(district_value)
                await asyncio.sleep(5)  # Wait after selecting district

                court_names, court_codes = await self.get_court_complexes()
                if court_codes:
                    for idx, code in enumerate(court_codes):
                        logging.info(f"Selecting court complex with code: {code}.")
                        await self.page.locator("#court_complex_code").select_option(
                            code
                        )
                        await asyncio.sleep(5)  # Wait after selecting court complex

                        court_name = court_names[idx]
                        await self.page.locator('//*[@id="act-tabMenu"]').click()
                        await asyncio.sleep(5)  # Wait after clicking ACT tab

                        await self.process_act_codes()
                        logging.info(
                            f"Completed processing for {court_name} in {district_value} which is {state_text}."
                        )
                        break  # Exit after processing one court complex
                return True
            else:
                logging.error("Failed to select a district.")
                return False

    async def navigate_state_2(self):
        logging.info("Navigating state options.")
        state_options = self.page.locator("#sess_state_code option")
        await self.page.wait_for_selector("#sess_state_code", state="visible")
        await asyncio.sleep(5)  # Ensure content is fully loaded

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
            if await self.process_state(state_option):
                break  # Exit after processing one state

    async def navigate_state(self):
        logging.info("Navigating state options.")

        # Wait for the state dropdown to be visible
        await self.page.wait_for_selector("#sess_state_code", state="visible")

        # Locate state options and count them
        # state_options = self.page.locator("#sess_state_code option")
        state_count = await self.state_options.count()
        logging.info(f"Found {state_count} state options.")

        # Print and log the state options
        state_names = await self.state_options.evaluate_all(
            "(options) => options.map(option => option.textContent)"
        )
        state_values = await self.state_options.evaluate_all(
            "(options) => options.map(option => option.getAttribute('value'))"
        )
        print("State Options Available:")
        print("State Names:", state_names)
        print("State Values:", state_values)

        insert_sql = self.create_insert_query(state_names, state_values)
        try:
            insert_data(self.connection, insert_sql)
        except Exception as e:
            logging.error(f"Error inserting data: {e}")

    def create_insert_query(self, state_names, state_codes):
        # Ensure the lists are of the same length
        if len(state_names) != len(state_codes):
            raise ValueError("state_names and state_codes must have the same length")

        # Generate the SQL statement
        insert_sql = "INSERT INTO States (state_name, state_code) VALUES "

        # List to hold each row's SQL
        values_sql = []

        for name, code in zip(state_names, state_codes):
            values_sql.append(f"('{name}', '{code}')")

        # Join all values into the final SQL statement
        insert_sql += ", ".join(values_sql) + ";"

        # Print or execute the SQL statement
        print(insert_sql)

        return insert_sql

    async def navigate_district(self, state_code):
        logging.info("Navigating district options.")
        # district_options = self.page.locator("#sess_dist_code option")
        await self.page.wait_for_selector("#sess_dist_code", state="visible")
        await asyncio.sleep(5)
        district_count = await self.page.locator("#sess_dist_code option").count()
        logging.info(f"Found {district_count} district options.")
        # Get all district options in one go
        district_elements = await self.page.locator(
            "#sess_dist_code option"
        ).evaluate_all(
            "(options) => options.map(option => ({text: option.textContent.trim(), value: option.getAttribute('value')}))"
        )

        # Filter out invalid options and extract names and codes
        valid_districts = [
            (district["text"], district["value"])
            for district in district_elements
            if not any(
                substring in district["text"].lower()
                for substring in ["select", "select_district"]
            )
        ]

        # Unpack valid districts into separate lists for names and codes
        district_names, district_codes = (
            zip(*valid_districts) if valid_districts else ([], [])
        )

        return district_names, district_codes

    async def process_states_3(self):
        await self.setup()
        await self.setup_options()
        # Wait for the state dropdown to be visible
        await self.page.wait_for_selector("#sess_state_code", state="visible")

        query_sql = "SELECT state_code FROM States"
        state_codes = custom_query(self.connection, query_sql)
        state_codes = [code[0] for code in state_codes]

        for state_code in state_codes[1:]:
            logging.info(f"Processing state {state_code}.")
            await self.page.locator("#sess_state_code").select_option(state_code)
            await asyncio.sleep(5)
            district_names, district_codes = await self.navigate_district(state_code)
            await self.page.locator("#sess_state_code").select_option(state_code)
            await asyncio.sleep(5)
            court_names, court_codes = await self.get_court_complexes()
            insert_sql = await self.create_district_query(
                state_code, district_names, district_codes
            )
            print("We got the insert sql")
            print(insert_sql)
            try:
                print("We are here")
                insert_data(self.connection, insert_sql)
            except Exception as e:
                logging.error(f"Error inserting data: {e}")

            await asyncio.sleep(5)

    async def get_court_complexes_3(self, state_code, district_code):
        await self.setup()
        await self.setup_options()
        # Wait for the state dropdown to be visible
        await self.page.wait_for_selector("#sess_state_code", state="visible")
        await self.page.locator("#sess_state_code").select_option(state_code)
        # Wait for the district dropdown to be visible
        try:
            await self.page.wait_for_selector("#sess_dist_code", state="visible")
            await self.page.locator("#sess_dist_code").select_option(district_code)
        except Exception as e:
            await self.setup()
            await self.setup_options()
            # Wait for the state dropdown to be visible
            await self.page.wait_for_selector("#sess_state_code", state="visible")
            await self.page.locator("#sess_state_code").select_option(state_code)
            await self.page.wait_for_selector("#sess_dist_code", state="visible")
            await self.page.locator("#sess_dist_code").select_option(district_code)

        await asyncio.sleep(5)

        court_names, court_codes = await self.get_court_complexes()

        if court_codes:
            for idx, code in enumerate(court_codes):
                court_name = court_names[idx]
                logging.info(f"Selecting court complex with code: {code}.")
                await self.page.locator("#court_complex_code").select_option(code)
                await asyncio.sleep(5)  # Wait after selecting court complex

                if await self.page.locator("#validateError button").is_visible():
                    await self.page.locator("#validateError button").click()

                logging.info(f"Processing court complex_2 {court_names[idx]}.")
                if await self.page.locator("#court_est_code").is_visible():
                    logging.info("Selector #court_est_code found. ")
                    await self.page.wait_for_selector(
                        "#court_est_code", state="visible"
                    )
                    await asyncio.sleep(5)  # Ensure content is fully loaded
                    court_est_options = self.page.locator("#court_est_code option")
                    court_est_count = await court_est_options.count()
                    logging.info(f"Found {court_est_count} court_est options.")
                    court_est_names = []
                    court_est_codes = []
                    for idx in range(court_est_count):
                        court_est_option = court_est_options.nth(idx)
                        court_est_text = await court_est_option.text_content()
                        court_est_value = await court_est_option.get_attribute("value")
                        save_codes_to_db(
                            self.connection,
                            self.date,
                            state_code,
                            district_code,
                            code,
                            court_name,
                            court_est_value,
                            court_est_text,
                        )
                        court_est_names.append(court_est_text)
                        court_est_codes.append(court_est_value)
                        logging.info(f"Added court_est: {court_est_text}.")
                else:
                    save_codes_to_db(
                        self.connection,
                        self.date,
                        state_code,
                        district_code,
                        code,
                        court_name,
                        "E003: No court establishment found",
                        "E003: No court establishment found",
                    )

    async def get_court_complexes_2(self, state_code, district_code):
        # await self.setup()
        # await self.setup_options()
        # Wait for the state dropdown to be visible
        await self.page.wait_for_selector("#sess_state_code", state="visible")
        await self.page.locator("#sess_state_code").select_option(state_code)
        # Wait for the district dropdown to be visible
        await self.page.wait_for_selector("#sess_dist_code", state="visible")
        await self.page.locator("#sess_dist_code").select_option(district_code)
        await asyncio.sleep(5)

        court_names, court_codes = await self.get_court_complexes()

        if court_codes:
            for idx, code in enumerate(court_codes):
                court_name = court_names[idx]
                logging.info(f"Selecting court complex with code: {code}.")
                await self.page.locator("#court_complex_code").select_option(code)
                await asyncio.sleep(5)  # Wait after selecting court complex

                if await self.page.locator("#validateError button").is_visible():
                    await self.page.locator("#validateError button").click()

                logging.info(f"Processing court complex_2 {court_names[idx]}.")
                if await self.page.locator("#court_est_code").is_visible():
                    logging.info("Selector #court_est_code found. ")
                    await self.page.wait_for_selector(
                        "#court_est_code", state="visible"
                    )
                    await asyncio.sleep(5)  # Ensure content is fully loaded
                    court_est_options = self.page.locator("#court_est_code option")
                    court_est_count = await court_est_options.count()
                    logging.info(f"Found {court_est_count} court_est options.")
                    court_est_names = []
                    court_est_codes = []
                    for idx in range(court_est_count):
                        court_est_option = court_est_options.nth(idx)
                        court_est_text = await court_est_option.text_content()
                        court_est_value = await court_est_option.get_attribute("value")
                        court_est_names.append(court_est_text)
                        court_est_codes.append(court_est_value)
                        logging.info(f"Added court_est: {court_est_text}.")

                    for idx, code in enumerate(court_est_codes):
                        court_est_name = court_est_names[idx]
                        if any(
                            substring in court_est_name.lower()
                            for substring in ["select", "state", "select_state"]
                        ):
                            logging.info(
                                "Skipping 'Select Court Establishment' option."
                            )
                            continue
                        else:
                            if await self.page.locator(
                                "#validateError button"
                            ).is_visible():
                                await self.page.locator("#validateError button").click()
                            logging.info(f"Selecting court_est with code: {code}.")
                            await self.page.locator("#court_est_code").select_option(
                                code
                            )
                            await asyncio.sleep(5)

                            if await self.page.locator(
                                "#validateError button"
                            ).is_visible():
                                await self.page.locator("#validateError button").click()

                            await self.page.locator('//*[@id="act-tabMenu"]').click()
                            await asyncio.sleep(5)  # Wait after clicking ACT tab

                            if await self.page.locator(
                                "#validateError button"
                            ).is_visible():
                                await self.page.locator("#validateError button").click()

                            page_content = await self.process_act_codes()
                            if page_content is None:
                                logging.info(
                                    f"Completed processing for {court_name}. No page content."
                                )
                                # Save the HTML content to the database
                                save_html_to_db(
                                    self.connection,
                                    self.date,
                                    state_code,
                                    district_code,
                                    court_name,
                                    court_est_name,
                                    "Error Code: 001 : No IPC related codes found.",
                                )
                                # self.connection.commit()
                                continue
                            else:
                                logging.info(f"Completed processing for {court_name}.")
                                # print("Page content:", page_content)
                                # break  # Exit after processing one court complex

                                # Adding the district name as a div at the end of the page content
                                full_page_content = (
                                    page_content
                                    + f'<div class="dist_code">{district_code}</div>'
                                )

                                # Save the HTML content to the database
                                save_html_to_db(
                                    self.date,
                                    self.connection,
                                    state_code,
                                    district_code,
                                    court_name,
                                    court_est_name,
                                    full_page_content,
                                )
                                # self.connection.commit()

                else:
                    logging.error("No Court Establishment found.")
                    court_name = court_names[idx]
                    if await self.page.locator("#validateError button").is_visible():
                        await self.page.locator("#validateError button").click()

                    await self.page.locator('//*[@id="act-tabMenu"]').click()
                    await asyncio.sleep(5)  # Wait after clicking ACT tab

                    if await self.page.locator("#validateError button").is_visible():
                        await self.page.locator("#validateError button").click()

                    page_content = await self.process_act_codes()
                    if page_content is None:
                        logging.info(
                            f"Completed processing for {court_name}. No page content."
                        )
                        # Save the HTML content to the database
                        save_html_to_db(
                            self.date,
                            self.connection,
                            state_code,
                            district_code,
                            court_name,
                            "E003: No court establishment found",
                            "E001: No IPC related codes found.",
                        )
                        # self.connection.commit()
                        continue
                    else:
                        # Adding the district name as a div at the end of the page content
                        full_page_content = (
                            page_content
                            + f'<div class="dist_code">{district_code}</div>'
                        )

                        # Save the HTML content to the database
                        save_html_to_db(
                            self.date,
                            self.connection,
                            state_code,
                            district_code,
                            court_name,
                            "E003: No court establishment found",
                            full_page_content,
                        )
                        # self.connection.commit()
                        logging.info(f"Completed processing for {court_name}.")

                # return False

    async def create_district_query(self, state_code, district_names, district_codes):
        # Ensure the lists are of the same length
        if len(district_names) != len(district_codes):
            raise ValueError(
                "district_names and district_codes must have the same length"
            )

        # Generate the SQL statement
        insert_sql = (
            "INSERT INTO Districts (state_code, district_name, district_code) VALUES "
        )

        # List to hold each row's SQL
        values_sql = []

        for name, code in zip(district_names, district_codes):
            values_sql.append(f"('{state_code}', '{name}', '{code}')")

        # Join all values into the final SQL statement
        insert_sql += ", ".join(values_sql) + ";"

        # Print or execute the SQL statement
        print(insert_sql)

        return insert_sql

    async def process_state_2(self, state_name, state_value):
        # Process each state and break after the first successful processing
        # Wait for the state dropdown to be visible
        await self.page.wait_for_selector("#sess_state_code", state="visible")
        # Locate state options and count them
        logging.info(f"Processing state {state_name}.")
        state_option = self.state_options.nth(state_value)
        if await self.process_state(state_option):
            print("Successfully processed a state.")
            # Exit after processing one state

    async def set_state(self, state_name, state_value):
        logging.info(f"Setting state to {state_name}.")
        await self.state_options.select_option(state_value)
        await asyncio.sleep(5)

        state_name_for_filename = state_name.lower().strip().replace(" ", "_")

    async def close(self):
        logging.info("Closing the browser.")
        await self.browser.close()
        await self.playwright.stop()
        logging.info("Browser closed.")

    async def setup_db(self):
        # Create a connection to the local SQLite database
        db_file = "jd-master-db.db"
        if os.path.exists(db_file):
            self.connection = create_connection(db_file)
        else:
            logging.error("Database file does not exist.")
            self.connection = create_connection(db_file)
        if not self.connection:
            return
        else:
            logging.info("Connection to SQLite database established.")

        # Create a table
        create_table(self.connection)

        # return self.connection
        return self.connection

    async def get_act_codes(
    connection=None,
    state_code="28",
    district_code="1",
    court_complex_code="1280004",
    est_code="",
    act_code
):

    # Get today's date
    date_scraped = datetime.date.today()
    logging.basicConfig(level=logging.INFO)

    # Define the URL
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/fillActType"

    # Define the headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # Define the data (parameters)
    data = {
        "state_code": state_code,
        "dist_code": district_code,
        "court_complex_code": court_complex_code,
        "est_code": est_code,
        "search_act": "",
        "ajax_req": "true",
        "app_token": "",
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=data)

    # Print the response
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code == 200:
        print("Request Successful")

        response_text = response.text

        # Parse the JSON response
        response_data = json.loads(response_text)

        # Extract the act_list HTML
        act_list_html = response_data.get("act_list", "")

        # Use BeautifulSoup to parse the HTML options
        soup = BeautifulSoup(act_list_html, "html.parser")

        # Initialize an empty dictionary for storing the ACT codes and their corresponding details
        filtered_act_dict = {}

        # Compile your regex for filtering act names
        ipc_regex = re.compile(r"^(I.P.C|IPC|Indian Penal Code)\b.*$", re.IGNORECASE)

        options = soup.find_all("option")
        print("Number of Options:", len(options))

        # Loop through each <option> tag and extract the value and text
        for index, option in enumerate(soup.find_all("option")):
            act_code = option.get("value")
            act_name = option.text.strip()

            # Apply regex filtering
            if act_code and act_name and act_code != "" and ipc_regex.search(act_name):
                logging.info(f"REGEX MATCHED: {act_name}")
                save_acts_to_db(
                    connection,
                    date_scraped,
                    state_code,
                    district_code,
                    court_complex_code,
                    est_code,
                    act_code,
                    act_name,
                )



async def main():
    print("----------------Starting main function----------------")
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus"
    navigator = CourtNavigator(url)

    try:
        # await navigator.setup()
        # await navigator.setup_options()
        connect = await navigator.setup_db()
        navigator.connection = connect
        # await navigator.navigate_state()
        # print("Creating district table.")
        # print(navigator.connection)
        # create_district_table(navigator.connection)
        # print("District table created.")
        # await navigator.process_states_3()
        # drop_table(navigator.connection, "CourtPages")
        # create_html_table(navigator.connection)
        create_court_table(navigator.connection)
        print("Courts table created.")
        rows = fetch_first_two_rows(navigator.connection)
        if rows:
            for row in rows:
                state_code, district_name, district_code = row
                print(f"State Code: {state_code}, District Name: {district_code}")
                # State - Karnataka - 3, District - Udupi - 16
                # State - Karnataka - 3, District - Chamrajnagar - 27
                # State - Assam - 6, District - Hojai - 30
                # State - Punjab - 22, District - Amritsar - 8
                # await navigator.get_court_complexes_2("22", "8")
                await navigator.get_court_complexes_3(state_code, district_code)
                await navigator.browser.close()
                print("Processing next row.")
                # break
        else:
            logging.error("No rows found.")

    except Exception as e:
        # connect.commit()
        # connect.close()
        logging.error(f"An error occurred: {e}")
    finally:
        connect.commit()
        connect.close()
        await navigator.close()


if __name__ == "__main__":
    asyncio.run(main())
