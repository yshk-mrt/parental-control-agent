"""
Weave Integration Test for Analysis Agent

This test demonstrates how Weave tracks multi-agent operations,
providing visibility into the analysis workflow and performance metrics.
"""

import asyncio
import os
import weave
from dotenv import load_dotenv
from analysis_agent import AnalysisAgent, AnalysisAgentHelper

# Load environment variables
load_dotenv()

@weave.op()
async def test_single_analysis():
    """Test single analysis with Weave tracking"""
    print("🔍 Testing single analysis with Weave tracking...")
    
    # Create analysis agent (Weave Model)
    agent = AnalysisAgent(
        age_group="elementary",
        strictness_level="moderate",
        cache_enabled=True
    )
    
    # Test input
    test_input = "I'm working on my math homework. What is 25 + 17?"
    
    # Perform analysis (automatically tracked by Weave)
    result = await agent.predict(test_input)
    
    print(f"   Category: {result.category}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Action: {result.parental_action}")
    print(f"   Educational Value: {result.educational_value}")
    
    return result

@weave.op()
async def test_cache_performance():
    """Test cache performance with Weave tracking"""
    print("⚡ Testing cache performance with Weave tracking...")
    
    agent = AnalysisAgent(cache_enabled=True)
    test_input = "Can I play games after finishing my homework?"
    
    # First analysis (cache miss)
    import time
    start_time = time.time()
    result1 = await agent.predict(test_input)
    first_time = time.time() - start_time
    
    # Second analysis (cache hit)
    start_time = time.time()
    result2 = await agent.predict(test_input)
    second_time = time.time() - start_time
    
    # Performance comparison
    speedup = first_time / max(second_time, 0.001)  # Avoid division by zero
    
    print(f"   First analysis: {first_time:.3f}s")
    print(f"   Second analysis: {second_time:.3f}s")
    print(f"   Cache speedup: {speedup:.1f}x")
    
    return {
        "first_time": first_time,
        "second_time": second_time,
        "speedup": speedup,
        "cache_working": result1.category == result2.category
    }

@weave.op()
async def test_multi_agent_workflow():
    """Test multi-agent workflow simulation"""
    print("🤖 Testing multi-agent workflow with Weave tracking...")
    
    # Simulate different agents processing different types of content
    agents = {
        "elementary_strict": AnalysisAgent(age_group="elementary", strictness_level="strict"),
        "middle_school_moderate": AnalysisAgent(age_group="middle_school", strictness_level="moderate"),
        "high_school_lenient": AnalysisAgent(age_group="high_school", strictness_level="lenient")
    }
    
    test_cases = [
        "I want to watch YouTube videos about science experiments",
        "Can I chat with my friends on Discord?",
        "I'm researching for my history project about World War 2"
    ]
    
    results = {}
    
    for agent_name, agent in agents.items():
        agent_results = []
        for test_case in test_cases:
            result = await agent.predict(test_case)
            agent_results.append({
                "input": test_case,
                "category": result.category,
                "action": result.parental_action,
                "confidence": result.confidence
            })
        results[agent_name] = agent_results
    
    # Display results
    for agent_name, agent_results in results.items():
        print(f"\n   {agent_name.upper()}:")
        for i, result in enumerate(agent_results, 1):
            print(f"     {i}. {result['category']} → {result['action']} (conf: {result['confidence']:.2f})")
    
    return results

@weave.op()
async def test_error_handling():
    """Test error handling with Weave tracking"""
    print("⚠️  Testing error handling with Weave tracking...")
    
    agent = AnalysisAgent()
    
    # Test with various edge cases
    edge_cases = [
        "",  # Empty input
        "a" * 1000,  # Very long input
        "🎮🎯🚀💻📱",  # Emoji only
        None  # None input (will be converted to string)
    ]
    
    results = []
    for test_input in edge_cases:
        try:
            result = await agent.predict(str(test_input) if test_input is not None else "")
            results.append({
                "input": test_input,
                "category": result.category,
                "success": True
            })
            print(f"   ✅ Handled: {str(test_input)[:20]}...")
        except Exception as e:
            results.append({
                "input": test_input,
                "error": str(e),
                "success": False
            })
            print(f"   ❌ Failed: {str(test_input)[:20]}... - {e}")
    
    return results

@weave.op()
async def comprehensive_analysis_evaluation():
    """Comprehensive evaluation of analysis agent with multiple metrics"""
    print("📊 Running comprehensive analysis evaluation...")
    
    # Create evaluation dataset
    evaluation_cases = [
        {
            "input": "I'm doing my math homework and need help with fractions",
            "expected_category": "educational",
            "expected_action": "allow"
        },
        {
            "input": "I want to play violent video games all night",
            "expected_category": "concerning",
            "expected_action": "restrict"
        },
        {
            "input": "Can I watch cartoons on Netflix?",
            "expected_category": "entertainment",
            "expected_action": "monitor"
        },
        {
            "input": "I'm chatting with my school friends about our project",
            "expected_category": "social",
            "expected_action": "allow"
        }
    ]
    
    agent = AnalysisAgent(age_group="elementary", strictness_level="moderate")
    
    evaluation_results = []
    correct_categories = 0
    correct_actions = 0
    
    for case in evaluation_cases:
        result = await agent.predict(case["input"])
        
        category_correct = result.category == case["expected_category"]
        action_correct = result.parental_action == case["expected_action"]
        
        if category_correct:
            correct_categories += 1
        if action_correct:
            correct_actions += 1
        
        evaluation_results.append({
            "input": case["input"],
            "predicted_category": result.category,
            "expected_category": case["expected_category"],
            "predicted_action": result.parental_action,
            "expected_action": case["expected_action"],
            "category_correct": category_correct,
            "action_correct": action_correct,
            "confidence": result.confidence
        })
        
        status_cat = "✅" if category_correct else "❌"
        status_act = "✅" if action_correct else "❌"
        print(f"   {status_cat} Category: {result.category} {status_act} Action: {result.parental_action}")
    
    # Calculate metrics
    category_accuracy = correct_categories / len(evaluation_cases)
    action_accuracy = correct_actions / len(evaluation_cases)
    
    print(f"\n   📈 Category Accuracy: {category_accuracy:.2%}")
    print(f"   📈 Action Accuracy: {action_accuracy:.2%}")
    
    return {
        "evaluation_results": evaluation_results,
        "category_accuracy": category_accuracy,
        "action_accuracy": action_accuracy,
        "total_cases": len(evaluation_cases)
    }

@weave.op()
async def main():
    """Main test function that runs all Weave integration tests"""
    print("🚀 Starting Weave Integration Tests for Analysis Agent")
    print("=" * 60)
    
    # Check API keys
    google_api_key = os.getenv('GOOGLE_API_KEY')
    weave_api_key = os.getenv('WEAVE_API_KEY')
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return False
    
    if not weave_api_key:
        print("⚠️  WEAVE_API_KEY not found - using local tracking")
    else:
        print("✅ Weave API key found - using cloud tracking")
    
    print(f"✅ Google API key found (length: {len(google_api_key)})")
    
    try:
        # Run all tests
        test_results = {}
        
        # Test 1: Single analysis
        test_results["single_analysis"] = await test_single_analysis()
        
        # Test 2: Cache performance
        test_results["cache_performance"] = await test_cache_performance()
        
        # Test 3: Multi-agent workflow
        test_results["multi_agent_workflow"] = await test_multi_agent_workflow()
        
        # Test 4: Error handling
        test_results["error_handling"] = await test_error_handling()
        
        # Test 5: Comprehensive evaluation
        test_results["comprehensive_evaluation"] = await comprehensive_analysis_evaluation()
        
        print("\n" + "=" * 60)
        print("🎉 ALL WEAVE INTEGRATION TESTS COMPLETED!")
        print("=" * 60)
        
        # Summary
        cache_result = test_results["cache_performance"]
        eval_result = test_results["comprehensive_evaluation"]
        
        print(f"📊 Performance Summary:")
        print(f"   Cache speedup: {cache_result['speedup']:.1f}x")
        print(f"   Category accuracy: {eval_result['category_accuracy']:.2%}")
        print(f"   Action accuracy: {eval_result['action_accuracy']:.2%}")
        
        print(f"\n🔍 Weave Tracking:")
        print(f"   All operations are tracked in Weave dashboard")
        print(f"   Visit your Weave project to see detailed traces")
        print(f"   Project: parental-control-agent")
        
        return True
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Initialize Weave (will use API key if available, otherwise local)
    try:
        weave.init("parental-control-agent")
        print("✅ Weave initialized successfully")
    except Exception as e:
        print(f"⚠️  Weave initialization failed: {e}")
        print("   Continuing with local tracking only...")
    
    # Run tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Weave integration is working correctly!")
    else:
        print("\n❌ Weave integration tests failed.") 