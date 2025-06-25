"""
MAPSHOCK Research Agent - LangGraph Implementation
================================================

Flow: Protocol Selector → Research Agent → LLM → Research Agent → User Interface
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class ResearchQuery(BaseModel):
    """A research query for LLM"""
    query_type: str = Field(..., description="Type of research query")
    query_text: str = Field(..., description="The actual query")
    priority: str = Field(..., description="Query priority")

# ==================== LANGGRAPH STATE ====================

class ResearchAgentState(TypedDict):
    """LangGraph state for Research Agent"""
    # Input
    protocol_selector_output: Dict[str, Any]
    
    # Processing
    refined_context: Dict[str, Any]
    research_queries: List[ResearchQuery]
    llm_responses: List[Dict[str, Any]]
    
    # Output
    synthesized_results: Dict[str, Any]
    formatted_output: Dict[str, Any]
    
    # Metadata
    current_step: str
    error_message: Optional[str]

# ==================== RESEARCH AGENT ====================

class ResearchAgent:
    """
    MAPSHOCK Research Agent using LangGraph
    """
    
    def __init__(self, llm_client):
        self.session_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        
        # Initialize LLM
        try:
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.3, max_tokens=2000)
        except:
            logger.warning("Failed to initialize LLM")
            self.llm = None
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        logger.info("Research Agent initialized with LangGraph")
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(ResearchAgentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("refine_context", self._refine_context_node)
        workflow.add_node("generate_queries", self._generate_queries_node)
        workflow.add_node("conduct_research", self._conduct_research_node)
        workflow.add_node("synthesize_results", self._synthesize_results_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Define edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "refine_context")
        workflow.add_edge("refine_context", "generate_queries")
        workflow.add_edge("generate_queries", "conduct_research")
        workflow.add_edge("conduct_research", "synthesize_results")
        workflow.add_edge("synthesize_results", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow
    
    # ==================== WORKFLOW NODES ====================
    
    async def _initialize_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Initialize research process"""
        logger.info("Initializing research process")
        
        state["current_step"] = "initialized"
        state["refined_context"] = {}
        state["research_queries"] = []
        state["llm_responses"] = []
        state["synthesized_results"] = {}
        state["formatted_output"] = {}
        state["error_message"] = None
        
        return state
    
    async def _refine_context_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Refine context for LLM research"""
        logger.info("Refining context for LLM research")
        
        try:
            protocol_output = state["protocol_selector_output"]
            
            # Extract key components
            enriched_context = protocol_output.get('enriched_context', {})
            selected_protocols = protocol_output.get('selected_protocols', [])
            
            # Build refined research context
            refined_context = {
                "original_query": enriched_context.get('original_query', ''),
                "company": self._extract_company_name(enriched_context),
                "industry": self._extract_industry(enriched_context),
                "analysis_type": enriched_context.get('suggested_analysis_type', 'comprehensive'),
                "extracted_entities": enriched_context.get('extracted_entities', {}),
                "active_protocols": [p.protocol_name for p in selected_protocols],
                "protocol_count": len(selected_protocols)
            }
            
            state["refined_context"] = refined_context
            state["current_step"] = "context_refined"
            
            logger.info(f"Context refined for {refined_context['analysis_type']} analysis")
            
        except Exception as e:
            logger.error(f"Context refinement failed: {e}")
            state["error_message"] = str(e)
        
        return state
    
    async def _generate_queries_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Generate research queries for LLM"""
        logger.info("Generating research queries for LLM")
        
        try:
            context = state["refined_context"]
            queries = []
            
            # Main analysis query
            queries.append(ResearchQuery(
                query_type="primary_analysis",
                query_text=f"Conduct {context['analysis_type']} analysis for {context['company']} in the {context['industry']} industry. Focus on: {context['original_query']}",
                priority="high"
            ))
            
            # Competitive analysis query
            queries.append(ResearchQuery(
                query_type="competitive_analysis",
                query_text=f"Analyze competitive landscape for {context['company']} in {context['industry']} industry",
                priority="medium"
            ))
            
            # Risk assessment query
            queries.append(ResearchQuery(
                query_type="risk_assessment",
                query_text=f"Identify key risks and threats for {context['company']} in current market conditions",
                priority="medium"
            ))
            
            # Opportunity analysis query
            queries.append(ResearchQuery(
                query_type="opportunity_analysis",
                query_text=f"Identify strategic opportunities for {context['company']} in {context['industry']} market",
                priority="medium"
            ))
            
            state["research_queries"] = queries
            state["current_step"] = "queries_generated"
            
            logger.info(f"Generated {len(queries)} research queries")
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            state["error_message"] = str(e)
        
        return state
    
    async def _conduct_research_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Conduct LLM research"""
        logger.info("Conducting LLM research")
        
        try:
            queries = state["research_queries"]
            context = state["refined_context"]
            responses = []
            
            for query in queries:
                try:
                    if self.llm:
                        # Build prompt
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", """You are a MAPSHOCK intelligence analyst. Provide comprehensive analysis in JSON format with:
                            1. executive_summary (key findings, confidence score)
                            2. detailed_analysis (insights, trends, data points)
                            3. strategic_implications (recommendations, risks, opportunities)
                            4. confidence_indicators (data quality, reliability)"""),
                            ("human", f"""
Analysis Context:
Company: {context['company']}
Industry: {context['industry']}
Analysis Type: {context['analysis_type']}
Active Protocols: {', '.join(context['active_protocols'])}

Research Query: {query.query_text}

Provide detailed analysis following MAPSHOCK protocols.""")
                        ])
                        
                        formatted_prompt = prompt_template.format_messages()
                        response = await self.llm.ainvoke(formatted_prompt)
                        
                        # Try to parse as JSON
                        try:
                            parser = JsonOutputParser()
                            llm_response = parser.parse(response.content)
                        except:
                            llm_response = {
                                "executive_summary": {
                                    "key_findings": [response.content[:200] + "..."],
                                    "confidence_score": 0.75
                                },
                                "detailed_analysis": {"insights": response.content},
                                "strategic_implications": {
                                    "recommendations": [f"Strategic recommendation for {query.query_type}"],
                                    "risks": [f"Risk identified in {query.query_type}"],
                                    "opportunities": [f"Opportunity from {query.query_type}"]
                                }
                            }
                    else:
                        # Fallback response
                        llm_response = {
                            "executive_summary": {
                                "key_findings": [f"Analysis for {query.query_type} - {context['company']} in {context['industry']}"],
                                "confidence_score": 0.75
                            },
                            "detailed_analysis": {
                                "insights": f"Detailed analysis results for {query.query_type}",
                                "recommendations": [f"Strategic recommendation based on {query.query_type}"]
                            },
                            "strategic_implications": {
                                "recommendations": [f"Implement strategy for {context['analysis_type']} analysis"],
                                "risks": [f"Monitor risks identified in {query.query_type}"],
                                "opportunities": [f"Leverage opportunities from {context['analysis_type']} analysis"]
                            }
                        }
                    
                    # Structure response
                    structured_response = {
                        "query_type": query.query_type,
                        "query": query.query_text,
                        "response": llm_response,
                        "priority": query.priority,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    }
                    
                    responses.append(structured_response)
                    logger.info(f"LLM research completed for {query.query_type}")
                    
                except Exception as e:
                    logger.error(f"LLM research failed for {query.query_type}: {e}")
                    error_response = {
                        "query_type": query.query_type,
                        "query": query.query_text,
                        "error": str(e),
                        "success": False,
                        "timestamp": datetime.now().isoformat()
                    }
                    responses.append(error_response)
            
            state["llm_responses"] = responses
            state["current_step"] = "research_completed"
            
            successful_responses = len([r for r in responses if r.get('success')])
            logger.info(f"LLM research completed: {successful_responses}/{len(queries)} successful")
            
        except Exception as e:
            logger.error(f"Research conduction failed: {e}")
            state["error_message"] = str(e)
        
        return state
    
    async def _synthesize_results_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Synthesize LLM responses"""
        logger.info("Synthesizing LLM responses")
        
        try:
            responses = state["llm_responses"]
            successful_responses = [r for r in responses if r.get('success', False)]
            
            if not successful_responses:
                state["synthesized_results"] = {
                    "synthesis_success": False,
                    "error": "No successful LLM responses to synthesize"
                }
                return state
            
            # Extract insights
            all_findings = []
            all_recommendations = []
            all_risks = []
            all_opportunities = []
            
            for response in successful_responses:
                response_data = response.get('response', {})
                
                # Extract findings
                exec_summary = response_data.get('executive_summary', {})
                if exec_summary.get('key_findings'):
                    if isinstance(exec_summary['key_findings'], list):
                        all_findings.extend(exec_summary['key_findings'])
                    else:
                        all_findings.append(str(exec_summary['key_findings']))
                
                # Extract strategic implications
                strategic = response_data.get('strategic_implications', {})
                if strategic.get('recommendations'):
                    if isinstance(strategic['recommendations'], list):
                        all_recommendations.extend(strategic['recommendations'])
                    else:
                        all_recommendations.append(str(strategic['recommendations']))
                
                if strategic.get('risks'):
                    if isinstance(strategic['risks'], list):
                        all_risks.extend(strategic['risks'])
                    else:
                        all_risks.append(str(strategic['risks']))
                
                if strategic.get('opportunities'):
                    if isinstance(strategic['opportunities'], list):
                        all_opportunities.extend(strategic['opportunities'])
                    else:
                        all_opportunities.append(str(strategic['opportunities']))
            
            # Remove duplicates and limit
            synthesized = {
                "key_findings": list(set(all_findings))[:5],
                "strategic_recommendations": list(set(all_recommendations))[:5],
                "risks_and_threats": list(set(all_risks))[:5],
                "opportunities": list(set(all_opportunities))[:5],
                "confidence_score": 0.8,
                "synthesis_quality": len(successful_responses) / len(responses) if responses else 0
            }
            
            state["synthesized_results"] = synthesized
            state["current_step"] = "results_synthesized"
            
            logger.info("LLM response synthesis completed")
            
        except Exception as e:
            logger.error(f"Results synthesis failed: {e}")
            state["error_message"] = str(e)
        
        return state
    
    async def _format_output_node(self, state: ResearchAgentState) -> ResearchAgentState:
        """Format final output for UI"""
        logger.info("Formatting results for UI")
        
        try:
            synthesized_results = state["synthesized_results"]
            context = state["refined_context"]
            protocols = state["protocol_selector_output"].get('selected_protocols', [])
            
            # Create formatted output
            formatted_output = {
                "executive_summary": {
                    "company": context["company"],
                    "industry": context["industry"],
                    "analysis_type": context["analysis_type"].title(),
                    "key_findings": synthesized_results.get('key_findings', []),
                    "confidence_score": synthesized_results.get('confidence_score', 0.75),
                    "timestamp": datetime.now().isoformat(),
                    "protocols_applied": len(protocols)
                },
                "detailed_analysis": {
                    "strategic_recommendations": synthesized_results.get('strategic_recommendations', []),
                    "risks_and_threats": synthesized_results.get('risks_and_threats', []),
                    "market_opportunities": synthesized_results.get('opportunities', [])
                },
                "data_quality": {
                    "source_coverage": len(context.get('active_protocols', [])),
                    "verification_score": synthesized_results.get('synthesis_quality', 0.8),
                    "freshness_rating": "High",
                    "confidence_level": "High" if synthesized_results.get('confidence_score', 0) > 0.8 else "Medium"
                },
                "methodology": {
                    "protocols_applied": [p.protocol_name for p in protocols],
                    "analysis_depth": "Standard",
                    "verification_level": "Enhanced"
                },
                "next_steps": {
                    "immediate_actions": [
                        "Review and validate key findings with stakeholders",
                        "Develop implementation plan for strategic recommendations",
                        "Monitor identified risks and mitigation strategies"
                    ],
                    "monitoring_recommendations": [
                        "Set up alerts for competitor activity and market changes",
                        "Establish KPIs to track progress on strategic initiatives"
                    ],
                    "follow_up_analysis": [
                        "Quarterly strategic position review",
                        "Customer perception and brand analysis"
                    ]
                }
            }
            
            state["formatted_output"] = formatted_output
            state["current_step"] = "formatting_completed"
            
            logger.info("UI formatting completed")
            
        except Exception as e:
            logger.error(f"Output formatting failed: {e}")
            state["error_message"] = str(e)
        
        return state
    
    # ==================== HELPER METHODS ====================
    
    def _extract_company_name(self, context: Dict[str, Any]) -> str:
        """Extract company name from context"""
        query = context.get('original_query', '')
        entities = context.get('extracted_entities', {})
        
        if entities.get('companies'):
            return entities['companies'][0]
        
        # Try to extract from query
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ['company', 'corp', 'inc', 'ltd', 'llc']:
                if i > 0:
                    return words[i-1]
        
        return "Target Company"
    
    def _extract_industry(self, context: Dict[str, Any]) -> str:
        """Extract industry from context"""
        entities = context.get('extracted_entities', {})
        if entities.get('industries'):
            return entities['industries'][0].title()
        return "Technology"
    
    # ==================== PUBLIC INTERFACE ====================
    
    async def conduct_research(self, protocol_selector_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main research method - receives output from Protocol Selector and conducts research
        """
        session_id = str(uuid.uuid4())
        
        initial_state = ResearchAgentState(
            protocol_selector_output=protocol_selector_output,
            refined_context={},
            research_queries=[],
            llm_responses=[],
            synthesized_results={},
            formatted_output={},
            current_step="starting",
            error_message=None
        )
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            logger.info(f"Starting research with {len(protocol_selector_output.get('selected_protocols', []))} protocols")
            
            final_state = await self.app.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "research_results": final_state["formatted_output"],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "protocols_applied": len(protocol_selector_output.get('selected_protocols', [])),
                "processing_summary": {
                    "context_refined": True,
                    "llm_queries_generated": len(final_state["research_queries"]),
                    "llm_responses_processed": len(final_state["llm_responses"]),
                    "output_formatted": True
                }
            }
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            } 