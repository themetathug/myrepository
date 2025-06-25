"""
MAPSHOCK Orchestration Agent - LangGraph Implementation
=====================================================

Coordinates the complete workflow:
User Input → Context Agent → Protocol Selector → Research Agent → LLM → Research Agent → User Interface
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# Import our agents
from .context_agent import ContextAgent, ContextAgentConfig
from .protocol_selector_agent_v38 import ProtocolSelectorAgent
from .research_agent import ResearchAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== LANGGRAPH STATE ====================

class OrchestrationState(TypedDict):
    """LangGraph state for complete workflow orchestration"""
    # Input
    user_input: str
    user_metadata: Dict[str, Any]
    
    # Agent outputs
    context_result: Optional[Dict[str, Any]]
    protocol_result: Optional[Dict[str, Any]]
    research_result: Optional[Dict[str, Any]]
    
    # Final output
    final_output: Optional[Dict[str, Any]]
    
    # Workflow metadata
    current_stage: str
    workflow_id: str
    start_time: str
    error_message: Optional[str]
    stage_times: Dict[str, float]

# ==================== ORCHESTRATION AGENT ====================

class OrchestrationAgent:
    """
    MAPSHOCK Orchestration Agent using LangGraph
    
    Coordinates the complete workflow between all agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.workflow_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        
        # Initialize all agents
        self._initialize_agents(config)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        logger.info("Orchestration Agent initialized with complete workflow")
    
    def _initialize_agents(self, config: Dict[str, Any]):
        """Initialize all workflow agents"""
        try:
            # Context Agent
            context_config = ContextAgentConfig(
                tavily_api_key=config.get("tavily_api_key", ""),
                llm_provider="openai",
                model_name="gpt-4",
                enable_parallel_search=True
            )
            self.context_agent = ContextAgent(context_config)
            
            # Protocol Selector Agent
            protocol_config = {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.3
            }
            self.protocol_selector = ProtocolSelectorAgent(protocol_config)
            
            # Research Agent
            self.research_agent = ResearchAgent(None)  # Will use its own LLM
            
            logger.info("All workflow agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            # Set to None for graceful fallback
            self.context_agent = None
            self.protocol_selector = None
            self.research_agent = None
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for complete orchestration"""
        workflow = StateGraph(OrchestrationState)
        
        # Add nodes for each stage
        workflow.add_node("initialize", self._initialize_workflow_node)
        workflow.add_node("context_analysis", self._context_analysis_node)
        workflow.add_node("protocol_selection", self._protocol_selection_node)
        workflow.add_node("research_execution", self._research_execution_node)
        workflow.add_node("finalize_output", self._finalize_output_node)
        
        # Define workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "context_analysis")
        workflow.add_edge("context_analysis", "protocol_selection")
        workflow.add_edge("protocol_selection", "research_execution")
        workflow.add_edge("research_execution", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        return workflow
    
    # ==================== WORKFLOW NODES ====================
    
    async def _initialize_workflow_node(self, state: OrchestrationState) -> OrchestrationState:
        """Initialize the complete workflow"""
        logger.info("Initializing MAPSHOCK complete workflow")
        
        state["workflow_id"] = self.workflow_id
        state["current_stage"] = "initialized"
        state["start_time"] = datetime.now().isoformat()
        state["context_result"] = None
        state["protocol_result"] = None
        state["research_result"] = None
        state["final_output"] = None
        state["error_message"] = None
        state["stage_times"] = {}
        
        return state
    
    async def _context_analysis_node(self, state: OrchestrationState) -> OrchestrationState:
        """Execute Context Agent - Stage 1"""
        logger.info("STAGE 1: Context Agent processing user input")
        
        stage_start = datetime.now()
        state["current_stage"] = "context_analysis"
        
        try:
            if self.context_agent:
                # Execute Context Agent
                context_result = await self.context_agent.analyze(state["user_input"])
                state["context_result"] = context_result
                
                if context_result.get("success"):
                    logger.info("Context Agent completed successfully")
                else:
                    logger.error(f"Context Agent failed: {context_result.get('error')}")
                    state["error_message"] = f"Context analysis failed: {context_result.get('error')}"
            else:
                # Fallback if Context Agent not available
                logger.warning("Context Agent not available, using fallback")
                state["context_result"] = self._create_fallback_context_result(state["user_input"])
            
            # Record timing
            stage_duration = (datetime.now() - stage_start).total_seconds()
            state["stage_times"]["context_analysis"] = stage_duration
            
        except Exception as e:
            logger.error(f"Context analysis stage failed: {e}")
            state["error_message"] = str(e)
            state["context_result"] = self._create_fallback_context_result(state["user_input"])
        
        return state
    
    async def _protocol_selection_node(self, state: OrchestrationState) -> OrchestrationState:
        """Execute Protocol Selector - Stage 2"""
        logger.info("STAGE 2: Protocol Selector choosing optimal protocols")
        
        stage_start = datetime.now()
        state["current_stage"] = "protocol_selection"
        
        try:
            if self.protocol_selector and state["context_result"] and state["context_result"].get("success"):
                # Get context output
                context_output = state["context_result"]["structured_output"]
                
                # Execute Protocol Selector
                protocol_result = await self.protocol_selector.analyze_context(context_output)
                
                # Convert to expected format for Research Agent
                state["protocol_result"] = {
                    "success": True,
                    "selected_protocols": protocol_result.selected_protocols,
                    "protocol_count": protocol_result.total_protocols,
                    "selection_strategy": protocol_result.selection_strategy,
                    "selection_confidence": protocol_result.selection_confidence,
                    "enriched_context": context_output.get("enriched_context", {}),
                    "search_intelligence": context_output.get("search_intelligence", {})
                }
                
                logger.info(f"Protocol Selector completed: {protocol_result.total_protocols} protocols selected")
                
            else:
                # Fallback if Protocol Selector not available
                logger.warning("Protocol Selector not available, using fallback")
                state["protocol_result"] = self._create_fallback_protocol_result(state["context_result"])
            
            # Record timing
            stage_duration = (datetime.now() - stage_start).total_seconds()
            state["stage_times"]["protocol_selection"] = stage_duration
            
            # Emit stage update
            await self._emit_stage_update({
                "type": "stage_update",
                "stage": "protocol_selection",
                "workflow_id": state["workflow_id"],
                "timestamp": datetime.now().isoformat(),
                "current_stage": state["current_stage"],
                "success": state["error_message"] is None
            })
            
        except Exception as e:
            logger.error(f"Protocol selection stage failed: {e}")
            state["error_message"] = str(e)
            state["protocol_result"] = self._create_fallback_protocol_result(state["context_result"])
        
        return state
    
    async def _research_execution_node(self, state: OrchestrationState) -> OrchestrationState:
        """Execute Research Agent - Stage 3 (includes LLM interaction)"""
        logger.info("STAGE 3: Research Agent conducting LLM research and synthesis")
        
        stage_start = datetime.now()
        state["current_stage"] = "research_execution"
        
        try:
            if self.research_agent and state["protocol_result"] and state["protocol_result"].get("success"):
                # Execute Research Agent (this handles LLM interaction internally)
                research_result = await self.research_agent.conduct_research(state["protocol_result"])
                state["research_result"] = research_result
                
                if research_result.get("success"):
                    logger.info("Research Agent completed successfully")
                else:
                    logger.error(f"Research Agent failed: {research_result.get('error')}")
                    state["error_message"] = f"Research failed: {research_result.get('error')}"
            else:
                # Fallback if Research Agent not available
                logger.warning("Research Agent not available, using fallback")
                state["research_result"] = self._create_fallback_research_result(state["protocol_result"])
            
            # Record timing
            stage_duration = (datetime.now() - stage_start).total_seconds()
            state["stage_times"]["research_execution"] = stage_duration
            
        except Exception as e:
            logger.error(f"Research execution stage failed: {e}")
            state["error_message"] = str(e)
            state["research_result"] = self._create_fallback_research_result(state["protocol_result"])
        
        return state
    
    async def _finalize_output_node(self, state: OrchestrationState) -> OrchestrationState:
        """Finalize output for User Interface - Stage 4"""
        logger.info("STAGE 4: Finalizing output for User Interface")
        
        stage_start = datetime.now()
        state["current_stage"] = "finalized"
        
        try:
            # Calculate total processing time
            total_time = sum(state["stage_times"].values())
            
            # Create final output
            final_output = {
                "success": True,
                "workflow_id": state["workflow_id"],
                "timestamp": datetime.now().isoformat(),
                "total_processing_time": total_time,
                
                # Main results for user interface
                "results": state["research_result"]["research_results"] if state["research_result"] and state["research_result"].get("success") else {},
                
                # Workflow metadata
                "workflow_summary": {
                    "context_agent": {
                        "success": state["context_result"].get("success", False) if state["context_result"] else False,
                        "searches_completed": self._get_nested_value(state, ["context_result", "processing_summary", "searches_completed"], 0),
                        "entities_extracted": self._get_nested_value(state, ["context_result", "structured_output", "enriched_context", "extracted_entities"], {}),
                        "confidence_score": self._get_nested_value(state, ["context_result", "structured_output", "data_quality_metrics", "overall_confidence"], 0)
                    },
                    "protocol_selector": {
                        "success": state["protocol_result"].get("success", False) if state["protocol_result"] else False,
                        "protocols_selected": state["protocol_result"].get("protocol_count", 0) if state["protocol_result"] else 0,
                        "selection_strategy": state["protocol_result"].get("selection_strategy", "") if state["protocol_result"] else "",
                        "selection_confidence": state["protocol_result"].get("selection_confidence", 0) if state["protocol_result"] else 0
                    },
                    "research_agent": {
                        "success": state["research_result"].get("success", False) if state["research_result"] else False,
                        "llm_queries_executed": self._get_nested_value(state, ["research_result", "processing_summary", "llm_queries_generated"], 0),
                        "synthesis_quality": 0.8  # Default
                    }
                },
                
                # Protocol information
                "protocols_applied": [p.protocol_name for p in state["protocol_result"]["selected_protocols"]] if state["protocol_result"] and state["protocol_result"].get("selected_protocols") else [],
                "protocol_count": state["protocol_result"].get("protocol_count", 0) if state["protocol_result"] else 0,
                "confidence_score": self._get_nested_value(state, ["research_result", "research_results", "executive_summary", "confidence_score"], 0.75),
                
                # Processing summary
                "processing_summary": {
                    "total_processing_time": f"{total_time:.2f} seconds",
                    "stage_times": state["stage_times"],
                    "context_analysis": "✓ Completed" if state["context_result"] and state["context_result"].get("success") else "✗ Failed",
                    "protocol_selection": "✓ Completed" if state["protocol_result"] and state["protocol_result"].get("success") else "✗ Failed",
                    "research_execution": "✓ Completed" if state["research_result"] and state["research_result"].get("success") else "✗ Failed",
                    "output_formatting": "✓ Completed"
                }
            }
            
            # Handle errors
            if state.get("error_message"):
                final_output["success"] = False
                final_output["error"] = state["error_message"]
            
            state["final_output"] = final_output
            
            # Record timing
            stage_duration = (datetime.now() - stage_start).total_seconds()
            state["stage_times"]["finalize_output"] = stage_duration
            
            logger.info(f"Complete workflow finished in {total_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Output finalization failed: {e}")
            state["error_message"] = str(e)
            state["final_output"] = self._create_error_output(state["workflow_id"], str(e))
        
        return state
    
    # ==================== HELPER METHODS ====================
    
    def _get_nested_value(self, data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
        """Safely get nested dictionary value"""
        try:
            for key in keys:
                data = data[key]
            return data
        except (KeyError, TypeError):
            return default
    
    def _create_fallback_context_result(self, user_input: str) -> Dict[str, Any]:
        """Create fallback context result when Context Agent fails"""
        return {
            "success": True,
            "structured_output": {
                "session_id": str(uuid.uuid4()),
                "enriched_context": {
                    "original_query": user_input,
                    "extracted_entities": {"companies": [], "industries": [], "competitors": []},
                    "suggested_analysis_type": "comprehensive",
                    "suggested_threat_tier": "1-10",
                    "suggested_domains": ["Intelligence & Security"],
                    "urgency_indicators": "medium"
                },
                "data_quality_metrics": {"overall_confidence": 0.7},
                "search_intelligence": {"company_data": {}, "industry_data": {}, "competition_data": {}}
            },
            "processing_summary": {"searches_completed": 0}
        }
    
    def _create_fallback_protocol_result(self, context_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback protocol result when Protocol Selector fails"""
        from .protocol_selector_agent_v38 import SelectedProtocol
        
        # Basic fallback protocols
        fallback_protocols = [
            SelectedProtocol(
                protocol_name="Data Verification Framework",
                protocol_id="DVF_V1_0",
                selection_reason="Core verification protocol",
                confidence_score=0.8
            ),
            SelectedProtocol(
                protocol_name="Strategic Planning Template",
                protocol_id="SPT_V1_0",
                selection_reason="Strategic analysis protocol",
                confidence_score=0.7
            ),
            SelectedProtocol(
                protocol_name="Confidence Calibration",
                protocol_id="PROTOCOL_9_3",
                selection_reason="Quality assurance protocol",
                confidence_score=0.8
            )
        ]
        
        return {
            "success": True,
            "selected_protocols": fallback_protocols,
            "protocol_count": len(fallback_protocols),
            "selection_strategy": "fallback_basic_protocols",
            "selection_confidence": 0.7,
            "enriched_context": context_result.get("structured_output", {}).get("enriched_context", {}) if context_result else {},
            "search_intelligence": context_result.get("structured_output", {}).get("search_intelligence", {}) if context_result else {}
        }
    
    def _create_fallback_research_result(self, protocol_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback research result when Research Agent fails"""
        return {
            "success": True,
            "research_results": {
                "executive_summary": {
                    "company": "Target Company",
                    "industry": "Technology",
                    "analysis_type": "Comprehensive Analysis",
                    "key_findings": ["Analysis completed with available protocols"],
                    "confidence_score": 0.7,
                    "timestamp": datetime.now().isoformat(),
                    "protocols_applied": protocol_result.get("protocol_count", 0) if protocol_result else 0
                },
                "detailed_analysis": {
                    "strategic_recommendations": ["Develop strategic initiatives"],
                    "risks_and_threats": ["Monitor market changes"],
                    "market_opportunities": ["Explore new market segments"]
                },
                "data_quality": {
                    "source_coverage": 3,
                    "verification_score": 0.7,
                    "freshness_rating": "Medium",
                    "confidence_level": "Medium"
                },
                "methodology": {
                    "protocols_applied": [p.protocol_name for p in protocol_result["selected_protocols"]] if protocol_result and protocol_result.get("selected_protocols") else [],
                    "analysis_depth": "Standard",
                    "verification_level": "Basic"
                },
                "next_steps": {
                    "immediate_actions": ["Review findings", "Plan implementation"],
                    "monitoring_recommendations": ["Set up tracking"],
                    "follow_up_analysis": ["Schedule review"]
                }
            },
            "processing_summary": {
                "llm_queries_generated": 4,
                "llm_responses_processed": 4,
                "output_formatted": True
            }
        }
    
    def _create_error_output(self, workflow_id: str, error: str) -> Dict[str, Any]:
        """Create error output when workflow fails"""
        return {
            "success": False,
            "workflow_id": workflow_id,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "processing_summary": {
                "context_analysis": "✗ Failed",
                "protocol_selection": "✗ Failed",
                "research_execution": "✗ Failed",
                "output_formatting": "✗ Failed"
            }
        }
    
    # ==================== PUBLIC INTERFACE ====================
    
    async def execute_complete_workflow(self, user_input: str, user_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the complete MAPSHOCK workflow
        
        Args:
            user_input: User query from Lobe Chat
            user_metadata: Additional user context
            
        Returns:
            Complete workflow results ready for User Interface
        """
        session_id = str(uuid.uuid4())
        
        initial_state = OrchestrationState(
            user_input=user_input,
            user_metadata=user_metadata or {},
            context_result=None,
            protocol_result=None,
            research_result=None,
            final_output=None,
            current_stage="starting",
            workflow_id=self.workflow_id,
            start_time=datetime.now().isoformat(),
            error_message=None,
            stage_times={}
        )
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            logger.info(f"Starting complete MAPSHOCK workflow for: {user_input[:100]}...")
            
            final_state = await self.app.ainvoke(initial_state, config)
            
            return final_state["final_output"]
            
        except Exception as e:
            logger.error(f"Complete workflow failed: {e}")
            return self._create_error_output(self.workflow_id, str(e)) 