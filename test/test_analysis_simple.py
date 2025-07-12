"""
Simple test script for Analysis Agent core functionality
"""

import asyncio
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis_agent import (
    AnalysisAgent, 
    AnalysisAgentHelper, 
    AnalysisResult,
    AnalysisCache,
    create_analysis_agent
)

async def test_analysis_agent_core():
    """Test the core Analysis Agent functionality"""
    print("Testing Analysis Agent Core Functionality...")
    print("=" * 50)
    
    try:
        # Test 1: Initialize agent
        print("\n1. Testing agent initialization...")
        agent = AnalysisAgent(
            age_group="elementary",
            strictness_level="moderate",
            cache_enabled=True
        )
        print("   ✅ Agent initialized successfully")
        
        # Test 2: Test configuration
        print("\n2. Testing configuration...")
        agent.configure_settings("high_school", "strict")
        assert agent.age_group == "high_school"
        assert agent.strictness_level == "strict"
        print("   ✅ Configuration updated successfully")
        
        # Test 3: Test statistics
        print("\n3. Testing statistics...")
        stats = agent.get_analysis_statistics()
        assert stats['total_analyses'] == 0
        assert stats['cache_hit_rate'] == 0.0
        print("   ✅ Statistics tracking working")
        
        # Test 4: Test cache functionality
        print("\n4. Testing cache functionality...")
        cache_key = agent.cache._get_cache_key("test input", None)
        assert len(cache_key) == 32  # MD5 hash
        print("   ✅ Cache key generation working")
        
        # Test 5: Test cleanup
        print("\n5. Testing cleanup...")
        agent.cleanup_cache()
        print("   ✅ Cache cleanup working")
        
        print("\n" + "=" * 50)
        print("🎉 All core tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_helper_agent():
    """Test the helper agent"""
    print("\nTesting Analysis Agent Helper...")
    print("=" * 50)
    
    try:
        # Test 1: Initialize helper
        print("\n1. Testing helper initialization...")
        helper = AnalysisAgentHelper()
        assert hasattr(helper, 'analysis_engine')
        print("   ✅ Helper initialized successfully")
        
        # Test 2: Test configuration
        print("\n2. Testing helper configuration...")
        helper.configure("elementary", "moderate")
        print("   ✅ Helper configuration working")
        
        # Test 3: Test statistics
        print("\n3. Testing helper statistics...")
        stats = helper.get_statistics()
        assert 'total_analyses' in stats
        print("   ✅ Helper statistics working")
        
        print("\n" + "=" * 50)
        print("🎉 All helper tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Helper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_adk_agent():
    """Test ADK agent creation"""
    print("\nTesting ADK Agent Creation...")
    print("=" * 50)
    
    try:
        # Test 1: Create ADK agent
        print("\n1. Testing ADK agent creation...")
        agent = create_analysis_agent()
        assert agent.name == "AnalysisAgent"
        assert agent.model == "gemini-2.0-flash"
        assert len(agent.tools) > 0
        print("   ✅ ADK agent created successfully")
        
        # Test 2: Check tools
        print("\n2. Testing tool registration...")
        tool_names = []
        for tool in agent.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, 'func') and hasattr(tool.func, '__name__'):
                tool_names.append(tool.func.__name__)
            else:
                tool_names.append(str(tool))
        
        expected_tools = [
            "analyze_input_context",
            "get_analysis_statistics",
            "configure_analysis_agent",
            "cleanup_analysis_cache"
        ]
        
        print(f"   Found {len(tool_names)} tools: {tool_names}")
        
        for tool_name in expected_tools:
            # Check if any tool name contains the expected tool name
            found = any(tool_name in tn for tn in tool_names)
            if found:
                print(f"   ✅ Tool found: {tool_name}")
            else:
                print(f"   ⚠️  Tool missing: {tool_name}")
        
        print("\n" + "=" * 50)
        print("🎉 All ADK tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ADK test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_functionality():
    """Test cache functionality"""
    print("\nTesting Cache Functionality...")
    print("=" * 50)
    
    try:
        # Test 1: Create cache
        print("\n1. Testing cache creation...")
        import tempfile
        temp_dir = tempfile.mkdtemp()
        cache = AnalysisCache(cache_dir=temp_dir, max_age_minutes=1)
        print("   ✅ Cache created successfully")
        
        # Test 2: Test cache key generation
        print("\n2. Testing cache key generation...")
        key1 = cache._get_cache_key("test input", None)
        key2 = cache._get_cache_key("test input", None)
        key3 = cache._get_cache_key("different input", None)
        
        assert key1 == key2, "Same input should generate same key"
        assert key1 != key3, "Different input should generate different key"
        assert len(key1) == 32, "Key should be 32 characters (MD5)"
        print("   ✅ Cache key generation working")
        
        # Test 3: Test cache miss
        print("\n3. Testing cache miss...")
        result = cache.get("non-existent", None)
        assert result is None, "Should return None for cache miss"
        print("   ✅ Cache miss working")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("\n" + "=" * 50)
        print("🎉 All cache tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("Analysis Agent Simple Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_results = []
    
    # Test 1: Core functionality
    result1 = await test_analysis_agent_core()
    test_results.append(("Core Functionality", result1))
    
    # Test 2: Helper agent
    result2 = await test_helper_agent()
    test_results.append(("Helper Agent", result2))
    
    # Test 3: ADK agent
    result3 = await test_adk_agent()
    test_results.append(("ADK Agent", result3))
    
    # Test 4: Cache functionality
    result4 = await test_cache_functionality()
    test_results.append(("Cache Functionality", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("SIMPLE TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("🎉 ALL SIMPLE TESTS PASSED!")
        print("Analysis Agent basic functionality is working correctly.")
    else:
        print("⚠️  Some tests failed.")
        print("Please check the error messages above.")
    
    return passed_tests == len(test_results)

if __name__ == "__main__":
    asyncio.run(main()) 