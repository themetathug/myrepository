import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime
import aiohttp
import os
import re
from urllib.parse import urlparse

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# LangChain imports
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None
    
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field, validator
from typing_extensions import TypedDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums for structured responses
class SearchCategory(Enum):
    COMPANY = "company"
    INDUSTRY = "industry"
    COMPETITION = "competition"

class AnalysisType(Enum):
    STRATEGIC = "strategic"
    COMPETITIVE = "competitive"
    OPERATIONAL = "operational"
    MARKET = "market"
    TECHNICAL = "technical"

# Pydantic models for structured data
class SearchResult(BaseModel):
    category: SearchCategory
    query: str
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str]
    source_domain: str

class EnrichedContext(BaseModel):
    original_query: str
    extracted_entities: Dict[str, List[str]]
    search_results: List[SearchResult]
    web_intelligence: Dict[str, Any]
    confidence_score: float
    data_freshness: str
    analysis_recommendations: List[str]

# LangGraph State for Context Agent
class ContextAgentState(TypedDict):
    """State for the Context Agent with Tavily integration"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    session_id: str
    current_step: str
    
    # Search orchestration
    search_queries: Dict[str, List[str]]  # category -> list of queries
    search_results: Dict[str, List[Dict[str, Any]]]  # category -> results
    parallel_search_status: Dict[str, str]
    
    # Context enrichment
    extracted_entities: Dict[str, List[str]]
    web_intelligence: Dict[str, Any]
    enriched_context: Optional[Dict[str, Any]]
    
    # Output for Protocol Selector
    structured_output: Optional[Dict[str, Any]]
    confidence_metrics: Dict[str, float]
    processing_metadata: Dict[str, Any]
    
    # Error handling
    error_count: int
    failed_searches: List[str]

@dataclass
class ContextAgentConfig:
    """Configuration for Context Agent with Tavily"""
    tavily_api_key: "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"
    llm_provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 2000
    max_search_results_per_query: int = 3
    search_timeout: int = 30
    enable_parallel_search: bool = True
    max_concurrent_searches: int = 15

class TavilySearchClient:
    """Async client for Tavily API integration"""
    
    def __init__(self, api_key: str, max_results: int = 3):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
        self.max_results = max_results
        
    async def search(self, query: str, search_depth: str = "basic") -> Dict[str, Any]:
        """Perform search using Tavily API"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": True,
            "max_results": self.max_results,
            "include_domains": [],
            "exclude_domains": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._format_search_result(result, query)
                    else:
                        logger.error(f"Tavily API error: {response.status}")
                        return self._empty_result(query)
                        
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return self._empty_result(query)
    
    def _format_search_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format Tavily response into standardized format"""
        
        formatted_results = []
        
        for item in result.get("results", []):
            formatted_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
                "published_date": item.get("published_date"),
                "source_domain": self._extract_domain(item.get("url", ""))
            })
        
        return {
            "query": query,
            "answer": result.get("answer", ""),
            "results": formatted_results,
            "search_time": datetime.now().isoformat(),
            "result_count": len(formatted_results)
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"
    
    def _empty_result(self, query: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "query": query,
            "answer": "",
            "results": [],
            "search_time": datetime.now().isoformat(),
            "result_count": 0,
            "error": True
        }

# Tools for the Context Agent
@tool
def extract_search_entities(user_input: str) -> Dict[str, List[str]]:
    """Extract companies, industries, and competition entities from user input"""
    
    import re
    
    # Common industry keywords
    industry_keywords = [
        "technology", "tech", "ai", "artificial intelligence", "software", "fintech",
        "healthcare", "pharmaceutical", "automotive", "retail", "e-commerce",
        "manufacturing", "construction", "energy", "oil", "gas", "banking",
        "insurance", "telecommunications", "media", "entertainment", "gaming"
    ]
    
    # Company detection patterns
    company_patterns = [
        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Co|Company))?\b',
        r'\b[A-Z]{2,10}\b'  # Acronyms
    ]
    
    text = user_input.lower()
    
    entities = {
        "companies": [],
        "industries": [],
        "competitors": [],
        "products": [],
        "markets": [],
        "technologies": []
    }
    
    # Extract industry mentions
    for keyword in industry_keywords:
        if keyword in text:
            entities["industries"].append(keyword)
    
    # Extract potential company names (basic pattern matching)
    for pattern in company_patterns:
        matches = re.findall(pattern, user_input)
        entities["companies"].extend(matches[:3])  # Limit to first 3
    
    # Extract market/geographic indicators
    market_keywords = ["market", "europe", "asia", "america", "global", "domestic", "international"]
    for keyword in market_keywords:
        if keyword in text:
            entities["markets"].append(keyword)
    
    # Extract technology terms
    tech_keywords = ["cloud", "mobile", "web", "platform", "api", "blockchain", "ml", "data"]
    for keyword in tech_keywords:
        if keyword in text:
            entities["technologies"].append(keyword)
    
    # Remove duplicates and limit results
    for key in entities:
        entities[key] = list(set(entities[key]))[:5]
    
    return entities

@tool
def generate_search_queries(user_input: str, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Generate 15 search queries across 3 categories (5 each)"""
    
    queries = {
        "company": [],
        "industry": [],
        "competition": []
    }
    
    # Base terms from user input
    base_terms = user_input.split()[:3]  # First 3 words as base
    
    # Company queries (5)
    company_base = entities.get("companies", ["company"])[:2]
    for company in company_base:
        queries["company"].extend([
            f"{company} financial performance 2024",
            f"{company} market share analysis",
            f"{company} recent news updates"
        ])
    
    # Add generic company queries if needed
    while len(queries["company"]) < 5:
        queries["company"].append(f"{' '.join(base_terms)} company analysis")
        queries["company"].append(f"{' '.join(base_terms)} business model")
    
    queries["company"] = queries["company"][:5]
    
    # Industry queries (5)
    industries = entities.get("industries", ["technology"])[:2]
    for industry in industries:
        queries["industry"].extend([
            f"{industry} industry trends 2024",
            f"{industry} market size forecast",
            f"{industry} growth analysis"
        ])
    
    # Add generic industry queries if needed
    while len(queries["industry"]) < 5:
        queries["industry"].append(f"{' '.join(base_terms)} industry overview")
        queries["industry"].append(f"{' '.join(base_terms)} market trends")
    
    queries["industry"] = queries["industry"][:5]
    
    # Competition queries (5)
    competitors = entities.get("competitors", [])
    if competitors:
        for competitor in competitors[:2]:
            queries["competition"].extend([
                f"{competitor} vs competitors",
                f"{competitor} competitive analysis"
            ])
    
    # Add generic competition queries
    while len(queries["competition"]) < 5:
        queries["competition"].append(f"{' '.join(base_terms)} competitors analysis")
        queries["competition"].append(f"{' '.join(base_terms)} competitive landscape")
        queries["competition"].append(f"{' '.join(base_terms)} market competition")
    
    queries["competition"] = queries["competition"][:5]
    
    return queries

@tool 
def analyze_search_results(search_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Analyze and synthesize search results for web intelligence"""
    
    intelligence = {
        "data_quality_score": 0.0,
        "source_diversity": 0.0,
        "content_freshness": "",
        "key_insights": [],
        "entity_mentions": {},
        "sentiment_indicators": {},
        "market_signals": [],
        "competitive_intelligence": [],
        "risk_indicators": []
    }
    
    total_results = 0
    sources = set()
    recent_content = 0
    
    # Analyze all search results
    for category, results in search_results.items():
        for result_batch in results:
            for result in result_batch.get("results", []):
                total_results += 1
                
                # Track source diversity
                sources.add(result.get("source_domain", "unknown"))
                
                # Check content freshness (basic check)
                content = result.get("content", "")
                if any(term in content.lower() for term in ["2024", "recent", "latest", "new"]):
                    recent_content += 1
                
                # Extract key insights (simplified)
                if len(content) > 100:
                    intelligence["key_insights"].append({
                        "category": category,
                        "insight": content[:200] + "...",
                        "source": result.get("source_domain", ""),
                        "score": result.get("score", 0.0)
                    })
    
    # Calculate metrics
    intelligence["data_quality_score"] = min(1.0, total_results / 10.0)
    intelligence["source_diversity"] = min(1.0, len(sources) / 8.0)
    intelligence["content_freshness"] = "high" if recent_content > total_results * 0.6 else "medium"
    
    # Limit insights to top 10
    intelligence["key_insights"] = sorted(
        intelligence["key_insights"], 
        key=lambda x: x["score"], 
        reverse=True
    )[:10]
    
    return intelligence

class ContextAgent:
    """
    MAPSHOCK Context Agent with Tavily Search Integration
    
    Responsibilities:
    1. Extract entities from user input
    2. Generate 15 parallel search queries (5 company, 5 industry, 5 competition)
    3. Execute searches via Tavily API
    4. Enrich context with web intelligence
    5. Structure data for Protocol Selector Agent
    """
    
    def __init__(self, config: ContextAgentConfig):
        self.config = config
        self.session_id = str(uuid.uuid4())
        
        # Initialize Tavily client
        self.tavily_client = TavilySearchClient(
            api_key=config.tavily_api_key,
            max_results=config.max_search_results_per_query
        )
        
        # Initialize tools
        self.tools = [extract_search_entities, generate_search_queries, analyze_search_results]
        self.tool_node = ToolNode(self.tools)
        
        print(f"DEBUG: self.tools initialized as: {self.tools}")
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize memory
        self.memory = MemorySaver()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"Context Agent initialized with Tavily integration")
    
    def _initialize_llm(self):
        """Initialize LLM with tool binding"""
        try:
            if self.config.llm_provider == "openai":
                llm = ChatOpenAI(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                return llm.bind_tools(self.tools)
            elif self.config.llm_provider == "anthropic" and ChatAnthropic:
                llm = ChatAnthropic(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                return llm.bind_tools(self.tools)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for search orchestration"""
        
        workflow = StateGraph(ContextAgentState)
        
        # Add nodes for search orchestration workflow
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("extract_entities", self._extract_entities_node)
        workflow.add_node("generate_queries", self._generate_queries_node)
        workflow.add_node("execute_parallel_search", self._execute_parallel_search_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("enrich_context", self._enrich_context_node)
        workflow.add_node("structure_output", self._structure_output_node)
        
        # Define workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "extract_entities")
        workflow.add_edge("extract_entities", "generate_queries")
        workflow.add_edge("generate_queries", "execute_parallel_search")
        workflow.add_edge("execute_parallel_search", "analyze_results")
        workflow.add_edge("analyze_results", "enrich_context")
        workflow.add_edge("enrich_context", "structure_output")
        workflow.add_edge("structure_output", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _initialize_node(self, state: ContextAgentState) -> ContextAgentState:
        """Initialize search session"""
        logger.info(f"Initializing search orchestration session: {self.session_id}")
        
        state["session_id"] = self.session_id
        state["current_step"] = "initialized"
        state["search_queries"] = {"company": [], "industry": [], "competition": []}
        state["search_results"] = {"company": [], "industry": [], "competition": []}
        state["parallel_search_status"] = {}
        state["extracted_entities"] = {}
        state["web_intelligence"] = {}
        state["confidence_metrics"] = {}
        state["processing_metadata"] = {}
        state["error_count"] = 0
        state["failed_searches"] = []
        
        return state
    
    async def _extract_entities_node(self, state: ContextAgentState) -> ContextAgentState:
        """Extract entities from user input"""
        logger.info("Extracting entities from user input")
        
        try:
            user_input = state["user_input"]
            entities = extract_search_entities(user_input)
            
            state["extracted_entities"] = entities
            state["current_step"] = "entities_extracted"
            
            logger.info(f"Extracted entities: {entities}")
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            state["error_count"] += 1
            state["extracted_entities"] = {
                "companies": [], "industries": [], "competitors": [],
                "products": [], "markets": [], "technologies": []
            }
        
        return state
    
    async def _generate_queries_node(self, state: ContextAgentState) -> ContextAgentState:
        """Generate 15 search queries across 3 categories"""
        logger.info("Generating search queries")
        
        try:
            user_input = state["user_input"]
            entities = state["extracted_entities"]
            
            queries = generate_search_queries.invoke({"user_input": user_input, "entities": entities})
            state["search_queries"] = queries
            state["current_step"] = "queries_generated"
            
            # Log generated queries
            total_queries = sum(len(q_list) for q_list in queries.values())
            logger.info(f"Generated {total_queries} search queries across 3 categories")
            
            for category, query_list in queries.items():
                logger.info(f"{category.capitalize()} queries: {len(query_list)}")
                for i, query in enumerate(query_list, 1):
                    logger.info(f"  {i}. {query}")
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            state["error_count"] += 1
            # Fallback to basic queries
            state["search_queries"] = {
                "company": [f"{state['user_input']} company analysis"],
                "industry": [f"{state['user_input']} industry analysis"],
                "competition": [f"{state['user_input']} competition analysis"]
            }
        
        return state
    
    async def _execute_parallel_search_node(self, state: ContextAgentState) -> ContextAgentState:
        """Execute 15 parallel searches using Tavily"""
        logger.info("Executing parallel searches via Tavily API")
        
        search_tasks = []
        query_metadata = []
        
        # Prepare all search tasks
        for category, queries in state["search_queries"].items():
            for query in queries:
                search_tasks.append(self.tavily_client.search(query))
                query_metadata.append({"category": category, "query": query})
        
        try:
            # Execute all searches in parallel
            logger.info(f"Starting {len(search_tasks)} parallel searches...")
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results by category
            results_by_category = {"company": [], "industry": [], "competition": []}
            successful_searches = 0
            
            for i, result in enumerate(search_results):
                metadata = query_metadata[i]
                category = metadata["category"]
                query = metadata["query"]
                
                if isinstance(result, Exception):
                    logger.error(f"Search failed for '{query}': {result}")
                    state["failed_searches"].append(query)
                    # Add empty result
                    results_by_category[category].append({
                        "query": query,
                        "results": [],
                        "error": True
                    })
                else:
                    results_by_category[category].append(result)
                    successful_searches += 1
                    state["parallel_search_status"][query] = "completed"
            
            state["search_results"] = results_by_category
            state["current_step"] = "searches_completed"
            
            logger.info(f"Completed {successful_searches}/{len(search_tasks)} searches successfully")
            
            # Log results summary
            for category, results in results_by_category.items():
                total_results = sum(len(r.get("results", [])) for r in results)
                logger.info(f"{category.capitalize()}: {len(results)} queries, {total_results} total results")
            
        except Exception as e:
            logger.error(f"Parallel search execution failed: {e}")
            state["error_count"] += 1
            state["search_results"] = {"company": [], "industry": [], "competition": []}
        
        return state
    
    async def _analyze_results_node(self, state: ContextAgentState) -> ContextAgentState:
        """Analyze search results for web intelligence"""
        logger.info("Analyzing search results")
        
        try:
            search_results = state["search_results"]
            print(f"DEBUG: search_results passed to analyze_search_results: {search_results}")
            intelligence = analyze_search_results.invoke({"search_results": search_results})
            
            state["web_intelligence"] = intelligence
            state["current_step"] = "results_analyzed"
            
            # Calculate confidence metrics
            state["confidence_metrics"] = {
                "data_quality": intelligence["data_quality_score"],
                "source_diversity": intelligence["source_diversity"],
                "search_success_rate": 1.0 - (len(state["failed_searches"]) / 15.0),
                "overall_confidence": (
                    intelligence["data_quality_score"] + 
                    intelligence["source_diversity"] + 
                    (1.0 - len(state["failed_searches"]) / 15.0)
                ) / 3.0
            }
            
            logger.info(f"Analysis complete. Overall confidence: {state['confidence_metrics']['overall_confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"Results analysis failed: {e}")
            state["error_count"] += 1
            state["web_intelligence"] = {"error": "Analysis failed"}
            state["confidence_metrics"] = {"overall_confidence": 0.0}
        
        return state
    
    async def _enrich_context_node(self, state: ContextAgentState) -> ContextAgentState:
        """Enrich context with web intelligence and MAPSHOCK framework preparation"""
        logger.info("Enriching context for MAPSHOCK analysis")
        
        try:
            # Create enriched context
            enriched_context = {
                "original_query": state["user_input"],
                "extracted_entities": state["extracted_entities"],
                "search_summary": {
                    "total_queries": sum(len(queries) for queries in state["search_queries"].values()),
                    "successful_searches": 15 - len(state["failed_searches"]),
                    "failed_searches": len(state["failed_searches"]),
                    "categories_covered": ["company", "industry", "competition"]
                },
                "web_intelligence": state["web_intelligence"],
                "confidence_metrics": state["confidence_metrics"],
                "data_freshness": state["web_intelligence"].get("content_freshness", "unknown"),
                
                # MAPSHOCK preparation hints
                "suggested_analysis_type": self._suggest_analysis_type(state),
                "suggested_threat_tier": self._suggest_threat_tier(state),
                "suggested_domains": self._suggest_mapshock_domains(state),
                "urgency_indicators": self._detect_urgency(state),
                
                # Protocol hints for next agent
                "protocol_hints": {
                    "data_verification_needed": True,
                    "real_time_sync_recommended": self._needs_real_time_sync(state),
                    "cross_domain_analysis": len(state["extracted_entities"].get("industries", [])) > 1,
                    "confidence_calibration_required": state["confidence_metrics"]["overall_confidence"] < 0.7
                }
            }
            
            state["enriched_context"] = enriched_context
            state["current_step"] = "context_enriched"
            
        except Exception as e:
            logger.error(f"Context enrichment failed: {e}")
            state["error_count"] += 1
        
        return state
    
    async def _structure_output_node(self, state: ContextAgentState) -> ContextAgentState:
        """Structure final output for Protocol Selector Agent"""
        logger.info("Structuring output for Protocol Selector")
        
        try:
            structured_output = {
                "session_id": state["session_id"],
                "timestamp": datetime.now().isoformat(),
                "processing_summary": {
                    "input_processed": True,
                    "entities_extracted": len(state["extracted_entities"]),
                    "searches_completed": 15 - len(state["failed_searches"]),
                    "web_intelligence_gathered": bool(state["web_intelligence"]),
                    "context_enriched": bool(state["enriched_context"]),
                    "errors_encountered": state["error_count"]
                },
                
                # Core data for Protocol Selector
                "enriched_context": state["enriched_context"],
                "search_intelligence": {
                    "company_data": self._summarize_category_results("company", state),
                    "industry_data": self._summarize_category_results("industry", state),
                    "competition_data": self._summarize_category_results("competition", state)
                },
                
                # Decision support for Protocol Selector
                "protocol_selector_inputs": {
                    "analysis_type_suggestion": state["enriched_context"]["suggested_analysis_type"],
                    "threat_tier_suggestion": state["enriched_context"]["suggested_threat_tier"],
                    "domain_suggestions": state["enriched_context"]["suggested_domains"],
                    "urgency_level": state["enriched_context"]["urgency_indicators"],
                    "confidence_score": state["confidence_metrics"]["overall_confidence"],
                    "protocol_hints": state["enriched_context"]["protocol_hints"]
                },
                
                # Quality metrics
                "data_quality_metrics": state["confidence_metrics"],
                "processing_metadata": {
                    "total_processing_time": "calculated_in_production",
                    "search_coverage": (15 - len(state["failed_searches"])) / 15.0,
                    "entity_extraction_success": bool(state["extracted_entities"]),
                    "web_intelligence_quality": state["web_intelligence"].get("data_quality_score", 0.0)
                }
            }
            
            state["structured_output"] = structured_output
            state["current_step"] = "output_structured"
            
            logger.info("Context Agent processing completed successfully")
            
        except Exception as e:
            logger.error(f"Output structuring failed: {e}")
            state["error_count"] += 1
        
        return state
    
    def _suggest_analysis_type(self, state: ContextAgentState) -> str:
        """Suggest analysis type based on user input and search results"""
        user_input = state["user_input"].lower()
        
        if any(word in user_input for word in ["compete", "competitor", "competitive", "rival"]):
            return "competitive"
        elif any(word in user_input for word in ["strategy", "strategic", "long-term", "planning"]):
            return "strategic"
        elif any(word in user_input for word in ["market", "industry", "sector"]):
            return "market"
        elif any(word in user_input for word in ["technical", "technology", "system"]):
            return "technical"
        else:
            return "operational"
    
    def _suggest_threat_tier(self, state: ContextAgentState) -> str:
        """Suggest threat tier based on urgency and content analysis"""
        user_input = state["user_input"].lower()
        
        if any(word in user_input for word in ["urgent", "critical", "emergency", "immediate"]):
            return "21-25"
        elif any(word in user_input for word in ["important", "significant", "high priority"]):
            return "11-20"
        else:
            return "1-10"
    
    def _suggest_mapshock_domains(self, state: ContextAgentState) -> List[str]:
        """Suggest MAPSHOCK domains based on extracted entities and context"""
        domains = []
        entities = state["extracted_entities"]
        
        # Always include Intelligence & Security as baseline
        domains.append("Intelligence & Security")
        
        # Add Economic & Financial if financial/business entities found
        if entities.get("companies") or "financial" in state["user_input"].lower():
            domains.append("Economic & Financial")
        
        # Add Corporate Systems if corporate entities found
        if entities.get("companies"):
            domains.append("Corporate Systems")
        
        # Add Social & Technological if tech entities found
        if entities.get("technologies"):
            domains.append("Social & Technological")
        
        return domains[:4]  # Limit to 4 domains
    
    def _detect_urgency(self, state: ContextAgentState) -> str:
        """Detect urgency level from user input"""
        user_input = state["user_input"].lower()
        
        if any(word in user_input for word in ["immediate", "urgent", "asap", "emergency"]):
            return "immediate"
        elif any(word in user_input for word in ["soon", "quickly", "fast", "priority"]):
            return "high"
        else:
            return "medium"
    
    def _needs_real_time_sync(self, state: ContextAgentState) -> bool:
        """Determine if real-time data sync is needed"""
        # Check if search results contain recent/time-sensitive content
        return state["web_intelligence"].get("content_freshness") == "high"
    
    def _summarize_category_results(self, category: str, state: ContextAgentState) -> Dict[str, Any]:
        """Summarize search results for a specific category"""
        results = state["search_results"].get(category, [])
        
        total_results = sum(len(r.get("results", [])) for r in results)
        top_sources = set()
        key_findings = []
        
        for result_batch in results:
            for result in result_batch.get("results", []):
                top_sources.add(result.get("source_domain", "unknown"))
                if result.get("content") and len(result["content"]) > 50:
                    key_findings.append({
                        "title": result.get("title", "")[:100],
                        "content_preview": result.get("content", "")[:200],
                        "score": result.get("score", 0.0),
                        "source": result.get("source_domain", "")
                    })
        
        # Sort findings by score and limit to top 5
        key_findings = sorted(key_findings, key=lambda x: x["score"], reverse=True)[:5]
        
        return {
            "query_count": len(results),
            "total_results": total_results,
            "unique_sources": len(top_sources),
            "top_sources": list(top_sources)[:5],
            "key_findings": key_findings,
            "coverage_score": min(1.0, total_results / 10.0)
        }
    
    async def analyze(self, user_input: str) -> Dict[str, Any]:
        """Main method to analyze user input with search orchestration"""
        
        # Initialize state
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "session_id": "",
            "current_step": "starting",
            "search_queries": {},
            "search_results": {},
            "parallel_search_status": {},
            "extracted_entities": {},
            "web_intelligence": {},
            "enriched_context": None,
            "structured_output": None,
            "confidence_metrics": {},
            "processing_metadata": {},
            "error_count": 0,
            "failed_searches": []
        }
        
        # Run the graph workflow
        config = {"configurable": {"thread_id": self.session_id}}
        
        try:
            logger.info(f"Starting Context Agent analysis for: {user_input[:100]}...")
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            return {
                "success": True,
                "structured_output": final_state["structured_output"],
                "session_id": final_state["session_id"],
                "processing_summary": {
                    "final_step": final_state["current_step"],
                    "error_count": final_state["error_count"],
                    "searches_completed": 15 - len(final_state["failed_searches"]),
                    "failed_searches": final_state["failed_searches"]
                },
                "ready_for_protocol_selector": final_state["current_step"] == "output_structured"
            }
            
        except Exception as e:
            logger.error(f"Context Agent analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": self._create_fallback_output(user_input)
            }
    
    def _create_fallback_output(self, user_input: str) -> Dict[str, Any]:
        """Create fallback output when analysis fails"""
        return {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "processing_summary": {
                "input_processed": True,
                "entities_extracted": 0,
                "searches_completed": 0,
                "web_intelligence_gathered": False,
                "context_enriched": False,
                "errors_encountered": 1
            },
            "enriched_context": {
                "original_query": user_input,
                "extracted_entities": {"companies": [], "industries": [], "competitors": []},
                "suggested_analysis_type": "operational",
                "suggested_threat_tier": "1-10",
                "suggested_domains": ["Intelligence & Security"],
                "urgency_indicators": "medium"
            },
            "protocol_selector_inputs": {
                "analysis_type_suggestion": "operational",
                "threat_tier_suggestion": "1-10", 
                "domain_suggestions": ["Intelligence & Security"],
                "urgency_level": "medium",
                "confidence_score": 0.3,
                "protocol_hints": {
                    "data_verification_needed": True,
                    "real_time_sync_recommended": False,
                    "cross_domain_analysis": False,
                    "confidence_calibration_required": True
                }
            }
        }

# Example usage and testing
async def test_context_agent(user_query: str = None):
    """Test the Context Agent with Tavily integration"""
    
    # Check if Tavily API key is available
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("Error: TAVILY_API_KEY environment variable not set")
        print("Please set your Tavily API key: export TAVILY_API_KEY='your-key'")
        print("You can get a free API key at: https://tavily.com")
        return
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        return
    
    print("Starting Context Agent Test")
    print("API Keys found - OK")
    
    # Initialize agent with error handling
    try:
        config = ContextAgentConfig(
            tavily_api_key=tavily_api_key,
            llm_provider="openai",
            model_name="gpt-3.5-turbo",  # Use cheaper model for testing
            temperature=0.3,
            max_search_results_per_query=2,  # Reduce for faster testing
            enable_parallel_search=True
        )
        
        agent = ContextAgent(config)
        print("Agent initialized successfully")
        
    except Exception as e:
        print(f"Agent initialization failed: {e}")
        return
    
    # Use provided query or prompt for input
    if not user_query:
        user_query = input("Enter your analysis query: ").strip()
        if not user_query:
            print("No query provided, using default example")
            user_query = "Analyze competitive landscape and strategic options for semiconductor equipment market"
    
    print(f"\nTesting with: {user_query}")
    print("Starting analysis...")
    
    try:
        # Run analysis
        result = await agent.analyze(user_query)
        
        if result["success"]:
            output = result["structured_output"]
            
            print(f"\nAnalysis completed successfully!")
            print(f"Session ID: {output['session_id']}")
            print(f"Searches completed: {result['processing_summary']['searches_completed']}/15")
            
            # Show key results
            enriched = output["enriched_context"]
            print(f"\nKey Results:")
            print(f"  Analysis Type: {enriched['suggested_analysis_type']}")
            print(f"  Threat Tier: {enriched['suggested_threat_tier']}")
            print(f"  Suggested Domains: {enriched['suggested_domains']}")
            print(f"  Confidence Score: {output['protocol_selector_inputs']['confidence_score']:.2f}")
            
            # Show search summary
            search_intel = output["search_intelligence"]
            print(f"\nSearch Results Summary:")
            for category in ["company_data", "industry_data", "competition_data"]:
                data = search_intel[category]
                print(f"  {category.replace('_', ' ').title()}: {data['total_results']} results from {data['unique_sources']} sources")
            
            print(f"\nReady for Protocol Selector: {result['ready_for_protocol_selector']}")
            
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")
            if 'fallback_data' in result:
                print("Fallback data available")
            
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

# Simple standalone test function
async def simple_test(test_query: str = None):
    """Simple test without full workflow"""
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("Missing TAVILY_API_KEY")
        return
    
    print("Testing Tavily client...")
    
    # Test Tavily client directly
    client = TavilySearchClient(tavily_api_key, max_results=2)
    
    # Use provided query or default
    search_query = test_query or "technology market analysis"
    
    try:
        result = await client.search(search_query)
        print(f"Tavily search successful: {result['result_count']} results")
        
        if result['results']:
            print(f"Sample result: {result['results'][0]['title']}")
        
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return
    
    print("Testing entity extraction...")
    
    # Test entity extraction
    try:
        test_input = test_query or "Analyze strategic options for technology company in competitive market"
        entities = extract_search_entities(test_input)
        print(f"Entity extraction successful: {entities}")
        
    except Exception as e:
        print(f"Entity extraction failed: {e}")
        return
    
    print("All basic tests passed!")

# Production-ready example
async def production_example(business_query: str = None):
    """Production-ready usage example with proper error handling"""
    
    # Validate environment
    required_env_vars = ["TAVILY_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        print("Please set them before running the agent.")
        return None
    
    try:
        # Production configuration
        config = ContextAgentConfig(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            llm_provider="openai",
            model_name="gpt-4",
            temperature=0.2,  # Lower temperature for production
            max_search_results_per_query=3,
            enable_parallel_search=True,
            max_concurrent_searches=15,
            search_timeout=30
        )
        
        agent = ContextAgent(config)
        
        # Use provided query or prompt for input
        if not business_query:
            business_query = input("Enter your business analysis query: ").strip()
            if not business_query:
                print("No query provided, please provide a valid business query")
                return None
        
        print(f"Processing: {business_query}")
        print("Starting comprehensive search orchestration...")
        
        start_time = datetime.now()
        result = await agent.analyze(business_query)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        if result["success"]:
            structured_output = result["structured_output"]
            
            print(f"\nAnalysis completed in {processing_time:.2f} seconds")
            print(f"Ready for Protocol Selector: {result['ready_for_protocol_selector']}")
            
            # Summary metrics
            ps_inputs = structured_output["protocol_selector_inputs"]
            print(f"\nAnalysis Summary:")
            print(f"  Confidence Score: {ps_inputs['confidence_score']:.2f}")
            print(f"  Analysis Type: {ps_inputs['analysis_type_suggestion']}")
            print(f"  Threat Tier: {ps_inputs['threat_tier_suggestion']}")
            print(f"  Domains: {len(ps_inputs['domain_suggestions'])}")
            print(f"  Processing Time: {processing_time:.2f}s")
            
            return structured_output
            
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"Production example failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# Main execution
if __name__ == "__main__":
    print("MAPSHOCK Context Agent with Tavily Search Integration")
    print("=" * 60)
    print("Features:")
    print("- Entity extraction from user input")
    print("- 15 parallel web searches (5 company, 5 industry, 5 competition)")
    print("- Context enrichment with web intelligence")
    print("- Structured output for Protocol Selector Agent")
    print("- LangGraph workflow orchestration")
    print()
    
    print("Setup Instructions:")
    print("1. pip install langgraph langchain langchain-openai aiohttp")
    print("2. export TAVILY_API_KEY='your-tavily-key'")
    print("3. export OPENAI_API_KEY='your-openai-key'")
    print("4. Get Tavily API key at: https://tavily.com")
    print()
    
    # Check environment and run appropriate test
    if os.getenv("TAVILY_API_KEY") and os.getenv("OPENAI_API_KEY"):
        print("Running interactive test...")
        print("You can provide a query or press Enter to use default example")
        asyncio.run(test_context_agent())
    elif os.getenv("TAVILY_API_KEY"):
        print("Running simple test (missing OpenAI key)...")
        asyncio.run(simple_test())
    else:
        print("Missing API keys. Please set TAVILY_API_KEY and OPENAI_API_KEY")
        print("Showing production example code structure only...")
        
        # Show example without running
        print("\nExample usage:")
        print("""
config = ContextAgentConfig(
    tavily_api_key="your-tavily-key",
    llm_provider="openai",
    model_name="gpt-4"
)

agent = ContextAgent(config)
result = await agent.analyze("Your business analysis query here")

if result["success"]:
    # Pass to Protocol Selector Agent
    protocol_input = result["structured_output"]
        """)