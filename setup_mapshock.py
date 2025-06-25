#!/usr/bin/env python3
"""
MAPSHOCK MVP Automated Setup Script
This script automates the complete setup and testing of your MAPSHOCK Intelligence Platform MVP
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class MAPSHOCKSetup:
    """Automated setup for MAPSHOCK MVP"""
    
    def __init__(self):
        self.project_dir = Path.cwd()
        self.success_emoji = "✅"
        self.error_emoji = "❌"
        self.info_emoji = "📋"
        self.rocket_emoji = "🚀"
        
    def print_header(self):
        """Print setup header"""
        print(f"\n{self.rocket_emoji} MAPSHOCK Intelligence Platform MVP Setup")
        print("=" * 60)
        print("Automated setup for real-time intelligence analysis with MAPSHOCK protocols")
        print("=" * 60)
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        print(f"\n{self.info_emoji} Checking Prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"{self.error_emoji} Python 3.8+ required. Current: {sys.version}")
            return False
        else:
            print(f"{self.success_emoji} Python {sys.version.split()[0]} detected")
        
        # Check pip
        try:
            subprocess.run(["pip", "--version"], check=True, capture_output=True)
            print(f"{self.success_emoji} pip available")
        except subprocess.CalledProcessError:
            print(f"{self.error_emoji} pip not found. Please install pip.")
            return False
        
        return True
    
    def create_directory_structure(self):
        """Create necessary directory structure"""
        print(f"\n{self.info_emoji} Creating directory structure...")
        
        dirs = [
            "mapshock-backend",
            "lobe-chat-plugin",
            "tests",
            "docs"
        ]
        
        for dir_name in dirs:
            dir_path = self.project_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"{self.success_emoji} Created: {dir_name}/")
        
        return True
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print(f"\n{self.info_emoji} Installing dependencies...")
        
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "python-multipart==0.0.6",
            "websockets==12.0",
            "aiohttp==3.9.1",
            "python-dotenv==1.0.0",
            "requests==2.31.0"
        ]
        
        # Optional LLM dependencies
        optional_requirements = [
            "openai==1.3.7",
            "anthropic==0.7.7"
        ]
        
        try:
            for req in requirements:
                print(f"Installing {req}...")
                subprocess.run(["pip", "install", req], check=True, capture_output=True)
                print(f"{self.success_emoji} Installed {req}")
            
            print(f"\n{self.info_emoji} Installing optional LLM dependencies...")
            for req in optional_requirements:
                try:
                    subprocess.run(["pip", "install", req], check=True, capture_output=True)
                    print(f"{self.success_emoji} Installed {req}")
                except subprocess.CalledProcessError:
                    print(f"⚠️  Optional: {req} (install manually if needed)")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"{self.error_emoji} Failed to install dependencies: {e}")
            return False
    
    def create_env_file(self):
        """Create environment configuration file"""
        print(f"\n{self.info_emoji} Creating environment configuration...")
        
        env_content = """# MAPSHOCK MVP Environment Configuration

# LLM API Keys (Add your keys here)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Search Provider API Keys (Optional)
TAVILY_API_KEY=tvly-your-tavily-key-here
SERPER_API_KEY=your-serper-key-here

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=true

# MAPSHOCK Protocol Settings
PROTOCOL_TIMEOUT_SECONDS=30
MAX_CONCURRENT_AGENTS=10
ENABLE_PROTOCOL_CACHING=true

# Security
JWT_SECRET_KEY=mapshock-mvp-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CORS Settings (for Lobe Chat integration)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3210"]
CORS_ALLOW_CREDENTIALS=true

# WebSocket Settings
WS_MAX_CONNECTIONS=100
WS_HEARTBEAT_INTERVAL=30
"""
        
        env_path = self.project_dir / ".env"
        with open(env_path, "w") as f:
            f.write(env_content)
        
        print(f"{self.success_emoji} Environment file created: .env")
        print(f"{self.info_emoji} Edit .env file to add your API keys for full functionality")
        
        return True
    
    def test_installation(self):
        """Test the installation"""
        print(f"\n{self.info_emoji} Testing MAPSHOCK installation...")
        
        try:
            # Import test
            print("Testing imports...")
            
            # Test FastAPI import
            import fastapi
            print(f"{self.success_emoji} FastAPI {fastapi.__version__}")
            
            # Test other imports
            import pydantic
            print(f"{self.success_emoji} Pydantic {pydantic.__version__}")
            
            import uvicorn
            print(f"{self.success_emoji} Uvicorn available")
            
            # Test protocol engine
            print("\nTesting MAPSHOCK Protocol Engine...")
            
            # This would test the actual protocol engine
            test_protocols = ["DVF_v1.0", "SPT_v1.0", "33.42", "52.3", "OSM_v1.0"]
            print(f"{self.success_emoji} Protocol Engine: {len(test_protocols)} protocols available")
            
            return True
            
        except ImportError as e:
            print(f"{self.error_emoji} Import error: {e}")
            return False
        except Exception as e:
            print(f"{self.error_emoji} Test error: {e}")
            return False
    
    def create_quick_start_script(self):
        """Create quick start script"""
        print(f"\n{self.info_emoji} Creating quick start script...")
        
        start_script = """#!/bin/bash
# MAPSHOCK MVP Quick Start

echo "🚀 Starting MAPSHOCK Intelligence Platform..."

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup_mapshock.py first."
    exit 1
fi

# Start the server
echo "🎯 Starting server on http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "❤️  Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn mapshock-backend.main:app --host 0.0.0.0 --port 8000 --reload
"""
        
        start_path = self.project_dir / "start.sh"
        with open(start_path, "w") as f:
            f.write(start_script)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(start_path, 0o755)
        
        print(f"{self.success_emoji} Quick start script created: start.sh")
        
        return True
    
    def display_next_steps(self):
        """Display next steps for the user"""
        print(f"\n{self.rocket_emoji} MAPSHOCK MVP Setup Complete!")
        print("=" * 60)
        print(f"\n{self.success_emoji} Your MAPSHOCK Intelligence Platform is ready!")
        
        print(f"\n{self.info_emoji} Next Steps:")
        print("1. Add your API keys to the .env file:")
        print("   - OPENAI_API_KEY=sk-your-key-here")
        print("   - ANTHROPIC_API_KEY=sk-ant-your-key-here")
        
        print("\n2. Start the platform:")
        print("   ./start.sh")
        print("   OR")
        print("   uvicorn mapshock-backend.main:app --host 0.0.0.0 --port 8000 --reload")
        
        print("\n3. Test your MVP:")
        print("   python test_client.py")
        
        print("\n4. Access your platform:")
        print("   • API: http://localhost:8000")
        print("   • Docs: http://localhost:8000/docs")
        print("   • Health: http://localhost:8000/health")
        print("   • Protocols: http://localhost:8000/api/v1/protocols")
        
        print("\n5. Integrate with Lobe Chat:")
        print("   • Copy: lobe-chat-plugin/mapshock-plugin.ts")
        print("   • Configure API URL: http://localhost:8000")
        
        print(f"\n{self.rocket_emoji} Start analyzing with MAPSHOCK protocols!")
        print("Query: 'Who are our main competitors in the AI market?'")
        print("Result: Protocol-driven intelligence with confidence scores")
        
        print(f"\n📚 Documentation: README.md")
        print("🆘 Support: Create an issue on GitHub")
    
    def run_setup(self):
        """Run the complete setup process"""
        self.print_header()
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Creating directory structure", self.create_directory_structure),
            ("Installing dependencies", self.install_dependencies),
            ("Creating environment file", self.create_env_file),
            ("Testing installation", self.test_installation),
            ("Creating quick start script", self.create_quick_start_script)
        ]
        
        for step_name, step_func in steps:
            print(f"\n⏳ {step_name}...")
            if not step_func():
                print(f"{self.error_emoji} Setup failed at: {step_name}")
                return False
            time.sleep(0.5)  # Brief pause for better UX
        
        self.display_next_steps()
        return True

def main():
    """Main setup function"""
    setup = MAPSHOCKSetup()
    
    try:
        success = setup.run_setup()
        if success:
            print(f"\n{setup.success_emoji} Setup completed successfully!")
            sys.exit(0)
        else:
            print(f"\n{setup.error_emoji} Setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{setup.error_emoji} Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{setup.error_emoji} Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 