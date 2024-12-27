import streamlit as st
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.storage.blob import BlobServiceClient
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AZURE_CONFIG = {
    "text_analytics_endpoint": "https://chatbot-text-analytics.cognitiveservices.azure.com/",
    "text_analytics_key": "Cwlsk9LEFP9eIl7EkJBcEi0L4bJRAPY0InQ34CAElXXD2hA4wdllJQQJ99ALACYeBjFXJ3w3AAAaACOGOgGY",
    "storage_account_name": "chatbotdatalogs",
    "storage_account_key": "kH9HGKArSLmQA0+iqPE2Nddi5cevUMhjFIKM/xwIBVcte4z24SBHA3Br5HvtIDkSIikrh0WqoSUc+ASt/sM6zA==",
    "language_endpoint": "https://chatbot-text-analytics.cognitiveservices.azure.com/",
    "language_key": "Cwlsk9LEFP9eIl7EkJBcEi0L4bJRAPY0InQ34CAElXXD2hA4wdllJQQJ99ALACYeBjFXJ3w3AAAaACOGOgGY",
    "speech_key": "IekvvmckTA3x0lpDaynoLpViaxqkxZGaTFgu0XIVer7Jrm2eU0HdJQQJ99ALACYeBjFXJ3w3AAAYACOGrh7A",
    "speech_region": "East US"
}

class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)

class RoleConfig(BaseModel):
    allowed_topics: List[str]
    help_url: str
    color: str

class TrainingResponse(BaseModel):
    keywords: List[str]
    response: str
    documentation_links: Optional[List[str]] = None

class RoleTrainingQuestion(BaseModel):
    keywords: List[str]
    response: str

class AzureServices:
    def __init__(self, config: dict):
        self.config = config
        self.text_analytics_client = TextAnalyticsClient(
            endpoint=config["text_analytics_endpoint"],
            credential=AzureKeyCredential(config["text_analytics_key"])
        )
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{config['storage_account_name']}.blob.core.windows.net",
            credential=config["storage_account_key"]
        )
        self.speech_config = speechsdk.SpeechConfig(
            subscription=config["speech_key"],
            region=config["speech_region"]
        )

    def analyze_sentiment(self, text: str) -> float:
        try:
            result = self.text_analytics_client.analyze_sentiment([text])[0]
            return result.confidence_scores.positive
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.5

    def extract_key_phrases(self, text: str) -> List[str]:
        try:
            result = self.text_analytics_client.extract_key_phrases([text])[0]
            return result if result.is_error else []
        except Exception as e:
            logger.error(f"Error extracting key phrases: {e}")
            return []

    def log_conversation(self, conversation_id: str, messages: List[Dict]):
        try:
            container_client = self.blob_service_client.get_container_client("conversations")
            blob_client = container_client.get_blob_client(f"{conversation_id}.json")
            blob_client.upload_blob(str(messages), overwrite=True)
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")

    def text_to_speech(self, text: str) -> bytes:
        try:
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = speech_synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            return None
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return None

NUMBER_OF_MESSAGES_TO_DISPLAY = 20
ROLE_CONFIGS: Dict[str, RoleConfig] = {
    "IT": RoleConfig(
        allowed_topics=["technical", "security", "infrastructure", "development"],
        help_url="https://learn.microsoft.com/en-us/training/roles/developer",
        color="#007ACC",
    ),
    "Sales": RoleConfig(
        allowed_topics=["sales", "customers", "products", "pricing"],
        help_url="https://learn.microsoft.com/en-us/training/roles/business-user",
        color="#00A36C",
    ),
    "HR": RoleConfig(
        allowed_topics=["employee management", "onboarding", "training", "policies"],
        help_url="https://learn.microsoft.com/en-us/training/roles/hr",
        color="#E74C3C",
    ),
    "Marketing": RoleConfig(
        allowed_topics=["campaigns", "analytics", "content", "social media"],
        help_url="https://learn.microsoft.com/en-us/training/roles/marketing",
        color="#9B59B6",
    ),
    "Finance": RoleConfig(
        allowed_topics=["reporting", "budgeting", "forecasting", "compliance"],
        help_url="https://learn.microsoft.com/en-us/training/roles/finance",
        color="#2ECC71",
    ),
    "Customer Support": RoleConfig(
        allowed_topics=["tickets", "customer service", "knowledge base", "support"],
        help_url="https://learn.microsoft.com/en-us/training/roles/support",
        color="#F1C40F",
    )
}

class RoleTrainingData:
    def __init__(self):
        self.training_data = {
            "IT": {
                "questions": {
                    "azure_active_directory": {
                        "keywords": ["azure ad", "active directory", "directory setup"],
                        "response": """Here's your Azure AD setup guidance:

Technical Steps:
1. Access Azure Portal Configuration
   - Navigate to portal.azure.com
   - Select Azure Active Directory
   - Configure initial directory

2. Security Implementation
   - Set up Multi-Factor Authentication
   - Configure Conditional Access policies
   - Implement Identity Protection

3. User Management
   - Create user accounts
   - Set up groups and roles
   - Configure self-service options

4. Integration Setup
   - Connect with on-premises directory
   - Configure SSO for applications
   - Set up hybrid identity

For detailed implementation steps, refer to our documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/",
                            "https://learn.microsoft.com/en-us/azure/active-directory/hybrid/",
                            "https://learn.microsoft.com/en-us/azure/active-directory/authentication/"
                        ]
                    },
                    "cloud_service_models": {
                        "keywords": ["cloud service models", "iaas", "paas", "saas"],
                        "response": """Here's an overview of Microsoft-based Cloud Service Models:

1. **Infrastructure as a Service (IaaS)**:
   - Provides virtualized computing resources over the internet.
   - Example: Azure Virtual Machines.

2. **Platform as a Service (PaaS)**:
   - Supplies hardware and software tools for application development.
   - Example: Azure App Service.

3. **Software as a Service (SaaS)**:
   - Offers software applications accessible over the internet.
   - Example: Microsoft 365.

For more information, refer to our documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/",
                            "https://learn.microsoft.com/en-us/azure/virtual-machines/",
                            "https://learn.microsoft.com/en-us/microsoft-365/overview/"
                        ]
                    },
                    "network_security_basics": {
                        "keywords": ["network security", "firewall setup", "vpn configuration"],
                        "response": """Here are Microsoft-based network security basics:

1. **Firewall Configuration**:
   - Use Azure Firewall to create and manage robust network access control.
   - Regularly update Azure Firewall rules.

2. **VPN Configuration**:
   - Configure Azure VPN Gateway for secure remote access.
   - Enable multi-factor authentication (MFA) for enhanced security.

3. **Network Monitoring**:
   - Use Azure Monitor and Network Watcher to detect and resolve threats.
   - Analyze logs and alerts for suspicious activity.

Enhance your network security with Azure solutions.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/firewall/",
                            "https://learn.microsoft.com/en-us/azure/vpn-gateway/",
                            "https://learn.microsoft.com/en-us/azure/network-watcher/"
                        ]
                    },
                     "azure_virtual_networks": {
                        "keywords": ["azure vnet", "virtual network", "network setup"],
                        "response": """Here’s how to set up Azure Virtual Networks:

1. **VNet Configuration**:
   - Create a Virtual Network (VNet) in the Azure Portal.
   - Define address spaces and subnets as per your requirements.

2. **Network Security**:
   - Configure Network Security Groups (NSGs) to control inbound and outbound traffic.
   - Implement Azure Firewall for enhanced security.

3. **Integration**:
   - Connect VNets using VNet Peering.
   - Enable VPN Gateway for secure connections to on-premises networks.

For detailed guidance, refer to Azure Virtual Network documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/virtual-network/",
                            "https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview",
                            "https://learn.microsoft.com/en-us/azure/vpn-gateway/"
                        ]
                    },
                    "azure_monitoring_and_logging": {
                        "keywords": ["azure monitor", "log analytics", "monitoring setup"],
                        "response": """Here’s how to implement monitoring and logging in Azure:

1. **Azure Monitor Setup**:
   - Enable Azure Monitor to track metrics and logs across resources.
   - Use Application Insights for monitoring application performance.

2. **Log Analytics**:
   - Configure Log Analytics workspaces for centralized logging.
   - Use Kusto Query Language (KQL) to analyze logs.

3. **Alerting**:
   - Set up alerts for critical metrics and thresholds.
   - Integrate with Azure Action Groups for automated notifications.

For more details, refer to Azure Monitor documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/azure-monitor/",
                            "https://learn.microsoft.com/en-us/azure/azure-monitor/logs/",
                            "https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/"
                        ]
                    },
                    "azure_kubernetes_service": {
                        "keywords": ["aks", "kubernetes", "container orchestration"],
                        "response": """Here’s how to use Azure Kubernetes Service (AKS):

1. **Cluster Setup**:
   - Create an AKS cluster in the Azure Portal.
   - Deploy containerized applications using Kubernetes manifests.

2. **Scaling and Upgrades**:
   - Enable auto-scaling for pods and nodes.
   - Perform rolling updates for seamless upgrades.

3. **Security and Networking**:
   - Use Azure Policy for Kubernetes for governance.
   - Integrate with Azure Container Registry for secure image storage.

For more information, refer to AKS documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/aks/",
                            "https://learn.microsoft.com/en-us/azure/aks/tutorial-kubernetes-deploy-cluster",
                            "https://learn.microsoft.com/en-us/azure/aks/scale-cluster"
                        ]
                    },
                    "azure_backup_and_recovery": {
                        "keywords": ["azure backup", "disaster recovery", "data protection"],
                        "response": """Here’s how to use Azure Backup and Recovery services:

1. **Backup Configuration**:
   - Set up Azure Backup for VMs, databases, and file shares.
   - Schedule periodic backups for automatic protection.

2. **Disaster Recovery**:
   - Use Azure Site Recovery to replicate workloads to a secondary region.
   - Test failover scenarios without impacting production.

3. **Monitoring**:
   - Use Recovery Services vault to monitor backup health.
   - Configure alerts for failed or missed backups.

For more details, refer to Azure Backup documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/backup/",
                            "https://learn.microsoft.com/en-us/azure/site-recovery/",
                            "https://learn.microsoft.com/en-us/azure/backup/backup-azure-vms/"
                        ]
                    },
                    "azure_api_management": {
                        "keywords": ["azure api", "api management", "api gateway"],
                        "response": """Here’s your guide to Azure API Management:

1. **API Gateway Setup**:
   - Publish APIs securely using Azure API Management service.
   - Apply policies like rate-limiting and IP filtering.

2. **Monitoring and Analytics**:
   - Monitor API performance using Azure Monitor.
   - Use API diagnostics for error and latency analysis.

3. **Developer Portal**:
   - Set up a developer portal for API documentation and testing.
   - Enable subscription-based access for external developers.

For detailed steps, refer to Azure API Management documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/api-management/",
                            "https://learn.microsoft.com/en-us/azure/api-management/api-management-howto-policies",
                            "https://learn.microsoft.com/en-us/azure/api-management/api-management-howto-developer-portal"
                        ]
                    },
                    "azure_virtual_machines": {
                        "keywords": ["azure vms", "virtual machines", "cloud computing"],
                        "response": """Here's your guide to Azure Virtual Machines:

1. **VM Deployment**:
   - Navigate to Azure Portal.
   - Choose your desired OS (Windows/Linux) and VM size.
   - Deploy using the pre-configured template or custom configuration.

2. **Security Configuration**:
   - Implement Network Security Groups (NSGs).
   - Enable Azure Defender for servers.
   - Set up Just-in-Time (JIT) access for VMs.

3. **Performance Optimization**:
   - Monitor VM performance using Azure Monitor.
   - Scale resources dynamically with Azure Auto-Scale.

For more detailed steps, refer to Azure Virtual Machines documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/virtual-machines/",
                            "https://learn.microsoft.com/en-us/azure/virtual-machines/windows/",
                            "https://learn.microsoft.com/en-us/azure/virtual-machines/linux/"
                        ]
                    },
                    "azure_devops": {
                        "keywords": ["azure devops", "ci/cd", "pipelines"],
                        "response": """Here’s your guide to Azure DevOps:

1. **Setting Up Pipelines**:
   - Use YAML templates for CI/CD pipelines.
   - Integrate with GitHub or Azure Repos for version control.

2. **Artifact Management**:
   - Store and manage build artifacts in Azure Artifacts.
   - Share packages across teams securely.

3. **Monitoring and Collaboration**:
   - Use Azure Boards for project tracking and management.
   - Integrate with Azure Monitor for pipeline performance insights.

For detailed steps, refer to Azure DevOps documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/devops/",
                            "https://learn.microsoft.com/en-us/azure/devops/pipelines/",
                            "https://learn.microsoft.com/en-us/azure/devops/artifacts/"
                        ]
                    },
                    "azure_storage": {
                        "keywords": ["azure storage", "blob storage", "data storage"],
                        "response": """Here’s your guide to Azure Storage:

1. **Storage Account Setup**:
   - Create a storage account in Azure Portal.
   - Choose from Blob, Table, Queue, or File Storage options.

2. **Data Security**:
   - Implement role-based access control (RBAC).
   - Enable encryption for data at rest and in transit.

3. **Scalability**:
   - Use Hot, Cool, or Archive tiers based on your data access frequency.
   - Enable Azure CDN for faster delivery.

For more information, refer to Azure Storage documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/storage/",
                            "https://learn.microsoft.com/en-us/azure/storage/blobs/",
                            "https://learn.microsoft.com/en-us/azure/storage/files/"
                        ]
                    },
                    "azure_functions": {
                        "keywords": ["azure functions", "serverless computing", "event-driven"],
                        "response": """Here’s how to use Azure Functions for serverless computing:

1. **Create a Function App**:
   - Choose your preferred programming language (C#, Java, Python, etc.).
   - Deploy via Azure Portal, VS Code, or CLI.

2. **Event-Driven Execution**:
   - Trigger functions using HTTP, Timer, or Event Grid.
   - Integrate with Azure services like Cosmos DB or Service Bus.

3. **Scaling**:
   - Azure Functions auto-scales based on the number of incoming requests.
   - Optimize execution with Durable Functions for stateful workflows.

For more details, refer to Azure Functions documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/azure-functions/",
                            "https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview",
                            "https://learn.microsoft.com/en-us/azure/azure-functions/durable-functions-overview"
                        ]
                    },
                    "azure_cosmos_db": {
                        "keywords": ["azure cosmos db", "nosql database", "global distribution"],
                        "response": """Here’s how to use Azure Cosmos DB:

1. **Global Distribution**:
   - Enable multi-region replication for high availability.
   - Choose consistency levels (Strong, Bounded Staleness, etc.) based on your needs.

2. **Data Models**:
   - Support for multiple APIs like SQL, MongoDB, Cassandra, Gremlin, and Table.
   - Choose the model best suited for your application (key-value, graph, etc.).

3. **Performance Tuning**:
   - Optimize RU (Request Units) for cost and performance.
   - Monitor with Azure Monitor and Application Insights.

For more information, refer to Azure Cosmos DB documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/azure/cosmos-db/",
                            "https://learn.microsoft.com/en-us/azure/cosmos-db/sql/",
                            "https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/"
                        ]
                    },
                }
            },
            "Sales": {
                "questions": {
                    "dynamics_365_sales": {
                        "keywords": ["dynamics 365", "crm", "customer relationship management"],
                        "response": """Here’s an overview of Microsoft Dynamics 365 Sales:

1. **Customer Relationship Management (CRM)**:
   - Manage customer data, sales processes, and lead tracking.
   - Use built-in AI insights to identify opportunities and trends.

2. **Sales Productivity**:
   - Automate repetitive tasks with Power Automate.
   - Integrate with Microsoft Teams for seamless collaboration.

3. **Analytics and Insights**:
   - Use Power BI dashboards to analyze sales performance.
   - Get predictive insights for better decision-making.

Explore Microsoft Dynamics 365 Sales for a comprehensive CRM solution.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales/",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-overview",
                            "https://learn.microsoft.com/en-us/power-bi/"
                        ]
                    },
                    "sales_forecasting": {
                        "keywords": ["sales forecasting", "dynamics 365 sales", "power bi"],
                        "response": """Here’s how to implement sales forecasting with Microsoft tools:

1. **Dynamics 365 Sales**:
   - Use AI-driven predictive analytics to create accurate forecasts.
   - Monitor sales pipelines and opportunities to refine projections.

2. **Power BI Integration**:
   - Build interactive reports to visualize forecast data.
   - Analyze historical sales trends to predict future outcomes.

3. **Collaboration**:
   - Share forecasts across teams via Microsoft Teams.
   - Get insights through Power Automate and improve planning.

Utilize Microsoft solutions for advanced sales forecasting.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/create-sales-forecast",
                            "https://learn.microsoft.com/en-us/power-bi/",
                            "https://learn.microsoft.com/en-us/microsoftteams/"
                        ]
                    },
                    "customer_engagement": {
                        "keywords": ["customer engagement", "dynamics 365 marketing", "personalized marketing"],
                        "response": """Boost customer engagement with Microsoft Dynamics 365 Marketing:

1. **Personalized Marketing Campaigns**:
   - Use AI-powered tools to design targeted campaigns.
   - Track customer journeys and deliver relevant content.

2. **Integration**:
   - Sync data with Dynamics 365 Sales for unified engagement.
   - Use Power BI for in-depth customer insights.

3. **Automation**:
   - Automate email marketing, event management, and social media campaigns.
   - Enhance customer interactions with intelligent chatbots.

Enhance your customer engagement with Dynamics 365 solutions.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/",
                            "https://learn.microsoft.com/en-us/power-bi/",
                            "https://learn.microsoft.com/en-us/dynamics365/sales/"
                        ]
                    },
                    "sales_pipeline_management": {
                        "keywords": ["sales pipeline", "dynamics 365 sales", "opportunity tracking"],
                        "response": """Effectively manage your sales pipeline using Dynamics 365 Sales:

1. **Pipeline Visualization**:
   - Track and visualize sales opportunities at every stage.
   - Use AI-driven insights to identify the best opportunities to focus on.

2. **Customizable Sales Stages**:
   - Customize sales stages to fit your business needs.
   - Automate transitions between stages for better pipeline management.

3. **Collaboration Tools**:
   - Collaborate with team members using Microsoft Teams for updates and information sharing.

Boost your sales pipeline management with Dynamics 365 Sales for better forecasting and tracking.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-pipeline",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/opportunity-management"
                        ]
                    },
                    "lead_management": {
                        "keywords": ["lead management", "dynamics 365 sales", "lead generation"],
                        "response": """Optimize lead management with Microsoft Dynamics 365 Sales:

1. **Lead Scoring**:
   - Use AI-powered scoring models to prioritize high-value leads.
   - Automatically assign leads to the right sales representative.

2. **Lead Nurturing**:
   - Automate email sequences to nurture leads.
   - Use Dynamics 365 Marketing to engage leads across multiple channels.

3. **Tracking and Reporting**:
   - Track lead activity and progress with built-in reporting tools.
   - Get real-time insights into lead performance and conversion.

Enhance your lead management with Dynamics 365 for improved lead generation and nurturing.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/lead-management",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/lead-scoring"
                        ]
                    },
                    "sales_team_collaboration": {
                        "keywords": ["sales team", "microsoft teams", "collaboration"],
                        "response": """Improve sales team collaboration using Microsoft tools:

1. **Microsoft Teams**:
   - Use Teams for chat, meetings, and document sharing across your sales team.
   - Collaborate on proposals, reports, and presentations in real-time.

2. **Shared Insights**:
   - Share insights from Dynamics 365 Sales directly in Teams channels.
   - Use AI to surface the most relevant data and insights for your team.

3. **Task Management**:
   - Use Microsoft Planner and To-Do to manage tasks and track team progress.
   - Integrate tasks with Dynamics 365 Sales for seamless management.

Enhance team collaboration and productivity using Microsoft Teams and Dynamics 365 Sales.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/microsoftteams/",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/team-collaboration"
                        ]
                    },
                    "sales_performance_analysis": {
                        "keywords": ["sales performance", "dynamics 365", "power bi"],
                        "response": """Track and analyze sales performance with Dynamics 365 Sales and Power BI:

1. **Performance Dashboards**:
   - Use Power BI to create interactive dashboards for real-time sales data.
   - Track KPIs, revenue, and pipeline performance at a glance.

2. **Sales Trend Analysis**:
   - Leverage historical data to analyze trends and predict future performance.
   - Use AI to spot growth opportunities and underperforming areas.

3. **Custom Reports**:
   - Create custom sales reports based on key metrics and trends.
   - Share performance insights across the organization for better decision-making.

Enhance your sales performance analysis using Microsoft tools.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-performance",
                            "https://learn.microsoft.com/en-us/power-bi/"
                        ]
                    },
                    "account_management": {
                        "keywords": ["account management", "dynamics 365 sales", "account segmentation"],
                        "response": """Manage customer accounts effectively with Dynamics 365 Sales:

1. **Account Segmentation**:
   - Use Dynamics 365 to categorize and segment customer accounts.
   - Apply AI-based recommendations for targeted account management strategies.

2. **Customer Insights**:
   - Leverage customer data to gain valuable insights on purchasing behavior.
   - Build detailed customer profiles to improve relationship-building efforts.

3. **Customer Retention**:
   - Implement strategies for improving customer satisfaction and loyalty.
   - Use automation to stay engaged with customers, ensuring long-term success.

Optimize your account management strategies with Dynamics 365 Sales.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/account-management",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/relationship-management"
                        ]
                    },
                    "crm_pipeline_management": {
                        "keywords": ["crm pipeline", "sales funnel", "pipeline stages"],
                        "response": """Here’s how to manage your CRM sales pipeline effectively:

1. **Pipeline Setup**:
   - Define stages in your sales funnel (e.g., Lead, Contacted, Qualified, Proposal Sent, Won/Lost).
   - Configure CRM to track deals through each stage.

2. **Monitoring Progress**:
   - Use dashboards to monitor deal progress and identify bottlenecks.
   - Generate reports for win rates and deal velocity.

3. **Optimization**:
   - Regularly update stages and remove stagnant deals.
   - Analyze historical data to improve pipeline efficiency.

For more guidance, refer to our CRM pipeline management documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-pipeline",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/reports-dashboards"
                        ]
                    },
                    "sales_forecasting": {
                        "keywords": ["sales forecast", "predict revenue", "forecasting accuracy"],
                        "response": """Here’s how to improve sales forecasting:

1. **Data Preparation**:
   - Use CRM data, historical sales, and market trends.
   - Include factors like seasonality and lead quality.

2. **Forecasting Models**:
   - Implement AI-driven forecasting tools in CRM.
   - Categorize forecasts by regions, products, or teams.

3. **Collaboration**:
   - Align with marketing and operations teams to validate forecasts.
   - Regularly update forecasts based on new data.

For more information, refer to our sales forecasting documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-forecast",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/forecast-modeling"
                        ]
                    },
                    "lead_scoring_and_prioritization": {
                        "keywords": ["lead scoring", "prioritize leads", "lead qualification"],
                        "response": """Here’s how to effectively score and prioritize leads:

1. **Scoring Setup**:
   - Use CRM tools to assign scores based on attributes like industry, engagement level, and budget.
   - Categorize leads into Hot, Warm, and Cold categories.

2. **Automation**:
   - Automate lead scoring using AI to dynamically adjust scores.
   - Set alerts for high-potential leads.

3. **Conversion Strategy**:
   - Focus on high-scoring leads with personalized outreach.
   - Regularly review and refine lead scoring criteria.

For more guidance, refer to lead management documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/lead-scoring",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/lead-management"
                        ]
                    },
                    "account_based_marketing": {
                        "keywords": ["abm", "account marketing", "target accounts"],
                        "response": """Here’s how to implement Account-Based Marketing (ABM):

1. **Account Identification**:
   - Identify high-value accounts using CRM and analytics.
   - Develop a list of target accounts and key decision-makers.

2. **Personalized Campaigns**:
   - Tailor marketing efforts for specific accounts.
   - Use tools like Dynamics 365 Marketing to design targeted campaigns.

3. **Alignment with Sales**:
   - Ensure close collaboration between sales and marketing teams.
   - Share account insights and activity logs.

For detailed steps, refer to our ABM implementation documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/account-based-marketing",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/target-accounts"
                        ]
                    },
                    "sales_analytics_and_insights": {
                        "keywords": ["sales analytics", "performance insights", "data-driven sales"],
                        "response": """Here’s how to leverage analytics for better sales performance:

1. **Data Collection**:
   - Integrate CRM with analytics tools to collect sales data.
   - Use Power BI for advanced visualizations.

2. **Performance Tracking**:
   - Monitor KPIs like conversion rates, revenue per rep, and sales cycle length.
   - Use dashboards to identify trends and areas of improvement.

3. **Insights to Action**:
   - Use insights to refine sales strategies.
   - Implement data-driven decisions for pricing, targeting, and resource allocation.

For detailed guidance, refer to our sales analytics documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/power-bi/guided-learning/",
                            "https://learn.microsoft.com/en-us/dynamics365/sales-enterprise/sales-analytics"
                        ]
                    },
                    "customer_retention_strategies": {
                        "keywords": ["customer retention", "renewal", "customer loyalty"],
                        "response": """Here’s how to improve customer retention:

1. **Customer Engagement**:
   - Use CRM to schedule regular follow-ups and check-ins.
   - Offer personalized support and solutions based on past interactions.

2. **Loyalty Programs**:
   - Implement rewards programs to incentivize repeat business.
   - Use Dynamics 365 for marketing campaigns targeting existing customers.

3. **Feedback and Improvement**:
   - Collect customer feedback through surveys.
   - Use insights to address pain points and enhance the customer experience.

For more details, refer to our customer retention documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/customer-retention"
                        ]
                    },  
                }
            },
            "HR": {
                "questions": {
                    "employee_onboarding": {
                        "keywords": ["employee onboarding"],
                        "response": """Here's your HR onboarding guidance:

Onboarding Process:
1. Pre-arrival
   - Document preparation
   - System access setup
   - Team notification

2. First Day
   - Welcome package
   - IT setup
   - Initial meetings

3. First Week
   - Training schedule
   - Policy review
   - Team introduction

4. First Month
   - Performance expectations
   - Regular check-ins
   - Goal setting

Refer to our HR documentation for detailed processes.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/viva/topics/",
                            "https://learn.microsoft.com/en-us/microsoft-365/admin/",
                            "https://learn.microsoft.com/en-us/viva/learning/"
                        ]
                    },
                    "employee_training": {
                        "keywords": ["employee training"],
                        "response": """Here's a guide for employee training with Microsoft Viva:

1. Set up training modules in Viva Learning.
2. Assign learning paths to employees.
3. Track progress and provide feedback.

Refer to the Microsoft Viva Learning documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/viva/learning/",
                            "https://learn.microsoft.com/en-us/microsoft-365/admin/"
                        ]
                    },
                    "team_collaboration": {
                        "keywords": ["team collaboration"],
                        "response": """For better team collaboration with Microsoft Teams:

1. Create channels for different projects.
2. Use Teams for real-time chats and meetings.
3. Share documents using Teams integration with SharePoint.

Refer to the Microsoft Teams guide for more information.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/microsoftteams/",
                            "https://learn.microsoft.com/en-us/sharepoint/"
                        ]
                    },
                    "performance_review": {
                        "keywords": ["performance review"],
                        "response": """Here’s how to manage performance reviews with Microsoft Viva Insights:

1. Set up regular feedback requests.
2. Use Insights for continuous performance tracking.
3. Create reports for performance reviews.

Check out Microsoft Viva Insights for further details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/viva/insights/",
                            "https://learn.microsoft.com/en-us/microsoft-365/admin/"
                        ]
                    },
                    "employee_feedback": {
                        "keywords": ["employee feedback"],
                        "response": """To gather feedback using Microsoft Forms:

1. Create custom surveys or feedback forms.
2. Distribute forms via email or Teams.
3. Analyze responses with automatic insights.

Refer to Microsoft Forms documentation for more details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/microsoft-forms/",
                            "https://learn.microsoft.com/en-us/microsoft-365/admin/"
                        ]
                    },
                    "workplace_wellbeing": {
                        "keywords": ["workplace wellbeing"],
                        "response": """Support employee wellbeing with Microsoft Viva:

1. Monitor wellbeing through personalized insights.
2. Offer wellbeing resources via Viva Connections.
3. Encourage work-life balance with Viva Insights.

Refer to the Microsoft Viva Wellbeing documentation for guidance.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/viva/wellbeing/",
                            "https://learn.microsoft.com/en-us/microsoft-365/admin/"
                        ]
                    },
                    "performance_management": {
                        "keywords": ["performance management"],
                        "response": """Manage employee performance effectively:

1. Set performance goals and KPIs.
2. Conduct regular performance reviews.
3. Use analytics for tracking progress and feedback.

Refer to Dynamics 365 Human Resources documentation for more details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/",
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/performance-management/"
                        ]
                    },
                    "employee_data": {
                        "keywords": ["employee data"],
                        "response": """Manage employee data securely:

1. Configure access controls and permissions.
2. Ensure compliance with GDPR and other regulations.
3. Use role-based security for data management.

Explore Dynamics 365 Human Resources for data management features.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/employee-data-management/",
                            "https://learn.microsoft.com/en-us/microsoft-365/compliance/"
                        ]
                    },
                    "leave_management": {
                        "keywords": ["leave management"],
                        "response": """Manage employee leave efficiently:

1. Configure leave policies and types.
2. Enable self-service leave requests.
3. Track leave balances and approvals.

Refer to Dynamics 365 Human Resources for leave management setup.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/leave-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/"
                        ]
                    },
                    "recruitment": {
                        "keywords": ["recruitment"],
                        "response": """Streamline recruitment processes:

1. Post job openings and manage applications.
2. Schedule interviews and track progress.
3. Use analytics for talent acquisition insights.

Learn more about recruitment in Dynamics 365 Human Resources.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/talent/",
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/"
                        ]
                    },
                    "training_programs": {
                        "keywords": ["training programs"],
                        "response": """Enhance training management:

1. Create and assign learning paths.
2. Track training completion and effectiveness.
3. Integrate with employee performance goals.

Explore Microsoft Viva Learning for training program management.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/viva/learning/",
                            "https://learn.microsoft.com/en-us/dynamics365/human-resources/"
                        ]
                    },
                }
            },
            "Marketing": {
                "questions": {
                    "social_media_analytics": {
                        "keywords": ["social media analytics", "Microsoft tools"],
                        "response": """Here’s how to track social media performance:

1. Monitor engagement metrics using Microsoft Dynamics 365 Marketing.
2. Track ad performance with Microsoft Advertising.
3. Integrate social listening tools for real-time insights.

Check out Microsoft tools for social media tracking.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/",
                            "https://learn.microsoft.com/en-us/advertising/"
                        ]
                    },
                    "customer_insights": {
                        "keywords": ["customer insights"],
                        "response": """Gain insights using Dynamics 365:

1. Collect customer data from multiple touchpoints.
2. Segment customers using AI-driven analytics.
3. Use Dynamics 365 to build personalized campaigns.

Learn more about customer insights with Microsoft Dynamics.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-insights/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                    "email_marketing": {
                        "keywords": ["email marketing"],
                        "response": """Enhance email marketing with Microsoft tools:

1. Use Dynamics 365 Marketing for targeted email campaigns.
2. Automate email workflows using Power Automate.
3. Track email performance with Power BI.

Refer to Microsoft resources for email marketing strategies.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/",
                            "https://learn.microsoft.com/en-us/power-automate/"
                        ]
                    },
                    "campaign_automation": {
                        "keywords": ["campaign automation"],
                        "response": """Automate campaigns using Dynamics 365:

1. Set up workflows and triggers for lead nurturing.
2. Automate follow-ups and email sequences.
3. Leverage AI to optimize campaign performance.

Explore Microsoft Dynamics for campaign automation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-insights/"
                        ]
                    },
                    "ad_performance": {
                        "keywords": ["ad performance"],
                        "response": """Measure ad performance using Microsoft Advertising:

1. Track impressions, clicks, and conversions.
2. Use automated bidding strategies for optimization.
3. Generate custom reports for campaign performance analysis.

Find more on Microsoft Advertising analytics.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/advertising/"
                        ]
                    },
                    "content_management": {
                        "keywords": ["content management"],
                        "response": """Streamline content management:

1. Create a centralized content library.
2. Collaborate on asset creation and updates.
3. Track content usage and performance.

Refer to the Dynamics 365 Marketing documentation for more details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/content-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                    "campaign_budgeting": {
                        "keywords": ["campaign budgeting", "campaign budgets"],
                        "response": """Manage campaign budgets effectively:

1. Set budget limits for campaigns.
2. Monitor spending in real-time.
3. Analyze ROI to optimize future campaigns.

Explore Dynamics 365 Marketing for budgeting features.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/campaign-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                    "personalization": {
                        "keywords": ["personalization","personalize marketing efforts"],
                        "response": """Achieve effective personalization:

1. Segment audiences using demographics and behaviors.
2. Deliver tailored messages and offers.
3. Use AI-driven insights for customer preferences.

Refer to Dynamics 365 Marketing for personalization features.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/personalization/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                    "cross_channel_marketing": {
                        "keywords": ["cross channel", "campaigns"],
                        "response": """Run seamless cross-channel campaigns:

1. Integrate email, SMS, social media, and web.
2. Monitor performance across all channels.
3. Optimize campaigns with unified insights.

Learn more in the Dynamics 365 Marketing documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/cross-channel/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                    "audience_targeting": {
                        "keywords": ["audience targeting"],
                        "response": """Enhance audience targeting:

1. Use advanced segmentation tools.
2. Leverage AI for predictive targeting.
3. Align messaging with specific audience needs.

Check the Dynamics 365 Marketing documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/audience-segmentation/",
                            "https://learn.microsoft.com/en-us/dynamics365/marketing/"
                        ]
                    },
                }
            },
            "Finance": {
                "questions": {
                    "budgeting": {
                        "keywords": ["budgeting"],
                        "response": """Here's how to set up budgeting:

1. Define budget plans and categories.
2. Set up fiscal periods and budget control.
3. Monitor budget performance with real-time reporting.

Refer to Microsoft Dynamics 365 Finance for budget setup details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/budgeting/"
                        ]
                    },
                    "cash_flow_management": {
                        "keywords": ["cash flow management"],
                        "response": """Manage cash flow efficiently with Dynamics 365:

1. Set up cash flow forecasts.
2. Track receivables and payables.
3. Use real-time analytics to monitor cash positions.

Find out more about cash flow management in Dynamics 365 Finance.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/cash-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "tax_compliance": {
                        "keywords": ["tax compliance"],
                        "response": """Ensure tax compliance with Dynamics 365:

1. Set up tax groups and authorities.
2. Configure tax reporting and filings.
3. Integrate with global tax regulations.

For tax management, refer to Dynamics 365 Finance documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/tax/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "financial_planning": {
                        "keywords": ["financial planning"],
                        "response": """Here’s how to set up financial planning:

1. Define financial objectives and goals.
2. Configure financial forecasts and planning models.
3. Monitor and adjust plans with scenario analysis.

Check out Dynamics 365 Finance for detailed planning setup.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/planning/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "financial_analysis": {
                        "keywords": ["financial analysis"],
                        "response": """Perform financial analysis with Dynamics 365:

1. Use financial reports and KPIs.
2. Analyze data trends with Power BI integration.
3. Leverage AI-powered insights for strategic decisions.

For financial analysis, explore Microsoft Dynamics 365 Finance documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/financial-analysis/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "expense_management": {
                        "keywords": ["expense management"],
                        "response": """Manage employee expenses effectively:

1. Streamline expense submission and approval workflows.
2. Automate reimbursement processes.
3. Integrate expenses with financial reporting.

Refer to the Dynamics 365 Finance documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/expense-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "cash_flow_analysis": {
                        "keywords": ["cash flow analysis"],
                        "response": """Perform detailed cash flow analysis:

1. Monitor cash inflows and outflows in real-time.
2. Generate forecasts for future cash positions.
3. Use visual dashboards for insights.

Check the Dynamics 365 Finance documentation for guidance.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/cash-flow-forecasting/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "budget_planning": {
                        "keywords": ["budget planning"],
                        "response": """Create and manage budgets efficiently:

1. Develop budgets using historical data.
2. Enable collaborative budget planning.
3. Monitor budget adherence with automated alerts.

Explore the Dynamics 365 Finance documentation for more information.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/budgeting/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "project_accounting": {
                        "keywords": ["project accounting"],
                        "response": """Simplify project accounting:

1. Track project costs and revenues.
2. Allocate resources and manage billing.
3. Generate project profitability reports.

Learn more in the Dynamics 365 Finance documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/project-accounting/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                    "tax_management": {
                        "keywords": ["tax management"],
                        "response": """Handle tax management seamlessly:

1. Configure tax rules and rates for different jurisdictions.
2. Automate tax calculations and compliance.
3. Generate detailed tax reports.

Refer to the Dynamics 365 Finance documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/finance/tax-calculation-service/",
                            "https://learn.microsoft.com/en-us/dynamics365/finance/"
                        ]
                    },
                }
            },
            "Customer Support": {
                "questions": {
                    "live_chat_support": {
                        "keywords": ["live chat support"],
                        "response": """Set up live chat support with Dynamics 365:

1. Configure Omnichannel for Customer Service.
2. Set up live chat routing and agent queues.
3. Monitor live chat performance with dashboards.

Explore more about live chat in Dynamics 365 Customer Service documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/omnichannel/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "knowledge_management": {
                        "keywords": ["knowledge management"],
                        "response": """Implement knowledge management effectively:

1. Create knowledge base articles in Dynamics 365.
2. Link articles to tickets for faster resolution.
3. Use AI to suggest relevant articles to agents.

Check Dynamics 365 documentation for knowledge management details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/knowledge-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "customer_feedback": {
                        "keywords": ["customer feedback"],
                        "response": """Collect and manage customer feedback:

1. Create surveys using Dynamics 365 Customer Voice.
2. Integrate feedback with ticketing systems.
3. Use insights to improve service quality.

Learn more about customer feedback in Microsoft Dynamics 365.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-voice/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "service_level_agreements": {
                        "keywords": ["service level agreements"],
                        "response": """Set up SLAs in Dynamics 365:

1. Define SLA KPIs and targets.
2. Configure SLA policies for support tickets.
3. Track SLA performance and breaches.

For more information, refer to Dynamics 365 SLA setup documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/service-level-agreements/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "case_management": {
                        "keywords": ["case management"],
                        "response": """Manage customer cases with Dynamics 365:

1. Create and assign cases to agents.
2. Track case status and resolution.
3. Use workflows to automate case handling.

For case management details, refer to Microsoft Dynamics 365 documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/case-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "self_service_portal": {
                        "keywords": ["self service portal"],
                        "response": """Here's how to set up a self-service portal:

1. Enable the Customer Service portal in Dynamics 365.
2. Add FAQs, knowledge base articles, and troubleshooting guides.
3. Configure case creation and tracking for users.

Refer to the Dynamics 365 documentation for detailed steps.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/self-service/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "chat_support": {
                        "keywords": ["chat support"],
                        "response": """Implement live chat with these steps:

1. Set up Omnichannel for Customer Service.
2. Configure chat widgets on your website or app.
3. Monitor chat sessions and integrate with ticketing systems.

Check the Dynamics 365 Omnichannel documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/omnichannel/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "customer_feedback": {
                        "keywords": ["customer feedback"],
                        "response": """Collect and analyze feedback effectively:

1. Use Dynamics 365 Customer Voice for surveys.
2. Monitor feedback trends and generate actionable insights.
3. Automate follow-up actions based on responses.

Refer to Dynamics 365 Customer Voice documentation for details.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-voice/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "ai_support": {
                        "keywords": ["ai support", "AI"],
                        "response": """Enhance customer support with AI:

1. Implement AI-driven virtual agents.
2. Use sentiment analysis to prioritize cases.
3. Analyze trends with AI-powered insights.

Learn more from the Dynamics 365 AI documentation.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/ai/customer-service-insights/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                    "case_routing": {
                        "keywords": ["case routing"],
                        "response": """Automate case routing with these steps:

1. Set up case queues based on criteria like priority or type.
2. Configure routing rules for automated assignment.
3. Monitor case distribution and workload balance.

Check the Dynamics 365 Customer Service documentation for guidance.""",
                        "documentation_links": [
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/case-management/",
                            "https://learn.microsoft.com/en-us/dynamics365/customer-service/"
                        ]
                    },
                }
            }
        }

    def get_response(self, role: str, message: str) -> Optional[str]:
        if role not in self.training_data:
            return None
            
        message = message.lower()
        for topic, data in self.training_data[role]["questions"].items():
            if any(keyword in message for keyword in data.keywords):
                return data.response
        return None

st.set_page_config(
    page_title="Microsoft Role-Based AI Assistant",
    page_icon="imgs/avatar_assistant.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://github.com/yourusername/your-repo",
        "Report a bug": "https://github.com/yourusername/your-repo/issues",
        "About": """
            ## Microsoft Role-Based AI Assistant
            Powered by Azure Cognitive Services

            This AI Assistant provides role-specific guidance and support
            for various Microsoft technologies and solutions.
        """
    }
)

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

def process_message(azure_services: AzureServices, message: str, role: str) -> str:
    sentiment_score = azure_services.analyze_sentiment(message)
    key_phrases = azure_services.extract_key_phrases(message)
    
    training_data = RoleTrainingData()
    response = training_data.get_response(role, message)
    
    if not response:
        if sentiment_score < 0.4:
            response = f"I understand you might be frustrated. Let me help you with your {role}-related question about {', '.join(key_phrases) if key_phrases else 'your topic'}."
        else:
            response = f"I'll help you with your {role}-related question about {', '.join(key_phrases) if key_phrases else 'your topic'}."
    
    return response

def main():
    azure_services = AzureServices(AZURE_CONFIG)

    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #0078D4,
                0 0 10px #0078D4,
                0 0 15px #0078D4;
            position: relative;
            z-index: -1;
            border-radius: 45px;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
        }
        .chat-message.user {
            background-color: #f0f2f6;
        }
        .chat-message.assistant {
            background-color: #e3f2fd;
        }
        .role-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: 500;
            color: white;
            display: inline-block;
            margin-bottom: 10px;
        }
        .stTextInput {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem;
            border-top: 1px solid #e0e0e0;
            z-index: 100;
        }
        .main-content {
            margin-bottom: 80px;
        }
        .chat-container {
            max-height: calc(100vh - 200px);
            overflow-y: auto;
            padding-bottom: 80px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    initialize_session_state()

    with st.sidebar:
        st.title("🎯 Role Selection")
        selected_role = st.selectbox(
            "Choose your role:",
            list(ROLE_CONFIGS.keys())
        )

        enable_tts = st.toggle("Enable Text-to-Speech", False)

        st.markdown(
            f"""<div class="role-badge" style="background-color: {ROLE_CONFIGS[selected_role].color}">
            {selected_role}</div>""",
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.subheader("📚 Help Center")
        if st.button("Access Role Resources"):
            st.markdown(f"[Role-specific training materials]({ROLE_CONFIGS[selected_role].help_url})")
        st.markdown("**Allowed Topics:**")
        for topic in ROLE_CONFIGS[selected_role].allowed_topics:
            st.markdown(f"- {topic.title()}")

    st.title("Microsoft Role-Based AI Assistant")

    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            welcome_msg = Message(
                role="assistant",
                content=f"Hello! I'm your {selected_role} assistant. How can I help you with {', '.join(ROLE_CONFIGS[selected_role].allowed_topics)}?"
            )
            st.session_state.messages.append(welcome_msg.dict())

        for message in st.session_state.messages[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

                if enable_tts and message["role"] == "assistant":
                    audio_data = azure_services.text_to_speech(message["content"])
                    if audio_data:
                        st.audio(audio_data, format="audio/wav")

    if prompt := st.chat_input("Type your message here...", key="chat_input"):
        user_message = Message(role="user", content=prompt)
        st.session_state.messages.append(user_message.dict())

        response_content = process_message(azure_services, prompt, selected_role)

        assistant_message = Message(role="assistant", content=response_content)
        st.session_state.messages.append(assistant_message.dict())

        azure_services.log_conversation(
            st.session_state.conversation_id,
            st.session_state.messages
        )
        st.rerun()

if __name__ == "__main__":
    main()
