import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
import requests
from bs4 import BeautifulSoup
import os # For accessing environment variables for API keys if preferred

class AIAgent:
    def __init__(self, driver_path=None, llm_config=None):
        """
        Initializes the AI Agent with a Selenium WebDriver and LLM configuration.
        :param driver_path: Path to your WebDriver executable (e.g., 'chromedriver').
                            If None, assumes WebDriver is in your system's PATH.
        :param llm_config: Dictionary containing 'provider', 'model', 'api_key', 'temperature'.
        """
        self.logs = [] # List to store logs to be returned to the web interface
        self.llm_config = llm_config if llm_config else {}

        options = webdriver.ChromeOptions()
        # Optional: Run in headless mode for no UI, useful for server environments
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--window-size=1920,1080')

        try:
            if driver_path:
                self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            self._log("Selenium WebDriver initialized.")
        except Exception as e:
            self._log(f"Error initializing WebDriver: {e}")
            self.driver = None # Set driver to None if initialization fails

    def _log(self, message):
        """Appends a message to the internal log list."""
        print(message) # Also print to console for real-time debugging
        self.logs.append(message)

    def _get_page_context(self):
        """
        Extracts visible text and a simplified representation of interactive elements
        from the current page for the LLM to analyze.
        Returns a dictionary with 'current_url', 'text_content', and 'interactive_elements'.
        """
        if not self.driver:
            self._log("WebDriver not initialized. Cannot get page context.")
            return {
                "current_url": "N/A",
                "text_content": "WebDriver not initialized.",
                "interactive_elements": []
            }

        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()
            
            text_content = soup.get_text(separator=' ', strip=True)
            if len(text_content) > 2000:
                text_content = text_content[:2000] + "..."
            
            interactive_elements = []
            elements = self.driver.find_elements(By.XPATH, "//button | //a | //input[not(@type='hidden')] | //textarea | //select")
            
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            for i, elem in enumerate(elements):
                try:
                    if not elem.is_displayed() or not elem.is_enabled():
                        continue

                    llm_identifier = f"llm_elem_{i}" 
                    self.driver.execute_script(f"arguments[0].setAttribute('data-llm-id', '{llm_identifier}');", elem)

                    tag = elem.tag_name
                    elem_info = {'tag': tag, 'id': llm_identifier} 

                    original_id = elem.get_attribute('id')
                    if original_id:
                        elem_info['original_html_id'] = original_id 
                    
                    name = elem.get_attribute('name')
                    if name:
                        elem_info['name'] = name
                    
                    text = elem.text.strip()
                    if text:
                        elem_info['text'] = text
                    
                    value = elem.get_attribute('value')
                    if value and tag == 'input':
                        elem_info['value'] = value
                    
                    placeholder = elem.get_attribute('placeholder')
                    if placeholder:
                        elem_info['placeholder'] = placeholder
                    
                    aria_label = elem.get_attribute('aria-label')
                    if aria_label:
                        elem_info['aria_label'] = aria_label
                    
                    if tag == 'input':
                        elem_info['type'] = elem.get_attribute('type')

                    location = elem.location
                    size = elem.size
                    
                    elem_info['bounding_box'] = {
                        'x': location['x'],
                        'y': location['y'],
                        'width': size['width'],
                        'height': size['height']
                    }

                    is_visible_in_viewport = (
                        location['x'] >= 0 and
                        location['y'] >= 0 and
                        (location['x'] + size['width']) <= viewport_width and
                        (location['y'] + size['height']) <= viewport_height
                    )
                    elem_info['is_visible_in_viewport'] = is_visible_in_viewport
                    
                    lower_combined_text = (
                        (text or '') + ' ' + 
                        (value or '') + ' ' + 
                        (placeholder or '') + ' ' + 
                        (aria_label or '') + ' ' +
                        (original_id or '')
                    ).lower()

                    if any(keyword in lower_combined_text for keyword in ['accept', 'agree', 'ok', 'continue', 'cookie', 'consent', 'privacy']):
                        elem_info['is_cookie_consent_button'] = True

                    if any(keyword in lower_combined_text for keyword in ['skip ads', 'skip ad', 'skip', 'advertisement', 'ad in']):
                        elem_info['is_skip_ad_button'] = True
                    if original_id in ['ytp-ad-skip-button', 'skip-button'] or \
                       'ytp-ad-skip-button-container' in elem.get_attribute('class') or \
                       'ytp-skip-ad-button' in elem.get_attribute('class') or \
                       'ytp-ad-overlay-close-button' in elem.get_attribute('class') or \
                       (aria_label and 'skip' in aria_label.lower()):
                        elem_info['is_skip_ad_button'] = True

                    if tag == 'a':
                        href = elem.get_attribute('href')
                        if href and ('/watch?v=' in href or 'youtube.com/video/' in href):
                            elem_info['is_video_link'] = True

                    if text or value or name or placeholder or aria_label or tag in ['button', 'a'] or original_id:
                        interactive_elements.append(elem_info)
                except selenium.common.exceptions.StaleElementReferenceException:
                    continue
                except Exception as e:
                    self._log(f"Warning: Could not process element due to: {e}")
                    continue
            
            return {
                "current_url": self.driver.current_url,
                "text_content": text_content,
                "interactive_elements": interactive_elements
            }
        except Exception as e:
            self._log(f"Error getting page context: {e}")
            return {
                "current_url": self.driver.current_url,
                "text_content": "Could not retrieve full page content.",
                "interactive_elements": []
            }

    def _call_llm(self, prompt):
        """Handles the API call to the selected LLM (Gemini or OpenAI)."""
        provider = self.llm_config.get('provider')
        model_name = self.llm_config.get('model')
        api_key = self.llm_config.get('api_key')
        temperature = self.llm_config.get('temperature', 0.7)

        if not api_key:
            raise ValueError("API Key is not provided.")
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "The action to perform.",
                            "enum": ["navigate_to", "click_element", "type_text", "task_complete"]
                        },
                        "params": {
                            "type": "OBJECT",
                            "description": "Parameters for the action.",
                            "properties": {
                                "url": {"type": "STRING", "description": "URL for navigate_to action."},
                                "id": {"type": "STRING", "description": "ID of the element for click_element or type_text action. This should be the 'id' from the interactive_elements list."},
                                "text": {"type": "STRING", "description": "Text to type for type_text action."},
                                "message": {"type": "STRING", "description": "Completion message for task_complete action."}
                            }
                        }
                    },
                    "required": ["action", "params"]
                }
            }
        }

        if provider == 'gemini':
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        elif provider == 'openai':
            # OpenAI API structure is different
            headers['Authorization'] = f'Bearer {api_key}'
            api_url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "response_format": {"type": "json_object"} # For structured JSON output
            }
        else:
            raise ValueError("Unsupported LLM provider specified.")

        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()

            if provider == 'gemini':
                if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
                    json_text = result['candidates'][0].get('content').get('parts')[0].get('text')
                    if json_text:
                        return json.loads(json_text)
            elif provider == 'openai':
                if result.get('choices') and result['choices'][0].get('message') and result['choices'][0]['message'].get('content'):
                    json_text = result['choices'][0]['message'].get('content')
                    if json_text:
                        # OpenAI might return JSON as a string, need to parse it
                        return json.loads(json_text)
            
            self._log(f"LLM response structure unexpected or missing content for {provider}: {result}")
            return {"action": "task_complete", "params": {"message": f"LLM failed to provide a valid action due to unexpected response structure from {provider}."}}

        except requests.exceptions.RequestException as e:
            self._log(f"API call failed for {provider}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self._log(f"API Response Status Code: {e.response.status_code}")
                self._log(f"API Response Body: {e.response.text}")
            return {"action": "task_complete", "params": {"message": f"API call failed for {provider}: {e}"}}
        except json.JSONDecodeError as e:
            self._log(f"Failed to decode JSON from LLM response for {provider}: {e}")
            self._log(f"Raw LLM response (if available): {response.text if 'response' in locals() else 'N/A'}")
            return {"action": "task_complete", "params": {"message": f"Failed to decode LLM response: {e}"}}
        except Exception as e:
            self._log(f"An unexpected error occurred during LLM interaction for {provider}: {e}")
            return {"action": "task_complete", "params": {"message": f"Unexpected error during LLM interaction for {provider}: {e}"}}


    def _get_llm_action(self, page_context, task_description):
        """
        Sends the current page context and the task description to the LLM.
        The LLM is prompted to return a JSON string specifying the next action.
        """
        prompt = f"""
        You are an AI web navigation agent. Your goal is to help me complete a task on a website.
        I will provide you with the current page's URL, visible text content, and a list of interactive elements.
        Each interactive element will have a unique 'id' (e.g., 'llm_elem_0'). This 'id' is what you MUST use for 'click_element' or 'type_text' actions. Some elements might also have an 'original_html_id' for additional context, but use the 'id' for actions.
        Each element will also have a 'bounding_box' (x, y, width, height) and an 'is_visible_in_viewport' flag.

        Some elements might also have an 'is_cookie_consent_button: true' flag if they appear to be related to cookie consent.
        Some elements might also have an 'is_skip_ad_button: true' flag if they appear to be a button to skip an advertisement.
        Some elements (links) might also have an 'is_video_link: true' flag if they lead to a video (e.g., on YouTube).

        Your task is: "{task_description}"

        **IMPORTANT RULES (Priority Order):**
        1.  If any interactive element has `is_cookie_consent_button: true` AND `is_visible_in_viewport: true`, your ABSOLUTE HIGHEST PRIORITY is to click that button to dismiss the cookie consent. You MUST select one of these buttons if present, before attempting any other action related to the main task. Look for buttons with text like 'Accept', 'Agree', 'OK', 'Continue', or related to 'cookies' or 'consent'.
        2.  If any interactive element has `is_skip_ad_button: true` AND `is_visible_in_viewport: true`, your NEXT HIGHEST PRIORITY is to click that button to skip the advertisement. You MUST select one of these buttons if present, before attempting any other action related to the main task (unless a cookie consent button is present and needs to be clicked first). Look for buttons with text like 'Skip Ads', 'Skip Ad', 'Skip', 'Advertisement'.
        3.  When choosing an element to interact with (click or type), **always prefer elements where `is_visible_in_viewport` is `true`**. Elements with negative Y-coordinates or very large Y-coordinates in their `bounding_box` are likely off-screen and not immediately clickable.
        4.  When the task involves playing a video (e.g., on YouTube), **always prioritize clicking elements where `is_video_link: true`**.

        Based on the provided information, decide the next best action to take.
        Your response MUST be a JSON object with two keys: "action" and "params".

        Possible actions and their parameters:
        1.  "navigate_to": {{"url": "https://example.com"}}
            - Use this to go to a completely new URL.
        2.  "click_element": {{"id": "id_from_interactive_elements_list"}}
            - Use this to click a button, link, or other clickable element. Ensure the 'id' is the 'id' from the 'interactive_elements' list.
        3.  "type_text": {{"id": "id_from_interactive_elements_list", "text": "your search query"}}
            - Use this to type text into an input field or textarea. Ensure the 'id' is the 'id' and the element is an input/textarea. After typing, if it's a search bar, consider if a "click_element" on a search button or simulating "Keys.RETURN" is needed.
        4.  "task_complete": {{"message": "Optional message about task completion"}}
            - Use this when the task is successfully completed.

        Current Page Context:
        {json.dumps(page_context, indent=2)}

        Provide only the JSON response.
        """
        return self._call_llm(prompt)

    def run_task(self, initial_url, task_description, max_steps=7):
        """
        Runs the AI agent to complete a web-based task.
        :param initial_url: The starting URL for the task.
        :param task_description: A clear description of the task to perform.
        :param max_steps: Maximum number of actions the agent can take to prevent infinite loops.
        :return: A list of log messages from the task execution.
        """
        self.logs = [] # Clear logs for new task
        if not self.driver:
            self._log("Agent cannot run task: WebDriver not initialized.")
            return self.logs

        try:
            self.driver.get(initial_url)
            self._log(f"Starting task: '{task_description}' on {initial_url}")

            for step in range(max_steps):
                self._log(f"\n--- Step {step + 1} ---")
                self._log(f"Current URL: {self.driver.current_url}")

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                page_context = self._get_page_context()
                self._log("Page context extracted for LLM.")
                
                llm_response = self._get_llm_action(page_context, task_description)
                self._log(f"LLM Action: {llm_response.get('action')}, Params: {llm_response.get('params')}")

                action = llm_response.get('action')
                params = llm_response.get('params', {})

                if action == "navigate_to":
                    url = params.get("url")
                    if url:
                        self._log(f"Navigating to: {url}")
                        self.driver.get(url)
                    else:
                        self._log("Error: 'navigate_to' action missing 'url' parameter. Terminating.")
                        break
                elif action == "click_element":
                    element_llm_id = params.get("id")
                    if element_llm_id:
                        try:
                            element = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-llm-id='{element_llm_id}']"))
                            )
                            self._log(f"Attempting to click element with data-llm-id: {element_llm_id}")
                            element.click()
                        except selenium.common.exceptions.ElementClickInterceptedException as e:
                            self._log(f"Error clicking element with data-llm-id '{element_llm_id}': {e}. This often means an overlay (like cookie consent) is blocking the click. Re-evaluating page context.")
                            time.sleep(2)
                            continue
                        except Exception as e:
                            self._log(f"Error clicking element with data-llm-id '{element_llm_id}': {e}. Terminating.")
                            break
                    else:
                        self._log("Error: 'click_element' action missing 'id' parameter. Terminating.")
                        break
                elif action == "type_text":
                    element_llm_id = params.get("id")
                    text_to_type = params.get("text")
                    if element_llm_id and text_to_type is not None:
                        try:
                            element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-llm-id='{element_llm_id}']"))
                            )
                            self._log(f"Typing '{text_to_type}' into element with data-llm-id: {element_llm_id}")
                            element.clear()
                            element.send_keys(text_to_type)
                            element.send_keys(Keys.RETURN) 
                        except Exception as e:
                            self._log(f"Error typing into element with data-llm-id '{element_llm_id}': {e}. Terminating.")
                            break
                    else:
                        self._log("Error: 'type_text' action missing 'id' or 'text' parameter. Terminating.")
                        break
                elif action == "task_complete":
                    self._log(f"Task completed successfully: {params.get('message', 'No message provided.')}")
                    break
                else:
                    self._log(f"Unknown action received from LLM: '{action}'. Terminating.")
                    break
                
                time.sleep(2)

            else:
                self._log(f"Max steps ({max_steps}) reached. Task not fully completed.")
            
        except Exception as e:
            self._log(f"An unexpected error occurred during task execution: {e}")
        finally:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self._log("Selenium WebDriver quit.")
            return self.logs

