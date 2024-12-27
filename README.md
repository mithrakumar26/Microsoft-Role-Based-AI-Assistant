# Microsoft Role-Based AI Assistant

## 📖 Overview
The Microsoft Role-Based AI Assistant is a dynamic, role-specific assistant designed to enhance productivity and streamline workflows. It leverages Azure Cognitive Services for sentiment analysis, text-to-speech capabilities, and more, providing an interactive interface for users to access tailored guidance based on their professional roles.

## 🌟 Key Features
- **Role-Specific Assistance**: Supports roles like IT, HR, Marketing, Sales, and more.
- **AI-Powered Analytics**: Includes sentiment analysis and key phrase extraction using Azure AI.
- **Text-to-Speech**: Converts AI responses into audio for an engaging user experience.
- **Conversation Logging**: Stores chat histories securely in Azure Blob Storage.
- **User-Friendly UI**: Built with Streamlit for an intuitive, interactive interface.

## 🛠️ Prerequisites
- Python 3.8 or higher.
- An active Azure account with:
  - Azure Cognitive Services (Text Analytics, Speech).
  - Azure Blob Storage configured.
- `pip` package manager for Python.

## ⚙️ Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/role-based-ai-assistant.git
   cd role-based-ai-assistant
   ```
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/Mac
   venv\Scripts\activate     # Windows
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Running the Application
1. Replace placeholders in the `AZURE_CONFIG` section of `app.py` with your Azure keys.
2. Start the application:
   ```bash
   streamlit run app.py
   ```
3. Open your browser and go to `http://localhost:8501` to interact with the AI assistant.

## 📘 Usage
- Select your role from the dropdown menu.
- Type your queries or requests into the chat interface.
- Receive AI-driven responses tailored to your role.
- Use the text-to-speech feature to listen to responses.
- Access stored conversation logs for future reference.

## 🌐 Deployment
To deploy the application:
1. Host the app on a platform like **Azure App Service**, **Heroku**, or **AWS**.
2. Ensure environment variables for Azure credentials are securely set.
3. Configure a reverse proxy like Nginx for production use if needed.

### Deployment with Azure App Service (Example):
1. Install the Azure CLI and log in:
   ```bash
   az login
   ```
2. Deploy the app using the following commands:
   ```bash
   az webapp up --name your-app-name --resource-group your-resource-group --runtime PYTHON:3.9
   ```

## 📂 requirements.txt
```plaintext
azure-cognitiveservices-speech==1.24.0
azure-core==1.29.2
azure-ai-textanalytics==5.2.0
azure-storage-blob==12.15.0
streamlit==1.26.0
pydantic==1.10.9
