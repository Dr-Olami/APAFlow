"""
Mentor agent implementation for SMEFlow.

Mentors provide guidance, recommendations, and educational content
for African SME business growth and best practices.
"""

from typing import Dict, Any, List, Optional, Union
from langchain.agents import AgentType, initialize_agent
from langchain.agents.agent import BaseMultiActionAgent, BaseSingleActionAgent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from .base import BaseAgent, AgentConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


class MentorAgent(BaseAgent):
    """
    Mentor agent for providing business guidance and recommendations.
    
    Designed for African SMEs with focus on:
    - Business strategy and planning
    - Market analysis and insights
    - Financial guidance and planning
    - Regulatory compliance advice
    - Growth recommendations
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLanguageModel,
        tools: Optional[List[BaseTool]] = None,
        prompt: Optional[PromptTemplate] = None
    ):
        """
        Initialize Mentor agent.
        
        Args:
            config: Agent configuration
            llm: Language model instance
            tools: Available tools for mentoring
            prompt: Custom prompt template
        """
        super().__init__(config, llm, tools, prompt)
        
        # Mentor-specific configuration
        self.expertise_areas = self._parse_expertise_areas(config.custom_instructions)
        self.guidance_style = "supportive_and_practical"
        self.knowledge_base = "african_sme_best_practices"
        
        logger.info(
            f"Initialized Mentor agent for tenant {config.tenant_id}",
            extra={
                "agent_id": self.agent_id,
                "tenant_id": config.tenant_id,
                "region": config.region,
                "expertise_areas": self.expertise_areas,
                "guidance_style": self.guidance_style
            }
        )
    
    def _create_agent(self) -> Union[BaseMultiActionAgent, BaseSingleActionAgent]:
        """Create the mentor agent implementation."""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            early_stopping_method=self.config.early_stopping_method,
            handle_parsing_errors=True
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Mentor agents."""
        base_prompt = f"""You are a Mentor agent for SMEFlow, designed to guide and support African SMEs in their business journey.

AGENT IDENTITY:
- Type: Mentor
- Region: {self.config.region}
- Tenant: {self.config.tenant_id}
- Languages: {', '.join(self.config.languages)}
- Expertise Areas: {', '.join(self.expertise_areas)}

CORE CAPABILITIES:
- Provide strategic business guidance and recommendations
- Analyze market opportunities and challenges
- Offer financial planning and management advice
- Guide regulatory compliance and legal requirements
- Support business growth and scaling strategies
- Share industry best practices and case studies

AFRICAN MARKET EXPERTISE:
- Deep understanding of African business ecosystems
- Knowledge of local regulations and compliance requirements
- Awareness of cultural nuances and business practices
- Experience with African financial systems and payment methods
- Understanding of infrastructure challenges and solutions
- Familiarity with government incentives and support programs

MENTORING APPROACH:
1. Listen actively and understand the business context
2. Ask clarifying questions to identify core challenges
3. Provide actionable, practical recommendations
4. Share relevant case studies and success stories
5. Consider local market conditions and constraints
6. Encourage sustainable and ethical business practices
7. Support long-term business growth and resilience

REGIONAL CONTEXT ({self.config.region}):
{self._get_regional_context()}

AVAILABLE TOOLS:
{self._format_tools_description()}

GUIDANCE PRINCIPLES:
- Be supportive, encouraging, and constructive
- Provide specific, actionable advice
- Consider resource constraints of SMEs
- Respect cultural values and business practices
- Focus on sustainable growth strategies
- Emphasize compliance and ethical practices
- Share knowledge generously and clearly

Remember: You're helping African entrepreneurs build successful, sustainable businesses. Be their trusted advisor and champion their success."""

        if self.config.custom_instructions:
            base_prompt += f"\n\nCUSTOM EXPERTISE:\n{self.config.custom_instructions}"
        
        return base_prompt
    
    def _parse_expertise_areas(self, custom_instructions: str) -> List[str]:
        """Parse expertise areas from custom instructions."""
        default_areas = [
            "business_strategy",
            "financial_planning", 
            "market_analysis",
            "regulatory_compliance",
            "growth_planning"
        ]
        
        if not custom_instructions:
            return default_areas
        
        # Look for expertise keywords in custom instructions
        expertise_keywords = {
            "finance": "financial_planning",
            "marketing": "marketing_strategy",
            "operations": "operations_management",
            "technology": "technology_adoption",
            "legal": "regulatory_compliance",
            "strategy": "business_strategy",
            "sales": "sales_optimization",
            "hr": "human_resources",
            "supply": "supply_chain",
            "export": "export_import"
        }
        
        found_areas = []
        instructions_lower = custom_instructions.lower()
        
        for keyword, area in expertise_keywords.items():
            if keyword in instructions_lower:
                found_areas.append(area)
        
        return found_areas if found_areas else default_areas
    
    def _get_regional_context(self) -> str:
        """Get regional business context and insights."""
        regional_contexts = {
            "NG": """
- Largest economy in Africa with diverse sectors
- Strong fintech and digital payment ecosystem
- Oil & gas, agriculture, and technology sectors
- Regulatory focus on local content and CBN policies
- High mobile penetration and digital adoption
- Challenges: Infrastructure, forex, and regulatory complexity
            """,
            "KE": """
- East African hub for technology and innovation
- Leading mobile money market (M-Pesa)
- Strong agriculture, tourism, and tech sectors
- Business-friendly regulatory environment
- Regional gateway for East African trade
- Challenges: Infrastructure gaps and regional instability
            """,
            "ZA": """
- Most developed financial markets in Africa
- Strong mining, manufacturing, and services sectors
- Advanced regulatory framework and compliance standards
- High inequality and unemployment challenges
- Gateway to Southern African markets
- Challenges: Load shedding, crime, and economic inequality
            """,
            "GH": """
- Stable democracy with growing economy
- Strong gold, cocoa, and oil sectors
- Emerging fintech and digital services
- Business-friendly policies and incentives
- Regional hub for West African trade
- Challenges: Infrastructure and access to finance
            """,
            "UG": """
- Growing economy with young population
- Strong agriculture and emerging oil sector
- Increasing mobile money adoption
- Government focus on industrialization
- Regional trade opportunities
- Challenges: Infrastructure and skills gaps
            """,
            "TZ": """
- Large market with growing middle class
- Strong mining, agriculture, and tourism
- Increasing digital financial services
- Government industrialization agenda
- Regional trade hub potential
- Challenges: Infrastructure and regulatory complexity
            """,
            "RW": """
- Business-friendly environment and low corruption
- Strong ICT and services sector growth
- Government focus on digital transformation
- Regional financial services hub
- Excellent governance and ease of doing business
- Challenges: Small market size and landlocked location
            """,
            "ET": """
- Second largest population in Africa
- Growing manufacturing and agriculture sectors
- Government-led development model
- Emerging financial services sector
- Regional hub for international organizations
- Challenges: Foreign exchange and political stability
            """,
            "EG": """
- Large market with strategic location
- Strong manufacturing and services sectors
- Government economic reform program
- Growing fintech and digital services
- Gateway to Middle East and Africa
- Challenges: Currency stability and bureaucracy
            """,
            "MA": """
- Gateway to Africa and Europe
- Strong manufacturing and services sectors
- Advanced financial system and regulations
- Government focus on digital transformation
- Regional hub for French-speaking Africa
- Challenges: Youth unemployment and regional disparities
            """
        }
        
        return regional_contexts.get(self.config.region, regional_contexts["NG"]).strip()
    
    def _format_tools_description(self) -> str:
        """Format available tools for the prompt."""
        if not self.tools:
            return "No specialized tools currently available. Rely on knowledge and reasoning."
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    async def provide_guidance(
        self,
        business_context: Dict[str, Any],
        challenge_description: str,
        guidance_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Provide business guidance and recommendations.
        
        Args:
            business_context: Context about the business
            challenge_description: Description of the challenge or question
            guidance_type: Type of guidance needed (strategy, finance, operations, etc.)
            
        Returns:
            Guidance and recommendations
        """
        input_data = {
            "query": f"Provide {guidance_type} guidance for the following business challenge: {challenge_description}",
            "business_context": business_context,
            "guidance_type": guidance_type,
            "expertise_areas": self.expertise_areas
        }
        
        context = {
            "operation_type": "business_guidance",
            "guidance_style": self.guidance_style,
            "regional_expertise": True,
            "business_size": business_context.get("size", "sme"),
            "industry": business_context.get("industry", "general")
        }
        
        return await self.execute(input_data, context)
    
    async def analyze_market_opportunity(
        self,
        market_data: Dict[str, Any],
        business_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze market opportunities for the business.
        
        Args:
            market_data: Market information and data
            business_profile: Business profile and capabilities
            
        Returns:
            Market analysis and opportunity assessment
        """
        input_data = {
            "query": "Analyze the market opportunity and provide strategic recommendations",
            "market_data": market_data,
            "business_profile": business_profile,
            "analysis_type": "market_opportunity"
        }
        
        context = {
            "operation_type": "market_analysis",
            "regional_focus": self.config.region,
            "cultural_considerations": self.config.cultural_context,
            "competitive_landscape": True
        }
        
        return await self.execute(input_data, context)
    
    async def create_business_plan(
        self,
        business_idea: str,
        entrepreneur_profile: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Help create or review a business plan.
        
        Args:
            business_idea: Description of the business idea
            entrepreneur_profile: Entrepreneur background and experience
            market_context: Market and competitive context
            
        Returns:
            Business plan guidance and framework
        """
        input_data = {
            "query": f"Help create a comprehensive business plan for: {business_idea}",
            "business_idea": business_idea,
            "entrepreneur_profile": entrepreneur_profile,
            "market_context": market_context,
            "plan_type": "comprehensive"
        }
        
        context = {
            "operation_type": "business_planning",
            "regional_requirements": self._get_business_plan_requirements(),
            "funding_landscape": self._get_funding_options(),
            "regulatory_considerations": True
        }
        
        return await self.execute(input_data, context)
    
    async def provide_financial_guidance(
        self,
        financial_data: Dict[str, Any],
        guidance_area: str = "general"
    ) -> Dict[str, Any]:
        """
        Provide financial planning and management guidance.
        
        Args:
            financial_data: Current financial information
            guidance_area: Specific area (cash_flow, funding, budgeting, etc.)
            
        Returns:
            Financial guidance and recommendations
        """
        input_data = {
            "query": f"Provide {guidance_area} financial guidance based on the business financial data",
            "financial_data": financial_data,
            "guidance_area": guidance_area,
            "currency": self._get_local_currency()
        }
        
        context = {
            "operation_type": "financial_guidance",
            "local_banking": self._get_banking_context(),
            "payment_systems": self._get_payment_systems(),
            "tax_considerations": True
        }
        
        return await self.execute(input_data, context)
    
    def _get_business_plan_requirements(self) -> Dict[str, Any]:
        """Get regional business plan requirements."""
        return {
            "registration_requirements": True,
            "tax_obligations": True,
            "licensing_needs": True,
            "compliance_standards": True,
            "local_content_requirements": self.config.region in ["NG", "ZA", "GH"]
        }
    
    def _get_funding_options(self) -> List[str]:
        """Get regional funding options."""
        base_options = [
            "microfinance",
            "bank_loans", 
            "government_grants",
            "angel_investors",
            "venture_capital"
        ]
        
        regional_options = {
            "NG": base_options + ["bon_grants", "bank_of_industry", "nexim_bank"],
            "KE": base_options + ["kiva", "kdb_bank", "uwezo_fund"],
            "ZA": base_options + ["seda", "idt", "nef_funding"],
            "GH": base_options + ["masloc", "nbssi", "exim_bank"],
            "RW": base_options + ["bdf", "wasac", "guarantee_fund"]
        }
        
        return regional_options.get(self.config.region, base_options)
    
    def _get_banking_context(self) -> Dict[str, Any]:
        """Get local banking and financial context."""
        return {
            "major_banks": self._get_major_banks(),
            "digital_banking": True,
            "mobile_money": self.config.region in ["KE", "UG", "TZ", "GH", "RW"],
            "forex_regulations": self.config.region in ["NG", "ET", "EG"],
            "credit_scoring": "emerging"
        }
    
    def _get_major_banks(self) -> List[str]:
        """Get major banks by region."""
        banks = {
            "NG": ["GTBank", "Zenith", "Access", "First Bank", "UBA"],
            "KE": ["KCB", "Equity", "Cooperative", "Standard Chartered", "Barclays"],
            "ZA": ["Standard Bank", "FNB", "ABSA", "Nedbank", "Capitec"],
            "GH": ["GCB", "Ecobank", "Standard Chartered", "Fidelity", "ADB"],
            "UG": ["Stanbic", "Centenary", "DFCU", "Equity", "Standard Chartered"]
        }
        
        return banks.get(self.config.region, ["Local Banks", "International Banks"])
    
    def _get_payment_systems(self) -> List[str]:
        """Get available payment systems."""
        systems = {
            "NG": ["Paystack", "Flutterwave", "Interswitch", "Remita"],
            "KE": ["M-Pesa", "Airtel Money", "Equity Bank", "KCB"],
            "ZA": ["PayFast", "Peach Payments", "Ozow", "SnapScan"],
            "GH": ["MTN Mobile Money", "AirtelTigo Money", "Vodafone Cash"],
            "UG": ["MTN Mobile Money", "Airtel Money", "Centenary Mobile"]
        }
        
        return systems.get(self.config.region, ["Mobile Money", "Bank Transfers"])
    
    def _get_local_currency(self) -> str:
        """Get local currency based on region."""
        currencies = {
            "NG": "NGN",
            "KE": "KES", 
            "ZA": "ZAR",
            "GH": "GHS",
            "UG": "UGX",
            "TZ": "TZS",
            "RW": "RWF",
            "ET": "ETB",
            "EG": "EGP",
            "MA": "MAD"
        }
        
        return currencies.get(self.config.region, "USD")
