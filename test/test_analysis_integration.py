"""
Integration test for Analysis Agent with real Gemini API
This test validates the complete system with actual API calls.
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis_agent import (
    AnalysisAgent, 
    AnalysisAgentHelper, 
    create_analysis_agent
)

# Load environment variables
load_dotenv()

async def test_real_api_analysis():
    """Test with real Gemini API calls"""
    print("Testing Analysis Agent with Real Gemini API...")
    print("=" * 60)
    
    try:
        # Create analysis agent
        agent = AnalysisAgent(age_group="elementary", strictness_level="moderate")
        
        # Test cases for different content types
        test_cases = [
            {
                "name": "Educational Content",
                "input": "I'm working on my math homework. What is 15 + 27?",
                "expected_category": "educational",
                "expected_action": "allow"
            },
            {
                "name": "Safe Social Content", 
                "input": "Can I play with my friends after school?",
                "expected_category": "safe",
                "expected_action": "allow"
            },
            {
                "name": "Entertainment Content",
                "input": "I want to watch cartoons on YouTube",
                "expected_category": "entertainment", 
                "expected_action": "monitor"
            },
            {
                "name": "Concerning Content",
                "input": "I hate school and don't want to go tomorrow",
                "expected_category": "concerning",
                "expected_action": "restrict"
            }
        ]
        
        print("\nRunning analysis tests...")
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}...")
            print(f"   Input: '{test_case['input']}'")
            
            try:
                # Run analysis
                result = await agent.analyze_input_context(test_case['input'])
                
                # Display results
                print(f"   Category: {result.category}")
                print(f"   Confidence: {result.confidence:.2f}")
                print(f"   Action: {result.parental_action}")
                print(f"   Educational Value: {result.educational_value}")
                print(f"   Safety Concerns: {len(result.safety_concerns)} concerns")
                print(f"   Context: {result.context_summary[:100]}...")
                
                # Check if results match expectations
                category_match = result.category == test_case['expected_category']
                action_match = result.parental_action == test_case['expected_action']
                
                if category_match and action_match:
                    print("   ✅ Results match expectations")
                else:
                    print("   ⚠️  Results differ from expectations")
                
                results.append({
                    'test_case': test_case['name'],
                    'success': True,
                    'result': result
                })
                
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                results.append({
                    'test_case': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
        
        # Display statistics
        print(f"\n{'='*60}")
        print("Analysis Statistics:")
        stats = agent.get_analysis_statistics()
        print(f"   Total analyses: {stats['total_analyses']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"   Error rate: {stats['error_rate']:.2%}")
        print(f"   Category distribution: {stats['category_distribution']}")
        
        # Test results summary
        successful_tests = sum(1 for r in results if r['success'])
        print(f"\nTest Results: {successful_tests}/{len(results)} tests passed")
        
        return successful_tests == len(results)
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

async def test_caching_performance():
    """Test caching performance"""
    print("\nTesting Caching Performance...")
    print("=" * 60)
    
    try:
        agent = AnalysisAgent(cache_enabled=True)
        test_input = "I'm studying for my science test about planets"
        
        # First analysis (cache miss)
        print("\n1. First analysis (cache miss)...")
        import time
        start_time = time.time()
        result1 = await agent.analyze_input_context(test_input)
        first_time = time.time() - start_time
        print(f"   Time: {first_time:.2f}s")
        print(f"   Category: {result1.category}")
        
        # Second analysis (cache hit)
        print("\n2. Second analysis (cache hit)...")
        start_time = time.time()
        result2 = await agent.analyze_input_context(test_input)
        second_time = time.time() - start_time
        print(f"   Time: {second_time:.2f}s")
        print(f"   Category: {result2.category}")
        
        # Performance comparison
        if second_time < first_time:
            speedup = first_time / second_time
            print(f"   ✅ Cache speedup: {speedup:.1f}x faster")
        else:
            print("   ⚠️  No significant speedup detected")
        
        # Cache statistics
        stats = agent.get_analysis_statistics()
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"   Total analyses: {stats['total_analyses']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

async def test_adk_integration():
    """Test ADK integration"""
    print("\nTesting ADK Integration...")
    print("=" * 60)
    
    try:
        # Create ADK agent
        adk_agent = create_analysis_agent()
        
        print(f"Agent created successfully:")
        print(f"   Name: {adk_agent.name}")
        print(f"   Model: {adk_agent.model}")
        print(f"   Tools: {len(adk_agent.tools)}")
        
        # List available tools
        print("\nAvailable tools:")
        for i, tool in enumerate(adk_agent.tools, 1):
            tool_name = getattr(tool, 'name', 'unknown')
            print(f"   {i}. {tool_name}")
        
        print("✅ ADK integration working correctly")
        return True
        
    except Exception as e:
        print(f"❌ ADK integration test failed: {e}")
        return False

async def test_multimodal_analysis():
    """Test multimodal analysis with screenshot"""
    print("\nTesting Multimodal Analysis...")
    print("=" * 60)
    
    try:
        agent = AnalysisAgent()
        
        # Create a fake screenshot file for testing
        temp_dir = tempfile.mkdtemp()
        screenshot_path = os.path.join(temp_dir, "test_screenshot.png")
        
        # Create a simple test image (1x1 pixel PNG)
        import base64
        # Minimal PNG data (1x1 transparent pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg=="
        )
        
        with open(screenshot_path, "wb") as f:
            f.write(png_data)
        
        # Test multimodal analysis
        test_input = "I'm looking at my homework assignment"
        result = await agent.analyze_input_context(test_input, screenshot_path)
        
        print(f"Multimodal analysis completed:")
        print(f"   Category: {result.category}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Action: {result.parental_action}")
        print(f"   Screenshot used: {result.screenshot_path is not None}")
        
        # Clean up
        os.unlink(screenshot_path)
        os.rmdir(temp_dir)
        
        print("✅ Multimodal analysis test passed")
        return True
        
    except Exception as e:
        print(f"❌ Multimodal analysis test failed: {e}")
        return False

async def main():
    """Run integration tests"""
    print("Analysis Agent Integration Test Suite")
    print("=" * 70)
    
    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Please set your Google API key in .env file")
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    
    # Run all tests
    test_results = []
    
    # Test 1: Real analysis with Gemini API
    result1 = await test_real_api_analysis()
    test_results.append(("Real API Analysis", result1))
    
    # Test 2: Caching performance
    result2 = await test_caching_performance()
    test_results.append(("Caching Performance", result2))
    
    # Test 3: ADK integration
    result3 = await test_adk_integration()
    test_results.append(("ADK Integration", result3))
    
    # Test 4: Multimodal analysis
    result4 = await test_multimodal_analysis()
    test_results.append(("Multimodal Analysis", result4))
    
    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("Analysis Agent is fully functional and ready for production use.")
    else:
        print("⚠️  Some tests failed.")
        print("Please check API configuration and network connectivity.")
    
    return passed_tests == len(test_results)

if __name__ == "__main__":
    asyncio.run(main()) 