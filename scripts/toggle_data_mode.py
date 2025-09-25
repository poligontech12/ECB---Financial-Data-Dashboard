#!/usr/bin/env python3
"""
ECB Data Mode Toggle Script

This script allows you to switch between API mode and local data mode
for the ECB Financial Data Visualizer.

Usage:
    python scripts/toggle_data_mode.py --mode local
    python scripts/toggle_data_mode.py --mode api
    python scripts/toggle_data_mode.py --status
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import get_config, ECB_API_CONFIG

def update_config_file(use_local_data: bool):
    """Update the config file to set the data mode"""
    config_file = Path(__file__).parent.parent / "src" / "utils" / "config.py"
    
    # Read the current config file
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace the use_local_data setting
    old_line = f'"use_local_data": {not use_local_data},'
    new_line = f'"use_local_data": {use_local_data},'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Write the updated config
        with open(config_file, 'w') as f:
            f.write(content)
        
        mode_name = "LOCAL" if use_local_data else "API"
        print(f"✅ Configuration updated: Data mode set to {mode_name}")
        return True
    else:
        print(f"❌ Could not find the configuration line to update")
        print(f"   Looking for: {old_line}")
        return False

def show_status():
    """Show the current data mode status"""
    try:
        config = get_config()
        use_local_data = config["ecb_api"].get("use_local_data", False)
        local_data_dir = config["ecb_api"].get("local_data_dir", "data/raw-data")
        
        mode_name = "LOCAL" if use_local_data else "API"
        print(f"📊 ECB Data Visualizer Status:")
        print(f"   Current Mode: {mode_name}")
        
        if use_local_data:
            data_dir = Path(config["paths"]["project_root"]) / local_data_dir
            print(f"   Local Data Directory: {data_dir}")
            
            if data_dir.exists():
                xml_files = list(data_dir.glob("*.xml"))
                metadata_files = list(data_dir.glob("*_metadata.json"))
                print(f"   Available Data Files: {len(xml_files)} XML files, {len(metadata_files)} metadata files")
                
                if xml_files:
                    print("   📁 Data Files:")
                    for xml_file in sorted(xml_files):
                        file_size = xml_file.stat().st_size
                        print(f"      - {xml_file.name} ({file_size:,} bytes)")
                else:
                    print("   ⚠️  No data files found in local directory")
                    print("   💡 Run: python scripts/download_ecb_data.py")
            else:
                print(f"   ❌ Local data directory does not exist: {data_dir}")
        else:
            print(f"   API Base URL: {config['ecb_api']['base_url']}")
            print(f"   API Timeout: {config['ecb_api']['timeout']} seconds")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Toggle between API and local data modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Switch to local data mode
  python scripts/toggle_data_mode.py --mode local
  
  # Switch to API mode  
  python scripts/toggle_data_mode.py --mode api
  
  # Show current status
  python scripts/toggle_data_mode.py --status
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['local', 'api'],
        help='Set data mode: local (use downloaded files) or api (use ECB API)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current data mode status'
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.mode:
        use_local_data = (args.mode == 'local')
        
        if update_config_file(use_local_data):
            print()
            show_status()
            
            if use_local_data:
                print()
                print("💡 Tips for local mode:")
                print("   - Make sure you have downloaded data files using:")
                print("     python scripts/download_ecb_data.py")
                print("   - Data files should be in: data/raw-data/")
                print("   - Restart the application to apply changes")
            else:
                print()
                print("💡 Tips for API mode:")
                print("   - Ensure you have internet connectivity")
                print("   - API requests are rate-limited")
                print("   - Restart the application to apply changes")
        else:
            print("❌ Failed to update configuration")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()