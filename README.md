# Microsoft Role-Based AI Assistant

## Overview
This project implements a Microsoft Role-Based AI Assistant that provides role-specific guidance and support for various Microsoft technologies and solutions. The application leverages Azure Cognitive Services such as Text Analytics, Blob Storage, and Speech Services, integrated into a Streamlit web app.

### Key Features:
- Role-based assistance tailored to IT, HR, Sales, Marketing, and more.
- Sentiment analysis and key phrase extraction using Azure Text Analytics.
- Conversation logging to Azure Blob Storage.
- Text-to-Speech (TTS) integration with Azure Speech Services.
- Dynamic role selection with custom topics and resources.

## Prerequisites
Before running the application, ensure you have the following:
1. Azure Cognitive Services keys for Text Analytics and Speech.
2. Azure Storage Account credentials.
3. Python 3.8+ installed.
4. Dependencies from `requirements.txt` installed.

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/azure-role-assistant.git
cd azure-role-assistant
```
2. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Azure keys:
Create an `.env` file in the root directory and populate it with your Azure credentials:
```
AZURE_TEXT_ANALYTICS_ENDPOINT=<your_endpoint>
AZURE_TEXT_ANALYTICS_KEY=<your_key>
AZURE_STORAGE_ACCOUNT_NAME=<your_storage_account_name>
AZURE_STORAGE_ACCOUNT_KEY=<your_storage_account_key>
AZURE_SPEECH_KEY=<your_speech_key>
AZURE_SPEECH_REGION=<your_speech_region>
```

## Running the Application
1. Start the Streamlit app:
```bash
streamlit run app.py
```
2. Access the application in your browser at `http://localhost:8501`.

## Usage
1. Select your role from the sidebar.
2. Interact with the assistant by typing your queries.
3. Enable Text-to-Speech (optional) to hear the assistant's responses.
4. View role-specific training materials and allowed topics.

## Deployment
To deploy the app, consider using Azure App Service or Docker. Update your environment variables as per the deployment environment.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for enhancements or bug fixes.

---
### requirements.txt ###
streamlit==1.24.1
azure-cognitiveservices-speech==1.22.0
azure-ai-textanalytics==5.2.0
azure-storage-blob==12.14.1
pydantic==1.10.11

### LICENSE ###
MIT License

Copyright (c) 2024 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
