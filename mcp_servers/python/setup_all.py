#!/usr/bin/env python3
"""
Setup script for all Python MCP servers
Team 28 - Code Paglus
"""

import os
import subprocess
import sys
import json
from pathlib import Path

# MCP server directories
MCP_SERVERS = [
    "square_mcp",
    "h2o_ai_mcp", 
    "github_mcp",
    "plaid_client",
    "aws_athena_mcp"
]

def run_command(command, cwd=None):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error running command: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception running command: {command}")
        print(f"Exception: {str(e)}")
        return False

def setup_virtual_environment(server_dir):
    """Setup virtual environment for MCP server"""
    print(f"📦 Setting up virtual environment for {server_dir}...")
    
    venv_path = os.path.join(server_dir, "venv")
    
    # Create virtual environment
    if not run_command(f"python3 -m venv {venv_path}"):
        return False
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(venv_path, "Scripts", "activate")
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:  # Unix/Linux/macOS
        activate_script = os.path.join(venv_path, "bin", "activate")
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    # Install requirements
    requirements_file = os.path.join(server_dir, "requirements.txt")
    if os.path.exists(requirements_file):
        print(f"📥 Installing requirements for {server_dir}...")
        if not run_command(f"{pip_path} install -r requirements.txt", cwd=server_dir):
            return False
    
    print(f"✅ Setup complete for {server_dir}")
    return True

def copy_config_templates():
    """Copy configuration templates from JavaScript implementations"""
    js_base = "../js"
    
    config_mapping = {
        "square_mcp": "square_mcp/config.json",
        "h2o_ai_mcp": "h2o_ai_mcp/config.json", 
        "github_mcp": "optional_github_mcp/config.json",
        "plaid_client": "plaid_client/config.json",
        "aws_athena_mcp": "aws_athena_mcp/config.json"
    }
    
    for python_dir, js_config_path in config_mapping.items():
        js_config_full_path = os.path.join(js_base, js_config_path)
        python_config_path = os.path.join(python_dir, "config.json")
        
        if os.path.exists(js_config_full_path) and not os.path.exists(python_config_path):
            print(f"📄 Copying config template for {python_dir}...")
            try:
                with open(js_config_full_path, 'r') as src:
                    config_data = json.load(src)
                
                # Adjust port numbers for Python versions
                if "server" in config_data and "port" in config_data["server"]:
                    config_data["server"]["port"] += 1000  # Add 1000 to avoid conflicts
                
                with open(python_config_path, 'w') as dst:
                    json.dump(config_data, dst, indent=2)
                
                print(f"✅ Config template copied for {python_dir}")
            except Exception as e:
                print(f"❌ Failed to copy config for {python_dir}: {str(e)}")

def create_run_scripts():
    """Create run scripts for each MCP server"""
    for server_dir in MCP_SERVERS:
        if os.name == 'nt':  # Windows
            script_name = f"run_{server_dir}.bat"
            script_content = f"""@echo off
cd {server_dir}
call venv\\Scripts\\activate
python main.py
pause
"""
        else:  # Unix/Linux/macOS
            script_name = f"run_{server_dir}.sh"
            script_content = f"""#!/bin/bash
cd {server_dir}
source venv/bin/activate
python main.py
"""
        
        with open(script_name, 'w') as f:
            f.write(script_content)
        
        if os.name != 'nt':
            os.chmod(script_name, 0o755)
        
        print(f"✅ Created run script: {script_name}")

def main():
    """Main setup function"""
    print("🚀 Setting up Python MCP Servers for Team 28 - Code Paglus")
    print("=" * 60)
    
    # Check if Python 3 is available
    if not run_command("python3 --version"):
        print("❌ Python 3 is required but not found")
        sys.exit(1)
    
    # Copy configuration templates
    print("\n📋 Copying configuration templates...")
    copy_config_templates()
    
    # Setup each MCP server
    print("\n🔧 Setting up MCP servers...")
    success_count = 0
    
    for server_dir in MCP_SERVERS:
        if os.path.exists(server_dir):
            if setup_virtual_environment(server_dir):
                success_count += 1
        else:
            print(f"⚠️  Directory not found: {server_dir}")
    
    # Create run scripts
    print("\n📝 Creating run scripts...")
    create_run_scripts()
    
    print(f"\n🎉 Setup complete! {success_count}/{len(MCP_SERVERS)} servers configured successfully")
    print("\n📖 Next steps:")
    print("1. Configure your API credentials in each config.json file")
    print("2. For AWS Athena: Configure AWS credentials using 'aws configure' or environment variables")
    print("3. Run individual servers using the generated run scripts")
    print("4. Test the servers using MCP Inspector or Claude Desktop")
    
    if os.name == 'nt':
        print("\nWindows users: Run .bat files to start servers")
    else:
        print("\nUnix/Linux/macOS users: Run .sh files to start servers")

if __name__ == "__main__":
    main()
