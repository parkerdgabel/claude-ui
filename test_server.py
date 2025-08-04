#!/usr/bin/env python
"""Test if the server can start successfully"""

import asyncio
import sys

async def test_imports():
    """Test if all imports work"""
    try:
        from claude_ui.main import app
        print("✓ Successfully imported FastAPI app")
        
        from claude_ui.services import (
            instance_service,
            project_service,
            session_service,
            mcp_service,
            worktree_service,
        )
        print("✓ Successfully imported all services")
        
        from claude_ui.core.database import init_db
        print("✓ Successfully imported database module")
        
        # Test database initialization
        await init_db()
        print("✓ Successfully initialized database")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests"""
    success = await test_imports()
    
    if success:
        print("\n✅ All imports successful! The app should be able to start.")
        print("\nTo run the server:")
        print("  uv run uvicorn claude_ui.main:app --reload --port 8002")
    else:
        print("\n❌ Import errors detected. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())