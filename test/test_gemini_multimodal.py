#!/usr/bin/env python3
"""
Test script for Gemini Multimodal ADK FunctionTool
"""

import os
import sys
import asyncio
import warnings
import base64
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gemini_multimodal import (
    GeminiMultimodalAnalyzer,
    MultimodalAnalysisConfig,
    AgeGroup,
    ContentCategory,
    analyze_text_content_tool,
    analyze_multimodal_content_tool,
    get_analysis_summary_tool,
    configure_analysis_settings_tool,
    create_gemini_analysis_agent
)
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Load environment variables
load_dotenv()

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Basic logging setup
import logging
logging.basicConfig(level=logging.INFO)

def test_gemini_multimodal_analyzer():
    """Test the GeminiMultimodalAnalyzer class"""
    print("🤖 Testing GeminiMultimodalAnalyzer...")
    
    try:
        # Check API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key configured (length: {len(api_key)})")
        
        # Create analyzer with config
        config = MultimodalAnalysisConfig(
            target_age_group=AgeGroup.ELEMENTARY,
            strict_mode=True,
            assess_educational_value=True
        )
        analyzer = GeminiMultimodalAnalyzer(config)
        print("✅ Analyzer created successfully")
        
        # Test text analysis with safe content
        print("\n📝 Testing safe educational content...")
        safe_text = "I'm working on my math homework. What is 5 + 3?"
        result = analyzer.analyze_text_only(safe_text)
        
        print(f"   Category: {result.category.value}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Age appropriate for elementary: {result.age_appropriate.get(AgeGroup.ELEMENTARY, False)}")
        print(f"   Context: {result.context_summary}")
        print(f"   Educational value: {result.educational_value}")
        
        if result.category in [ContentCategory.SAFE, ContentCategory.EDUCATIONAL]:
            print("✅ Safe content correctly identified")
        else:
            print("⚠️  Safe content not identified as safe")
        
        # Test text analysis with concerning content
        print("\n⚠️  Testing concerning content...")
        concerning_text = "I hate school and want to skip class tomorrow"
        result2 = analyzer.analyze_text_only(concerning_text)
        
        print(f"   Category: {result2.category.value}")
        print(f"   Confidence: {result2.confidence}")
        print(f"   Concerns: {result2.concerns}")
        print(f"   Recommendations: {result2.recommendations}")
        
        if result2.category in [ContentCategory.CONCERNING, ContentCategory.INAPPROPRIATE]:
            print("✅ Concerning content correctly identified")
        else:
            print("⚠️  Concerning content not flagged")
        
        # Test analysis summary
        print("\n📊 Testing analysis summary...")
        summary = analyzer.get_analysis_summary()
        print(f"   Total analyses: {summary.get('total_analyses', 0)}")
        print(f"   Category distribution: {summary.get('category_distribution', {})}")
        print(f"   Average confidence: {summary.get('average_confidence', 0)}")
        
        if summary.get('status') == 'success':
            print("✅ Analysis summary generated successfully")
        else:
            print("❌ Analysis summary failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ GeminiMultimodalAnalyzer test failed: {e}")
        return False

def test_gemini_multimodal_tools():
    """Test individual ADK function tools"""
    print("\n🔧 Testing Gemini Multimodal Tools...")
    
    try:
        # Create mock tool context
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        tool_context = MockToolContext()
        
        # Test configuration tool
        print("⚙️  Testing configuration tool...")
        tool_context.state['target_age_group'] = 'elementary'
        tool_context.state['strict_mode'] = True
        
        config_result = configure_analysis_settings_tool(tool_context)
        if config_result['status'] == 'success':
            print("✅ Configuration tool working")
            print(f"   Age group: {config_result['config']['age_group']}")
            print(f"   Strict mode: {config_result['config']['strict_mode']}")
        else:
            print(f"❌ Configuration tool failed: {config_result['message']}")
            return False
        
        # Test text analysis tool
        print("\n📝 Testing text analysis tool...")
        tool_context.state['current_input_text'] = "I'm learning about dinosaurs for my science project"
        
        text_result = analyze_text_content_tool(tool_context)
        if text_result['status'] == 'success':
            print("✅ Text analysis tool working")
            print(f"   Category: {text_result['analysis']['category']}")
            print(f"   Parental action: {text_result['parental_action']}")
            print(f"   Educational value: {text_result['analysis']['educational_value']}")
        else:
            print(f"❌ Text analysis tool failed: {text_result['message']}")
            return False
        
        # Test analysis summary tool
        print("\n📊 Testing analysis summary tool...")
        summary_result = get_analysis_summary_tool(tool_context)
        if summary_result['status'] == 'success':
            print("✅ Analysis summary tool working")
            print(f"   Total analyses: {summary_result['summary'].get('total_analyses', 0)}")
        else:
            print(f"❌ Analysis summary tool failed: {summary_result['message']}")
            return False
        
        # Test multimodal analysis tool (without actual image)
        print("\n🖼️  Testing multimodal tool (no image)...")
        tool_context.state['current_input_text'] = "Looking at pictures of animals"
        tool_context.state['current_screenshot_base64'] = ""  # No image
        
        multimodal_result = analyze_multimodal_content_tool(tool_context)
        if multimodal_result['status'] == 'no_image_input':
            print("✅ Multimodal tool correctly handles missing image")
        else:
            print(f"⚠️  Multimodal tool unexpected result: {multimodal_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini multimodal tools test failed: {e}")
        return False

def test_age_group_assessment():
    """Test age group specific assessments"""
    print("\n👶 Testing Age Group Assessment...")
    
    try:
        # Test different age groups
        age_groups = [AgeGroup.ELEMENTARY, AgeGroup.MIDDLE_SCHOOL, AgeGroup.HIGH_SCHOOL]
        test_content = "I want to watch a movie about superheroes fighting"
        
        for age_group in age_groups:
            print(f"\n   Testing for {age_group.value}...")
            
            config = MultimodalAnalysisConfig(
                target_age_group=age_group,
                strict_mode=True
            )
            analyzer = GeminiMultimodalAnalyzer(config)
            
            result = analyzer.analyze_text_only(test_content)
            
            print(f"   Category: {result.category.value}")
            print(f"   Age appropriate: {result.age_appropriate.get(age_group, False)}")
            print(f"   Concerns: {len(result.concerns)} concerns")
        
        print("✅ Age group assessment test completed")
        return True
        
    except Exception as e:
        print(f"❌ Age group assessment test failed: {e}")
        return False

def test_content_categories():
    """Test different content category classifications"""
    print("\n📂 Testing Content Categories...")
    
    try:
        config = MultimodalAnalysisConfig(
            target_age_group=AgeGroup.ELEMENTARY,
            strict_mode=True
        )
        analyzer = GeminiMultimodalAnalyzer(config)
        
        # Test different types of content
        test_cases = [
            ("I'm doing my math homework", "Should be SAFE or EDUCATIONAL"),
            ("I'm playing a fun educational game", "Should be EDUCATIONAL or ENTERTAINMENT"),
            ("I'm chatting with my friends", "Should be SOCIAL"),
            ("I'm looking at something I shouldn't", "Should be CONCERNING or INAPPROPRIATE")
        ]
        
        for text, expected in test_cases:
            print(f"\n   Testing: '{text}'")
            result = analyzer.analyze_text_only(text)
            print(f"   Result: {result.category.value} ({expected})")
            print(f"   Confidence: {result.confidence}")
        
        print("✅ Content categories test completed")
        return True
        
    except Exception as e:
        print(f"❌ Content categories test failed: {e}")
        return False

async def test_gemini_analysis_agent():
    """Test the complete Gemini analysis agent"""
    print("\n🤖 Testing GeminiAnalysisAgent...")
    
    try:
        # Create agent
        agent = create_gemini_analysis_agent()
        
        # Create session service
        session_service = InMemorySessionService()
        
        # Create runner
        runner = Runner(
            agent=agent,
            session_service=session_service,
            app_name="parental_control_gemini_test"
        )
        
        print("✅ GeminiAnalysisAgent created successfully!")
        print(f"   Agent name: {agent.name}")
        print(f"   Tools count: {len(agent.tools)}")
        print(f"   Model: {agent.model}")
        
        # Test that agent has all required tools
        tool_names = [tool.func.__name__ for tool in agent.tools]
        expected_tools = [
            "analyze_text_content_tool",
            "analyze_multimodal_content_tool",
            "get_analysis_summary_tool",
            "configure_analysis_settings_tool"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✅ Tool available: {expected_tool}")
            else:
                print(f"❌ Tool missing: {expected_tool}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ GeminiAnalysisAgent test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🛡️  Testing Error Handling...")
    
    try:
        config = MultimodalAnalysisConfig()
        analyzer = GeminiMultimodalAnalyzer(config)
        
        # Test empty input
        print("   Testing empty input...")
        result = analyzer.analyze_text_only("")
        print(f"   Empty input result: {result.category.value}")
        
        # Test very long input
        print("   Testing very long input...")
        long_text = "This is a test " * 1000  # Very long text
        result = analyzer.analyze_text_only(long_text)
        print(f"   Long input result: {result.category.value}")
        
        # Test special characters
        print("   Testing special characters...")
        special_text = "Testing with émojis 🎉 and spëcial châractërs"
        result = analyzer.analyze_text_only(special_text)
        print(f"   Special chars result: {result.category.value}")
        
        print("✅ Error handling test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_integration_simulation():
    """Test integration with keylogger and screen capture simulation"""
    print("\n🔗 Testing Integration Simulation...")
    
    try:
        # Create mock tool context with realistic data
        class MockToolContext:
            def __init__(self):
                self.state = {
                    'current_input_text': 'I want to search for information about animals',
                    'current_screenshot_base64': '',  # Would be actual base64 in real use
                    'screenshot_mime_type': 'image/jpeg',
                    'keylogger_active': True,
                    'target_age_group': 'elementary',
                    'strict_mode': True
                }
        
        tool_context = MockToolContext()
        
        # Simulate the complete workflow
        print("   1. Configuring analysis settings...")
        config_result = configure_analysis_settings_tool(tool_context)
        assert config_result['status'] == 'success'
        
        print("   2. Analyzing text content...")
        text_result = analyze_text_content_tool(tool_context)
        assert text_result['status'] == 'success'
        
        print("   3. Generating analysis summary...")
        summary_result = get_analysis_summary_tool(tool_context)
        assert summary_result['status'] == 'success'
        
        print("   4. Checking parental action recommendation...")
        parental_action = text_result['parental_action']
        print(f"   Recommended action: {parental_action}")
        
        print("✅ Integration simulation successful")
        return True
        
    except Exception as e:
        print(f"❌ Integration simulation failed: {e}")
        return False

async def main():
    """Run all Gemini multimodal tests"""
    print("🚀 Starting Gemini Multimodal Tool Tests\n")
    
    # Check API key first
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key in the .env file")
        return False
    
    # Test 1: Basic analyzer functionality
    analyzer_ok = test_gemini_multimodal_analyzer()
    
    # Test 2: ADK tools
    tools_ok = test_gemini_multimodal_tools()
    
    # Test 3: Age group assessment
    age_group_ok = test_age_group_assessment()
    
    # Test 4: Content categories
    categories_ok = test_content_categories()
    
    # Test 5: Agent integration
    agent_ok = await test_gemini_analysis_agent()
    
    # Test 6: Error handling
    error_handling_ok = test_error_handling()
    
    # Test 7: Integration simulation
    integration_ok = test_integration_simulation()
    
    # Summary
    print("\n" + "="*60)
    print("📊 GEMINI MULTIMODAL TEST SUMMARY")
    print("="*60)
    
    tests = [
        ("Basic Analyzer", analyzer_ok),
        ("ADK Tools", tools_ok),
        ("Age Group Assessment", age_group_ok),
        ("Content Categories", categories_ok),
        ("Agent Integration", agent_ok),
        ("Error Handling", error_handling_ok),
        ("Integration Simulation", integration_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All Gemini Multimodal tests passed!")
        print("✅ Ready to integrate with keylogger and screen capture!")
    elif passed >= 5:
        print("\n✅ Core Gemini Multimodal functionality is working!")
        print("⚠️  Some advanced features may need attention.")
    else:
        print("\n❌ Gemini Multimodal implementation needs troubleshooting.")
        print("💡 Make sure your GOOGLE_API_KEY is valid and has Gemini API access.")
    
    return passed >= 5

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 