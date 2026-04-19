

# Luna AI scrrenshots

### Home Screen
![Home](https://github.com/shivanshu099/luna_agent_chatbot_version_3/blob/main/Screenshot_1.png)

### Settings
![Settings](https://github.com/shivanshu099/luna_agent_chatbot_version_3/blob/main/Screenshot_2.png)




# Luna AI

Luna AI is a modern desktop AI assistant with a sleek interface, voice interaction capabilities, and persistent memory. It connects to multiple powerful LLM providers, including Groq, Google Gemini, and locally hosted models via Ollama.

## Features

- **Modern GUI**: A beautiful dark-themed interface built with `tkinter`, featuring tabbed navigation for Chat and Settings.
- **Voice Mode**: Real-time voice interaction with push-to-talk capability, utilizing Speech-to-Text and Text-to-Speech.
- **Dynamic Avatars**: Visual feedback during AI processing with dynamic animations and avatars.
- **Long-term Memory**: Built-in ChromaDB integration allows the AI to store and retrieve information across sessions.
- **Web & Tool Integration**: Capable of executing multi-step workflows, fetching location data via map searches, and using Playwright for automated operations.
- **Multi-Provider Support**: Easily switch between Groq, Gemini, and Ollama to balance speed, cost, and local privacy.

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) (if using local models)
- API Keys for Google Gemini or Groq (added to `.env`)


get gemini api from here  https://www.google.com/aclk?sa=L&ai=DChsSEwiG0Oa-vIuQAxXsq2YCHVnII0kYACICCAEQABoCc20&ae=2&co=1&ase=2&gclid=EAIaIQobChMIhtDmvryLkAMV7KtmAh1ZyCNJEAAYASAAEgKhvPD_BwE&cid=CAASN-Roxlv1kMkccYUZxr3BU5mCGmQa8G4e79pHOTRRCaOaKu3g5MXNrKQVkOeLsVGxMhxTpcXxxsI&cce=2&category=acrcp_v1_71&sig=AOD64_1pYThYH63P70uUX2Hl-giQvC8grA&q&nis=4&adurl&ved=2ahUKEwju5eG-vIuQAxVicGwGHdOFAR4Q0Qx6BAgWEAE




## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd luna_ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY="your_api_key"
   GOOGLE_API_KEY="your_api_key"
   GEMINI_API_KEY="your_api_key"
   MY_EMAIL="your_email"
   MY_APP_NAME="your_app_name"
   MY_APP_PASSWORD="your_app_password"
   ```

## Usage

Start the application by running:

```bash
python final_main.py
```

- **Chat Interface**: Type messages directly or use the Voice button to speak to the assistant.
- **Settings**: Use the Settings tab to switch your active model provider and configure Ollama models.
































