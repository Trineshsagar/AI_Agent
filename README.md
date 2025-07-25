# AI_Agent
A LLM and python based project which can do all your internet works by a single prompt.

Your AI Web Agent: Intelligent Web Automation, Simplified 🚀
Navigate, interact, and automate any website with the power of AI, all from a user-friendly local interface. 🤖

Your AI Web Agent is a powerful yet accessible tool designed to bring intelligent automation to your everyday web tasks. Say goodbye to complex scripting—simply describe what you need, and watch it handle the web like a pro: navigating pages, interacting with elements, and completing your goals effortlessly. 🌐

Key Capabilities 🔑
Intelligent Web Interaction 🧠: Powered by cutting-edge Large Language Models (LLMs) like Google Gemini and OpenAI GPT, the agent interprets your natural language commands and smartly chooses the optimal actions on any webpage.

Browser Automation ⚙️: Effortlessly handles essential web tasks, including typing in search fields, clicking buttons and links, and jumping to specific URLs.

Dynamic Context Awareness 👀: The agent "views" the webpage, spotting interactive elements, grasping their context (like text, placeholders, or ARIA labels), and even managing annoyances like cookie banners or "skip ad" buttons. It focuses on visible elements for dependable results.

Customizable LLM Control 🎛️: Customize the AI's behavior right from the web interface:

Provider Selection 🔄: Pick between Google Gemini or OpenAI.

Model Flexibility 📊: Choose from various models, from speedy free ones like Gemini 2.0 Flash to robust paid options like Gemini 1.5 Pro, GPT-4o, or GPT-4.

Creativity Slider 🔥: Adjust the LLM's style for precision or creativity with a simple temperature control.

Secure Input 🔒: Input API keys and task prompts directly in the browser, keeping everything tidy and safe.

Local & Private Execution 🛡️: Everything runs on your machine, keeping your data and activities completely private.

Transparent Logging 📜: Monitor real-time logs of actions and decisions in the web interface for total insight.

Why Choose Your AI Web Agent? 💡
Simplicity 😌: Automate intricate web flows without coding beyond setup.

Flexibility 🔄: Adapts to diverse sites and tasks with a smart, evolving AI core.

Control 🎮: Fine-tune the AI model and its decisions with ease.

Transparency 🔍: Track every move with live, clear logging.

Extensibility 🛠️: Based on Python, Flask, and Selenium—perfect for developers to tweak and expand.

This agent isn't just a tool; it's your personal web wizard, making online tasks faster and smarter! ✨

Get Started Today! 📈
Dive in with our easy setup— you'll be automating in minutes:

➡️Install Python and key libraries: Flask, Selenium, BeautifulSoup4, and Requests. 🐍

[requirements.txt](https://github.com/user-attachments/files/21415613/requirements.txt)

#Flask
#selenium
#beautifulsoup4
#requests
#google-generativeai

run the following command to install the requirments

    pip install -r requirments.txt

   * make sure that your computer had Python pre installed to run this tool
     

   * 📲🔛"Download the matching ChromeDriver for your browser version." 🌐  
   
        - make sure that you saved chromedriver in your c:/windows or in the same folder of your tool




  * Grab your API key from Google AI Studio or OpenAI. 🔑

  * Download and  save all the files (app.py ,agent.py, requirments.txt and create another folder as templets\index.html) ,  in the new folder as "ai-agent".

  ➡️ run the following command in the powershell at  c:\ai-agent
  
      python -m venv .venv
     .venv\scripts\activate

➡️ Launch the Flask app on your local server. 🚀

      python app.py

Open the web interface in your browser and start commanding! 🌟

Ready to supercharge your web workflow? Clone the repo, follow these steps, and let the automation begin! If you encounter any hiccups, check the docs or community forums for tips. Happy automating! 🎉
