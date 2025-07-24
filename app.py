from flask import Flask, render_template, request, jsonify
from agent import AIAgent # Ensure agent.py is in the same directoryi
import os

app = Flask(__name__)

# --- IMPORTANT: Configure ChromeDriver Path ---
# Set this to your ChromeDriver path if it's not in your system's PATH.
# Example: CHROME_DRIVER_PATH = r"C:\Users\YourUser\Downloads\chromedriver.exe"
# If ChromeDriver is in your system's PATH, you can leave this as None.
CHROME_DRIVER_PATH = None 

@app.route('/')
def index():
    """Renders the main web interface."""
    return render_template('index.html')

@app.route('/run_agent', methods=['POST'])
def run_agent_task():
    """Handles the form submission to run the AI agent."""
    data = request.json
    
    api_key = data.get('api_key')
    llm_provider = data.get('llm_provider')
    llm_model = data.get('llm_model')
    temperature = float(data.get('temperature', 0.7)) # Convert to float
    initial_url = data.get('initial_url')
    task_description = data.get('task_description')

    # Basic validation
    if not api_key or not llm_provider or not llm_model or not initial_url or not task_description:
        return jsonify({"status": "error", "logs": ["Missing required fields. Please fill all inputs."]})

    llm_config = {
        'provider': llm_provider,
        'model': llm_model,
        'api_key': api_key,
        'temperature': temperature
    }

    # Initialize and run the agent
    # The AIAgent class now takes llm_config directly
    agent = AIAgent(driver_path=CHROME_DRIVER_PATH, llm_config=llm_config)
    
    # Run the task and get logs
    logs = agent.run_task(initial_url, task_description)
    
    return jsonify({"status": "completed", "logs": logs})

if __name__ == '__main__':
    # Create the 'templates' directory if it doesn't exist
    # This ensures render_template can find index.html
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True) # debug=True allows auto-reloading and better error messages
