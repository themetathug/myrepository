#!/usr/bin/env python3
"""
Test Complete MAPSHOCK LangGraph Workflow
========================================

Tests the complete LangGraph workflow:
User Input → Context Agent → Protocol Selector → Research Agent → LLM → User Interface
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

class MAPSHOCKWorkflowTester:
    """Test the complete MAPSHOCK LangGraph workflow"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
    
    def test_complete_workflow(self):
        """Test the complete workflow with a sample query"""
        
        print("🚀 Testing Complete MAPSHOCK LangGraph Workflow")
        print("=" * 70)
        print("Flow: User Input → Context Agent → Protocol Selector → Research Agent → LLM → User Interface")
        print("Framework: LangChain + LangGraph")
        print("=" * 70)
        
        # Sample user input from Lobe Chat
        user_input = {
            "query": "Analyze competitive threats to LAM Research in the semiconductor equipment market and strategic options for expansion",
            "company": "LAM Research",
            "industry": "Semiconductor Equipment",
            "urgency": "high",
            "analysis_type": "competitive",
            "regions": ["Asia", "North America"],
            "user_context": {
                "market_segment": "Semiconductor Manufacturing Equipment",
                "concerns": ["Chinese competition", "supply chain risks", "market expansion"]
            }
        }
        
        print("📤 STAGE 0: User Input from Lobe Chat")
        print(f"Query: {user_input['query']}")
        print(f"Company: {user_input['company']}")
        print(f"Industry: {user_input['industry']}")
        print(f"Urgency: {user_input['urgency']}")
        print(f"Analysis Type: {user_input['analysis_type']}")
        print()
        
        # Submit to workflow
        try:
            print("📡 Submitting to MAPSHOCK LangGraph Workflow...")
            response = requests.post(
                f"{self.api_url}/api/v1/analyze",
                json=user_input,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                print(f"✅ LangGraph workflow started! Task ID: {task_id}")
                print(f"Status: {result['status']}")
                print(f"Current Stage: {result['current_stage']}")
                print()
                
                # Poll for results and show workflow stages
                self.monitor_workflow_stages(task_id)
                
            else:
                print(f"❌ Workflow submission failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def monitor_workflow_stages(self, task_id: str):
        """Monitor workflow stages in real-time"""
        
        stages = {
            "initializing": "🔄 Initializing LangGraph workflow...",
            "context_analysis": "🔍 STAGE 1: Context Agent (LangGraph) processing user input",
            "protocol_selection": "🛡️ STAGE 2: Protocol Selector (LangGraph) choosing optimal protocols",
            "research_execution": "🧠 STAGE 3: Research Agent (LangGraph) → LLM → Research Agent",
            "formatting_output": "📊 STAGE 4: Research Agent → User Interface formatting",
            "completed": "✅ LANGGRAPH WORKFLOW COMPLETE!",
            "finalized": "✅ LANGGRAPH WORKFLOW COMPLETE!"
        }
        
        print("🔄 Monitoring LangGraph Workflow Stages:")
        print("-" * 60)
        
        max_attempts = 60  # 2 minutes
        attempt = 0
        current_stage = ""
        
        while attempt < max_attempts:
            try:
                response = requests.get(f"{self.api_url}/api/v1/status/{task_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    stage = result.get("current_stage", "unknown")
                    status = result.get("status", "processing")
                    
                    # Show stage update
                    if stage != current_stage:
                        current_stage = stage
                        stage_message = stages.get(stage, f"📋 {stage}")
                        print(f"{stage_message}")
                        
                        if stage in ["completed", "finalized"]:
                            print()
                            self.display_final_results(result)
                            return
                        elif status == "error":
                            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
                            return
                    
                    time.sleep(2)  # Check every 2 seconds
                    attempt += 1
                    
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    return
                    
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                return
        
        print("⏰ Workflow monitoring timeout")
    
    def display_final_results(self, result: Dict[str, Any]):
        """Display final workflow results"""
        
        print("🎉 COMPLETE LANGGRAPH WORKFLOW RESULTS")
        print("=" * 70)
        
        # Basic info
        print(f"Task ID: {result.get('task_id', 'N/A')}")
        total_time = result.get('total_processing_time', result.get('processing_time_seconds', 0))
        print(f"Total Processing Time: {total_time:.2f} seconds")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Framework: LangChain + LangGraph")
        print()
        
        # Workflow Summary
        workflow_summary = result.get("workflow_summary", {})
        print("📊 LANGGRAPH WORKFLOW EXECUTION SUMMARY:")
        print("-" * 50)
        
        context_agent = workflow_summary.get("context_agent", {})
        print(f"Context Agent (LangGraph):")
        print(f"  - Success: {context_agent.get('success', False)}")
        print(f"  - Searches completed: {context_agent.get('searches_completed', 0)}")
        print(f"  - Entities extracted: {len(context_agent.get('entities_extracted', {}))}")
        print(f"  - Confidence score: {context_agent.get('confidence_score', 0):.2f}")
        
        protocol_selector = workflow_summary.get("protocol_selector", {})
        print(f"Protocol Selector (LangGraph):")
        print(f"  - Success: {protocol_selector.get('success', False)}")
        print(f"  - Protocols selected: {protocol_selector.get('protocols_selected', 0)}")
        print(f"  - Selection strategy: {protocol_selector.get('selection_strategy', 'N/A')}")
        print(f"  - Selection confidence: {protocol_selector.get('selection_confidence', 0):.2f}")
        
        research_agent = workflow_summary.get("research_agent", {})
        print(f"Research Agent (LangGraph):")
        print(f"  - Success: {research_agent.get('success', False)}")
        print(f"  - LLM queries executed: {research_agent.get('llm_queries_executed', 0)}")
        print(f"  - Synthesis quality: {research_agent.get('synthesis_quality', 0):.2f}")
        print()
        
        # Protocol Information
        protocols_applied = result.get("protocols_applied", [])
        print(f"🛡️ PROTOCOLS APPLIED ({len(protocols_applied)}):")
        print("-" * 50)
        for i, protocol in enumerate(protocols_applied[:10], 1):  # Show first 10
            print(f"{i:2d}. {protocol}")
        if len(protocols_applied) > 10:
            print(f"... and {len(protocols_applied) - 10} more protocols")
        print()
        
        # Main Results
        results = result.get("results", {})
        
        # Executive Summary
        exec_summary = results.get("executive_summary", {})
        print("📋 EXECUTIVE SUMMARY:")
        print("-" * 50)
        print(f"Company: {exec_summary.get('company', 'N/A')}")
        print(f"Industry: {exec_summary.get('industry', 'N/A')}")
        print(f"Analysis Type: {exec_summary.get('analysis_type', 'N/A')}")
        print(f"Confidence Score: {exec_summary.get('confidence_score', 0):.2%}")
        
        key_findings = exec_summary.get('key_findings', [])
        if key_findings:
            print("\n🔍 KEY FINDINGS:")
            for i, finding in enumerate(key_findings[:5], 1):
                print(f"{i}. {finding}")
        print()
        
        # Detailed Analysis
        detailed = results.get("detailed_analysis", {})
        if detailed:
            print("🔬 DETAILED ANALYSIS SECTIONS:")
            print("-" * 50)
            
            recommendations = detailed.get("strategic_recommendations", [])
            if recommendations:
                print("💡 Strategic Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")
            
            risks = detailed.get("risks_and_threats", [])
            if risks:
                print("\n⚠️ Risks and Threats:")
                for i, risk in enumerate(risks[:3], 1):
                    print(f"  {i}. {risk}")
            
            opportunities = detailed.get("market_opportunities", [])
            if opportunities:
                print("\n🎯 Market Opportunities:")
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"  {i}. {opp}")
        print()
        
        # Data Quality
        data_quality = results.get("data_quality", {})
        print("📊 DATA QUALITY METRICS:")
        print("-" * 50)
        print(f"Source Coverage: {data_quality.get('source_coverage', 0)} sources")
        print(f"Verification Score: {data_quality.get('verification_score', 0):.2f}")
        print(f"Freshness Rating: {data_quality.get('freshness_rating', 'Unknown')}")
        print(f"Confidence Level: {data_quality.get('confidence_level', 'Unknown')}")
        print()
        
        # Processing Summary
        processing_summary = result.get("processing_summary", {})
        print("⚙️ LANGGRAPH PROCESSING SUMMARY:")
        print("-" * 50)
        for stage, status in processing_summary.items():
            if stage not in ["total_processing_time", "stage_times"]:
                print(f"{stage.replace('_', ' ').title()}: {status}")
        
        # Stage timing if available
        stage_times = processing_summary.get("stage_times", {})
        if stage_times:
            print("\n⏱️ Stage Timing:")
            for stage, duration in stage_times.items():
                print(f"  {stage.replace('_', ' ').title()}: {duration:.2f}s")
        
        print()
        
        print("🎯 LANGGRAPH WORKFLOW SUCCESS!")
        print("All 4 stages completed using LangChain + LangGraph framework")
        print("User Input → Context Agent → Protocol Selector → Research Agent → User Interface")
    
    def test_health_check(self):
        """Test system health and workflow readiness"""
        print("❤️ Testing System Health...")
        
        try:
            response = requests.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                health = response.json()
                print("✅ System Health Check Passed")
                print(f"Version: {health.get('version', 'Unknown')}")
                print(f"Framework: {health.get('framework', 'Unknown')}")
                print(f"Workflow: {health.get('workflow', 'Unknown')}")
                print(f"Protocols Available: {health.get('protocols_available', 0)}")
                print(f"Workflow Ready: {health.get('workflow_ready', False)}")
                
                agents_status = health.get('agents_status', {})
                print("\n🤖 LangGraph Agents Status:")
                for agent, status in agents_status.items():
                    status_icon = "✅" if status else "❌"
                    agent_name = agent.replace('_', ' ').title()
                    if agent == "orchestration_agent":
                        agent_name += " (LangGraph)"
                    print(f"  {status_icon} {agent_name}: {'Ready' if status else 'Not Available'}")
                
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

def main():
    """Main test function"""
    print("🚀 MAPSHOCK Complete LangGraph Workflow Test")
    print("=" * 70)
    print("Testing: User Input → Context Agent → Protocol Selector → Research Agent → LLM → User Interface")
    print("Framework: LangChain + LangGraph")
    print("=" * 70)
    
    tester = MAPSHOCKWorkflowTester()
    
    # Test system health first
    if not tester.test_health_check():
        print("❌ System not ready. Please start the MAPSHOCK server first:")
        print("   python -m uvicorn mapshock-MVP.main:app --reload")
        return
    
    print("\n" + "="*70)
    
    # Test complete workflow
    tester.test_complete_workflow()

if __name__ == "__main__":
    main() 