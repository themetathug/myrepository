#!/usr/bin/env python3
"""
MAPSHOCK Intelligence Platform v3.0 Startup Script
=================================================

LangChain + LangGraph Workflow Implementation
User Input → Context Agent → Protocol Selector → Research Agent → LLM → User Interface
"""

import os
import sys
import subprocess
import time

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for LLM operations",
        "TAVILY_API_KEY": "Tavily API key for search operations (optional)"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append((var, description))
        else:
            # Mask the key for security
            key_value = os.getenv(var)
            masked_key = key_value[:8] + "..." + key_value[-4:] if len(key_value) > 12 else "***"
            print(f"✅ {var}: {masked_key}")
    
    if missing_vars:
        print("\n⚠️ Missing Environment Variables:")
        for var, description in missing_vars:
            print(f"  - {var}: {description}")
        print("\nTo set environment variables:")
        print("  export OPENAI_API_KEY='your-openai-key'")
        print("  export TAVILY_API_KEY='your-tavily-key'")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_server():
    """Start the MAPSHOCK server"""
    print("\n🚀 Starting MAPSHOCK Intelligence Platform v3.0...")
    print("Framework: LangChain + LangGraph")
    print("Workflow: User Input → Context Agent → Protocol Selector → Research Agent → LLM → User Interface")
    print("\nServer will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 80)
    
    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "mapshock-MVP.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")

def run_tests():
    """Run workflow tests"""
    print("\n🧪 Running MAPSHOCK workflow tests...")
    try:
        subprocess.run([sys.executable, "test_complete_workflow.py"])
    except Exception as e:
        print(f"❌ Tests failed: {e}")

def main():
    """Main startup function"""
    print("🚀 MAPSHOCK Intelligence Platform v3.0")
    print("=" * 60)
    print("LangChain + LangGraph Workflow Implementation")
    print("=" * 60)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    print("\n🔍 Checking environment...")
    env_ok = check_environment_variables()
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Install dependencies")
    print("2. Start MAPSHOCK server")
    print("3. Run workflow tests")
    print("4. Full setup (install + start)")
    print("5. Exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            install_dependencies()
        elif choice == "2":
            if not env_ok:
                print("\n⚠️ Environment variables missing. Server may not work properly.")
                proceed = input("Continue anyway? (y/N): ").strip().lower()
                if proceed != 'y':
                    return
            start_server()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            if install_dependencies():
                if not env_ok:
                    print("\n⚠️ Environment variables missing. Server may not work properly.")
                    proceed = input("Continue anyway? (y/N): ").strip().lower()
                    if proceed != 'y':
                        return
                time.sleep(2)
                start_server()
        elif choice == "5":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main() 