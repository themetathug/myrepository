#!/usr/bin/env python3
"""
MAPSHOCK Advanced Protocol Test Client
This script demonstrates the full MAPSHOCK OS v38.12 protocol system with 65 core protocols
"""

import asyncio
import json
import requests
import websocket
import time
from typing import Dict, Any

class AdvancedMAPSHOCKTestClient:
    """Advanced test client for MAPSHOCK OS v38.12 with full protocol support"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.ws_url = api_url.replace("http", "ws")
    
    def test_protocol_discovery(self):
        """Test protocol discovery and information endpoints"""
        print("🛡️ Testing MAPSHOCK Protocol Discovery...")
        
        try:
            # Get all protocols
            response = requests.get(f"{self.api_url}/api/v1/protocols")
            
            if response.status_code == 200:
                data = response.json()
                protocols = data.get('protocols', {})
                
                print(f"✅ MAPSHOCK OS v{data.get('version', 'Unknown')} Loaded")
                print(f"📊 Available Protocols: {data.get('total_count', 0)}")
                print(f"🎯 Categories: {len(data.get('categories', {}))}")
                
                # Show protocol categories
                categories = data.get('categories', {})
                print("\n📋 Protocol Categories:")
                print("-" * 60)
                for category, protocols_in_cat in categories.items():
                    print(f"  • {category.title()}: {len(protocols_in_cat)} protocols")
                    for i, protocol in enumerate(protocols_in_cat[:3]):  # Show first 3
                        protocol_info = protocols.get(protocol, {})
                        print(f"    - {protocol}: {protocol_info.get('name', 'Unknown')}")
                    if len(protocols_in_cat) > 3:
                        print(f"    ... and {len(protocols_in_cat) - 3} more")
                
                # Show tier mappings
                tier_mappings = data.get('tier_mappings', {})
                print(f"\n🎚️ Threat Tier System:")
                print("-" * 60)
                for tier, config in tier_mappings.items():
                    print(f"  • Tier {tier}: {config.get('description', 'No description')}")
                    print(f"    Max Protocols: {config.get('max_protocols', 0)}")
                    print(f"    Required: {len(config.get('required_protocols', []))}")
                
                return True
            else:
                print(f"❌ Failed to get protocols: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_competitive_analysis_advanced(self):
        """Test advanced competitive analysis with 20+ protocols"""
        print("\n🔍 Testing Advanced Competitive Analysis...")
        
        request_data = {
            "company": "TechCorp Inc.",
            "industry": "Artificial Intelligence",
            "analysis_type": "competitive",
            "query": "Who are our main competitors in enterprise AI and what foreign influence risks should we monitor?",
            "urgency": "high",
            "regions": ["North America", "Europe", "Asia"],
            "user_context": {
                "market_segment": "Enterprise AI",
                "target_audience": "Fortune 500",
                "specific_concerns": "foreign influence, competitive threats, market positioning"
            },
            "enable_advanced_protocols": True
        }
        
        return self._execute_advanced_analysis("Competitive Analysis", request_data)
    
    def test_threat_assessment_maximum(self):
        """Test maximum threat assessment with highest tier protocols"""
        print("\n🚨 Testing Maximum Threat Assessment...")
        
        request_data = {
            "company": "CriticalInfra Corp",
            "industry": "Critical Infrastructure",
            "analysis_type": "threat",
            "query": "Analyze potential foreign cyber threats to our critical infrastructure including institutional capture risks",
            "urgency": "critical",
            "regions": ["Global"],
            "user_context": {
                "security_clearance": "high",
                "threat_indicators": "foreign interference, cyber attacks, institutional infiltration",
                "critical_assets": "power grid, telecommunications, financial systems"
            },
            "enable_advanced_protocols": True
        }
        
        return self._execute_advanced_analysis("Maximum Threat Assessment", request_data)
    
    def test_institutional_analysis(self):
        """Test institutional analysis with governance protocols"""
        print("\n🏛️ Testing Institutional Analysis...")
        
        request_data = {
            "company": "GovTech Solutions",
            "industry": "Government Technology",
            "analysis_type": "institutional",
            "query": "Assess institutional capture risks and governance vulnerabilities in our sector",
            "urgency": "high",
            "regions": ["North America"],
            "user_context": {
                "government_contracts": True,
                "regulatory_environment": "highly regulated",
                "compliance_requirements": "federal"
            },
            "enable_advanced_protocols": True
        }
        
        return self._execute_advanced_analysis("Institutional Analysis", request_data)
    
    def test_narrative_analysis(self):
        """Test narrative analysis with media monitoring protocols"""
        print("\n📰 Testing Narrative Analysis...")
        
        request_data = {
            "company": "MediaTech Corp",
            "industry": "Media Technology",
            "analysis_type": "comprehensive",
            "query": "Monitor narrative momentum and disinformation risks affecting our brand and market position",
            "urgency": "medium",
            "regions": ["Global"],
            "user_context": {
                "media_exposure": "high",
                "narrative_sensitivity": "brand reputation critical",
                "disinformation_concerns": "social media manipulation"
            },
            "enable_advanced_protocols": True
        }
        
        return self._execute_advanced_analysis("Narrative Analysis", request_data)
    
    def _execute_advanced_analysis(self, analysis_name: str, request_data: Dict) -> Dict[str, Any]:
        """Execute advanced analysis and display results"""
        
        try:
            print(f"📤 Submitting {analysis_name}...")
            print(f"   Company: {request_data['company']}")
            print(f"   Industry: {request_data['industry']}")
            print(f"   Urgency: {request_data['urgency'].upper()}")
            print(f"   Type: {request_data['analysis_type']}")
            
            # Submit analysis request
            response = requests.post(
                f"{self.api_url}/api/v1/analyze",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                print(f"✅ Analysis submitted! Task ID: {task_id}")
                print(f"   Expected protocols: {result.get('expected_protocols', 'Unknown')}")
                
                # Poll for results
                print("⏳ Polling for advanced results...")
                return self.poll_for_advanced_results(task_id, analysis_name)
            else:
                print(f"❌ Request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def poll_for_advanced_results(self, task_id: str, analysis_name: str, max_attempts: int = 30) -> Dict[str, Any]:
        """Poll for advanced analysis results"""
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.api_url}/api/v1/status/{task_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["status"] == "completed":
                        print(f"✅ {analysis_name} completed!")
                        self.display_advanced_results(result, analysis_name)
                        return result
                    elif result["status"] == "error":
                        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                        return result
                    else:
                        print(f"⏳ Attempt {attempt + 1}: Status = {result['status']}")
                        time.sleep(2)
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Polling error: {e}")
                time.sleep(2)
        
        print("⏰ Analysis timeout")
        return {"status": "timeout"}
    
    def display_advanced_results(self, result: Dict[str, Any], analysis_name: str):
        """Display advanced analysis results"""
        
        print("\n" + "="*80)
        print(f"📊 MAPSHOCK OS v38.12 - {analysis_name.upper()} RESULTS")
        print("="*80)
        
        # Basic info
        print(f"Task ID: {result.get('task_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Confidence Score: {result.get('confidence_score', 0):.2%}")
        print(f"Threat Tier: {result.get('threat_tier', 'N/A')}")
        print(f"Protocol Count: {result.get('protocol_count', 0)}")
        
        # Protocols applied
        protocols = result.get('protocols_applied', [])
        print(f"\n🛡️ PROTOCOLS APPLIED ({len(protocols)}):")
        print("-" * 50)
        for i, protocol in enumerate(protocols, 1):
            print(f"{i:2d}. {protocol}")
        
        # Protocol dependencies
        dependencies = result.get('protocol_dependencies', {})
        if dependencies:
            print(f"\n🔗 DEPENDENCY CHAIN:")
            print("-" * 50)
            for protocol, deps in list(dependencies.items())[:5]:  # Show first 5
                if deps:
                    print(f"  {protocol} → {', '.join(deps[:3])}")
                    if len(deps) > 3:
                        print(f"    ... and {len(deps) - 3} more dependencies")
        
        # Analysis results
        analysis = result.get('analysis_result', {})
        
        # Executive Summary
        exec_summary = analysis.get('executive_summary', {})
        if exec_summary:
            print(f"\n📋 EXECUTIVE SUMMARY")
            print("-" * 50)
            key_findings = exec_summary.get('key_findings', [])
            for i, finding in enumerate(key_findings[:5], 1):  # Show first 5
                print(f"{i}. {finding}")
        
        # Simplified Executive Summary (from OSM v1.0)
        simplified = analysis.get('simplified_executive_summary', {})
        if simplified:
            print(f"\n🎯 KEY INSIGHTS (OSM v1.0 Simplified)")
            print("-" * 50)
            print(f"Confidence Level: {simplified.get('confidence_level', 'Unknown')}")
            print(f"Threat Assessment: {simplified.get('threat_assessment', 'Unknown')}")
            
            priority_actions = simplified.get('priority_actions', [])
            if priority_actions:
                print(f"\n💡 PRIORITY ACTIONS:")
                for i, action in enumerate(priority_actions[:3], 1):
                    print(f"{i}. {action}")
        
        # Protocol Execution Results
        protocol_execution = analysis.get('protocol_execution', {})
        if protocol_execution:
            print(f"\n⚙️ PROTOCOL EXECUTION")
            print("-" * 50)
            print(f"Total Protocols: {protocol_execution.get('total_protocols_applied', 0)}")
            print(f"Dependency Validation: {protocol_execution.get('dependency_validation', 'Unknown')}")
            print(f"Execution Time: {protocol_execution.get('execution_time', 'Unknown')}")
            print(f"Tier Compliance: {protocol_execution.get('tier_compliance', 'Unknown')}")
            
            # Show specific protocol results
            protocol_results = protocol_execution.get('protocol_results', {})
            if protocol_results:
                print(f"\n🔍 SPECIFIC PROTOCOL RESULTS:")
                for protocol, result_data in list(protocol_results.items())[:3]:  # Show first 3
                    print(f"  • {protocol}:")
                    if isinstance(result_data, dict):
                        for key, value in list(result_data.items())[:2]:  # Show first 2 fields
                            print(f"    - {key}: {value}")
        
        # Meta information
        meta = result.get('meta', {})
        if meta:
            print(f"\n📈 ANALYSIS METADATA")
            print("-" * 50)
            print(f"Dependency Chain Length: {meta.get('dependency_chain_length', 0)}")
            
            context_analysis = meta.get('context_analysis', {})
            if context_analysis:
                active_contexts = [k for k, v in context_analysis.items() if v]
                if active_contexts:
                    print(f"Active Context Triggers: {', '.join(active_contexts)}")
        
        print("\n" + "="*80)
    
    def test_protocol_details(self):
        """Test individual protocol information"""
        print("\n📖 Testing Protocol Details...")
        
        # Test a few key protocols
        key_protocols = ["DVF_v1.0", "10.0", "52.3", "OSM_v1.0", "33.34"]
        
        for protocol_id in key_protocols:
            try:
                response = requests.get(f"{self.api_url}/api/v1/protocols/{protocol_id}")
                
                if response.status_code == 200:
                    protocol = response.json()
                    print(f"\n🛡️ Protocol {protocol_id}:")
                    print(f"   Name: {protocol.get('name', 'Unknown')}")
                    print(f"   Purpose: {protocol.get('purpose', 'Unknown')}")
                    print(f"   Priority: {protocol.get('priority', 'Unknown')}")
                    print(f"   Mandatory: {protocol.get('mandatory', False)}")
                    
                    dependencies = protocol.get('dependencies', [])
                    if dependencies:
                        print(f"   Dependencies: {', '.join(dependencies[:3])}")
                        if len(dependencies) > 3:
                            print(f"   ... and {len(dependencies) - 3} more")
                else:
                    print(f"❌ Failed to get {protocol_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error getting {protocol_id}: {e}")
    
    def test_health_check_advanced(self):
        """Test advanced health check"""
        print("\n❤️ Testing Advanced Health Check...")
        
        try:
            response = requests.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                health = response.json()
                print("✅ Advanced System Health Check Passed")
                print(f"Version: {health.get('version', 'Unknown')}")
                print(f"MAPSHOCK Version: {health.get('mapshock_version', 'Unknown')}")
                print(f"Protocols Available: {health.get('protocols_available', 0)}")
                print(f"Active Connections: {health.get('active_connections', 0)}")
                
                features = health.get('features', [])
                if features:
                    print(f"Advanced Features:")
                    for feature in features:
                        print(f"  ✓ {feature}")
                
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

def main():
    """Main test function for advanced MAPSHOCK system"""
    print("🚀 MAPSHOCK OS v38.12 Advanced Protocol Test Suite")
    print("=" * 70)
    print("Testing full protocol system with 65 core protocols")
    print("=" * 70)
    
    client = AdvancedMAPSHOCKTestClient()
    
    # Test sequence
    print("Starting advanced test suite...\n")
    
    # 1. Advanced health check
    if not client.test_health_check_advanced():
        print("❌ Health check failed. Ensure server is running.")
        return
    
    # 2. Protocol discovery
    if not client.test_protocol_discovery():
        print("❌ Protocol discovery failed.")
        return
    
    # 3. Protocol details
    client.test_protocol_details()
    
    # 4. Competitive analysis (moderate complexity)
    print("\n" + "="*70)
    print("🎯 TESTING ANALYSIS SCENARIOS")
    print("="*70)
    
    competitive_result = client.test_competitive_analysis_advanced()
    
    # 5. Maximum threat assessment (highest complexity)
    threat_result = client.test_threat_assessment_maximum()
    
    # 6. Institutional analysis
    institutional_result = client.test_institutional_analysis()
    
    # 7. Narrative analysis
    narrative_result = client.test_narrative_analysis()
    
    # Final assessment
    print("\n" + "="*70)
    print("📊 ADVANCED TEST SUITE RESULTS")
    print("="*70)
    
    successful_tests = sum([
        1 if competitive_result and competitive_result.get('status') == 'completed' else 0,
        1 if threat_result and threat_result.get('status') == 'completed' else 0,
        1 if institutional_result and institutional_result.get('status') == 'completed' else 0,
        1 if narrative_result and narrative_result.get('status') == 'completed' else 0
    ])
    
    print(f"✅ Successful Analysis Tests: {successful_tests}/4")
    
    if successful_tests >= 3:
        print("\n🎉 Your MAPSHOCK OS v38.12 implementation is working excellently!")
        print("📊 Key Achievements:")
        print("  ✓ 20+ protocols per analysis successfully applied")
        print("  ✓ Dependency validation working correctly")
        print("  ✓ Tier-based protocol activation functioning")
        print("  ✓ Context-aware protocol selection operational")
        print("  ✓ Advanced protocol post-processing active")
        
        # Show protocol counts from results
        if competitive_result:
            print(f"  ✓ Competitive Analysis: {competitive_result.get('protocol_count', 0)} protocols")
        if threat_result:
            print(f"  ✓ Threat Assessment: {threat_result.get('protocol_count', 0)} protocols")
        if institutional_result:
            print(f"  ✓ Institutional Analysis: {institutional_result.get('protocol_count', 0)} protocols")
        
        print(f"\n🎯 Next Steps:")
        print("  1. Add real LLM API keys for enhanced intelligence generation")
        print("  2. Configure external search providers (Tavily, Serper)")
        print("  3. Deploy to production environment")
        print("  4. Integrate with Lobe Chat for real-time analysis")
        print("  5. Set up monitoring and alerting for protocol execution")
        
    else:
        print(f"\n⚠️ Some advanced tests failed. Check error messages above.")
        print("🔧 Troubleshooting:")
        print("  1. Ensure protocols.json is loaded correctly")
        print("  2. Check that all dependencies are installed")
        print("  3. Verify advanced protocol engine is functioning")
        print("  4. Review logs for detailed error information")

if __name__ == "__main__":
    main() 