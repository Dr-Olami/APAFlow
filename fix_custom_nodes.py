#!/usr/bin/env python3
"""
Script to fix SMEFlow custom nodes for proper Flowise integration
"""

import os
import shutil
from pathlib import Path

def replace_node_files():
    """Replace all custom node files with fixed versions"""
    
    base_path = Path("flowise/custom-nodes")
    
    # Define node replacements
    replacements = [
        {
            "original": base_path / "agents/SMEFlowSupervisor/SMEFlowSupervisor.js",
            "fixed": base_path / "agents/SMEFlowSupervisor/SMEFlowSupervisor_fixed.js"
        },
        {
            "original": base_path / "chains/SMEFlowWorkflow/SMEFlowWorkflow.js",
            "fixed": base_path / "chains/SMEFlowWorkflow/SMEFlowWorkflow_fixed.js"
        },
        {
            "original": base_path / "tools/SMEFlowAfricanIntegrations/SMEFlowAfricanIntegrations.js",
            "fixed": base_path / "tools/SMEFlowAfricanIntegrations/SMEFlowAfricanIntegrations_fixed.js"
        }
    ]
    
    print("🔧 Fixing SMEFlow custom nodes for Flowise compatibility...")
    
    for replacement in replacements:
        original_file = replacement["original"]
        fixed_file = replacement["fixed"]
        
        if fixed_file.exists():
            print(f"✅ Replacing {original_file.name}")
            
            # Backup original
            backup_file = original_file.with_suffix('.js.backup')
            if original_file.exists():
                shutil.copy2(original_file, backup_file)
                print(f"   📦 Backed up to {backup_file.name}")
            
            # Replace with fixed version
            shutil.copy2(fixed_file, original_file)
            print(f"   ✨ Applied fix from {fixed_file.name}")
            
            # Remove fixed file
            fixed_file.unlink()
            print(f"   🗑️  Cleaned up {fixed_file.name}")
        else:
            print(f"❌ Fixed file not found: {fixed_file}")
    
    print("\n🎉 Node fixes completed!")
    print("\nNext steps:")
    print("1. Commit and push changes to GitHub")
    print("2. Pull changes in Codespaces") 
    print("3. Copy fixed nodes to Flowise container")
    print("4. Restart Flowise to load updated nodes")

if __name__ == "__main__":
    replace_node_files()
