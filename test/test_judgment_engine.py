#!/usr/bin/env python3
"""
Comprehensive test suite for Judgment Engine
"""

import asyncio
import sys
import os
import pytest
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from judgment_engine import (
    JudgmentEngine,
    JudgmentEngineHelper,
    JudgmentConfig,
    JudgmentAction,
    AgeGroup,
    StrictnessLevel,
    ContentCategory,
    JudgmentRule,
    create_judgment_agent,
    judge_content_tool,
    get_judgment_statistics_tool,
    configure_judgment_tool,
    add_custom_judgment_rule_tool,
    get_recent_judgments_tool
)

class TestJudgmentEngine:
    """Test suite for Judgment Engine core functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = JudgmentConfig(
            age_group=AgeGroup.ELEMENTARY,
            strictness_level=StrictnessLevel.MODERATE
        )
        self.engine = JudgmentEngine(self.config)
    
    @pytest.mark.asyncio
    async def test_judgment_engine_initialization(self):
        """Test judgment engine initialization"""
        assert self.engine.config.age_group == AgeGroup.ELEMENTARY
        assert self.engine.config.strictness_level == StrictnessLevel.MODERATE
        assert len(self.engine.rules) > 0
        assert self.engine.stats['total_judgments'] == 0
        print("✅ Judgment engine initialization test passed")
    
    @pytest.mark.asyncio
    async def test_educational_content_judgment(self):
        """Test judgment for educational content"""
        analysis_result = {
            'category': 'educational',
            'confidence': 0.85,
            'input_text': 'I am learning about dinosaurs for my science project',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        result = await self.engine.judge_content(analysis_result)
        
        assert result.action == JudgmentAction.ALLOW
        assert result.confidence == 0.85
        assert 'Educational Content' in result.reasoning
        assert len(result.applied_rules) > 0
        assert not result.emergency_flag
        print("✅ Educational content judgment test passed")
    
    @pytest.mark.asyncio
    async def test_dangerous_content_judgment(self):
        """Test judgment for dangerous content"""
        analysis_result = {
            'category': 'dangerous',
            'confidence': 0.95,
            'input_text': 'dangerous chemical experiments',
            'safety_concerns': ['violence', 'dangerous activities'],
            'age_appropriateness': {'elementary': False}
        }
        
        result = await self.engine.judge_content(analysis_result)
        
        assert result.action == JudgmentAction.BLOCK
        assert result.confidence == 0.95
        assert ('Dangerous Content' in result.reasoning or 'Emergency Keywords' in result.reasoning)
        assert len(result.applied_rules) > 0
        print("✅ Dangerous content judgment test passed")
    
    @pytest.mark.asyncio
    async def test_emergency_keywords_detection(self):
        """Test emergency keyword detection"""
        analysis_result = {
            'category': 'concerning',
            'confidence': 0.75,
            'input_text': 'I am feeling suicidal and want to hurt myself',
            'safety_concerns': ['self-harm'],
            'age_appropriateness': {'elementary': False}
        }
        
        result = await self.engine.judge_content(analysis_result)
        
        assert result.action == JudgmentAction.BLOCK
        assert result.emergency_flag == True
        assert 'Emergency' in result.reasoning or 'emergency' in result.reasoning
        print("✅ Emergency keywords detection test passed")
    
    @pytest.mark.asyncio
    async def test_age_specific_rules(self):
        """Test age-specific rule application"""
        # Test elementary social content (should be restricted)
        elementary_engine = JudgmentEngine(JudgmentConfig(
            age_group=AgeGroup.ELEMENTARY,
            strictness_level=StrictnessLevel.MODERATE
        ))
        
        social_analysis = {
            'category': 'social',
            'confidence': 0.8,
            'input_text': 'chatting with friends on social media',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        elementary_result = await elementary_engine.judge_content(social_analysis)
        assert elementary_result.action == JudgmentAction.RESTRICT
        
        # Test high school social content (should be monitored)
        high_school_engine = JudgmentEngine(JudgmentConfig(
            age_group=AgeGroup.HIGH_SCHOOL,
            strictness_level=StrictnessLevel.MODERATE
        ))
        
        high_school_result = await high_school_engine.judge_content(social_analysis)
        assert high_school_result.action == JudgmentAction.MONITOR
        
        print("✅ Age-specific rules test passed")
    
    @pytest.mark.asyncio
    async def test_strictness_level_impact(self):
        """Test strictness level impact on judgments"""
        entertainment_analysis = {
            'category': 'entertainment',
            'confidence': 0.7,
            'input_text': 'watching funny videos',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        # Test strict mode
        strict_engine = JudgmentEngine(JudgmentConfig(
            age_group=AgeGroup.ELEMENTARY,
            strictness_level=StrictnessLevel.STRICT
        ))
        
        strict_result = await strict_engine.judge_content(entertainment_analysis)
        assert strict_result.action in [JudgmentAction.MONITOR, JudgmentAction.RESTRICT]
        
        # Test lenient mode
        lenient_engine = JudgmentEngine(JudgmentConfig(
            age_group=AgeGroup.HIGH_SCHOOL,
            strictness_level=StrictnessLevel.LENIENT
        ))
        
        lenient_result = await lenient_engine.judge_content(entertainment_analysis)
        assert lenient_result.action in [JudgmentAction.ALLOW, JudgmentAction.MONITOR]
        
        print("✅ Strictness level impact test passed")
    
    @pytest.mark.asyncio
    async def test_low_confidence_fallback(self):
        """Test low confidence fallback behavior"""
        low_confidence_analysis = {
            'category': 'unknown',
            'confidence': 0.3,
            'input_text': 'ambiguous content',
            'safety_concerns': [],
            'age_appropriateness': {}
        }
        
        result = await self.engine.judge_content(low_confidence_analysis)
        
        assert result.action == JudgmentAction.MONITOR
        assert 'Low Confidence' in result.reasoning or 'Unknown' in result.reasoning
        print("✅ Low confidence fallback test passed")
    
    def test_custom_rule_addition(self):
        """Test adding custom rules"""
        custom_rule_data = {
            'rule_id': 'CUSTOM-001',
            'name': 'Custom Gaming Rule',
            'description': 'Allow gaming content during specific hours',
            'conditions': {
                'category': 'entertainment',
                'confidence': {'min': 0.6}
            },
            'action': 'allow',
            'priority': 12,
            'age_groups': ['elementary'],
            'strictness_levels': ['lenient'],
            'enabled': True
        }
        
        success = self.engine.add_custom_rule(custom_rule_data)
        assert success == True
        
        # Verify rule was added
        custom_rules = [r for r in self.engine.rules if r.rule_id == 'CUSTOM-001']
        assert len(custom_rules) == 1
        assert custom_rules[0].name == 'Custom Gaming Rule'
        print("✅ Custom rule addition test passed")
    
    def test_judgment_statistics(self):
        """Test judgment statistics collection"""
        stats = self.engine.get_judgment_statistics()
        
        assert 'total_judgments' in stats
        assert 'action_distribution' in stats
        assert 'action_percentages' in stats
        assert 'emergency_flags' in stats
        assert 'configuration' in stats
        assert stats['configuration']['age_group'] == 'elementary'
        assert stats['configuration']['strictness_level'] == 'moderate'
        print("✅ Judgment statistics test passed")
    
    def test_configuration_updates(self):
        """Test configuration updates"""
        # Test age group update
        self.engine.configure_judgment_settings(age_group='high_school')
        assert self.engine.config.age_group == AgeGroup.HIGH_SCHOOL
        
        # Test strictness level update
        self.engine.configure_judgment_settings(strictness_level='strict')
        assert self.engine.config.strictness_level == StrictnessLevel.STRICT
        
        # Test emergency keywords update
        new_keywords = ['test_keyword', 'another_keyword']
        self.engine.configure_judgment_settings(emergency_keywords=new_keywords)
        assert self.engine.config.emergency_keywords == new_keywords
        print("✅ Configuration updates test passed")

class TestJudgmentEngineHelper:
    """Test suite for Judgment Engine Helper class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.helper = JudgmentEngineHelper()
    
    @pytest.mark.asyncio
    async def test_helper_initialization(self):
        """Test helper initialization"""
        assert self.helper.judgment_engine is not None
        assert isinstance(self.helper.judgment_engine, JudgmentEngine)
        print("✅ Helper initialization test passed")
    
    @pytest.mark.asyncio
    async def test_helper_process_analysis(self):
        """Test helper analysis processing"""
        analysis_result = {
            'category': 'safe',
            'confidence': 0.9,
            'input_text': 'doing homework',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        result = await self.helper.process_analysis_result(analysis_result)
        
        assert result.action == JudgmentAction.ALLOW
        assert result.confidence == 0.9
        print("✅ Helper analysis processing test passed")
    
    def test_helper_statistics(self):
        """Test helper statistics"""
        stats = self.helper.get_statistics()
        assert isinstance(stats, dict)
        assert 'total_judgments' in stats
        print("✅ Helper statistics test passed")
    
    def test_helper_configuration(self):
        """Test helper configuration"""
        self.helper.configure('middle_school', 'lenient')
        assert self.helper.judgment_engine.config.age_group == AgeGroup.MIDDLE_SCHOOL
        assert self.helper.judgment_engine.config.strictness_level == StrictnessLevel.LENIENT
        print("✅ Helper configuration test passed")

class TestJudgmentADKTools:
    """Test suite for ADK Function Tools"""
    
    @pytest.mark.asyncio
    async def test_judge_content_tool(self):
        """Test judge content ADK tool"""
        analysis_result = {
            'category': 'educational',
            'confidence': 0.8,
            'input_text': 'learning math',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        result = await judge_content_tool(analysis_result)
        
        assert result['status'] == 'success'
        assert result['action'] == 'allow'
        assert result['confidence'] == 0.8
        assert 'reasoning' in result
        assert 'applied_rules' in result
        print("✅ Judge content tool test passed")
    
    @pytest.mark.asyncio
    async def test_statistics_tool(self):
        """Test statistics ADK tool"""
        result = await get_judgment_statistics_tool()
        
        assert result['status'] == 'success'
        assert 'statistics' in result
        assert 'total_judgments' in result['statistics']
        print("✅ Statistics tool test passed")
    
    @pytest.mark.asyncio
    async def test_configuration_tool(self):
        """Test configuration ADK tool"""
        result = await configure_judgment_tool('elementary', 'strict')
        
        assert result['status'] == 'success'
        assert result['configuration']['age_group'] == 'elementary'
        assert result['configuration']['strictness_level'] == 'strict'
        print("✅ Configuration tool test passed")
    
    @pytest.mark.asyncio
    async def test_add_rule_tool(self):
        """Test add custom rule ADK tool"""
        rule_data = {
            'rule_id': 'TEST-001',
            'name': 'Test Rule',
            'description': 'Test rule for testing',
            'conditions': {'category': 'test'},
            'action': 'monitor',
            'priority': 5
        }
        
        result = await add_custom_judgment_rule_tool(rule_data)
        
        assert result['status'] == 'success'
        assert result['rule_id'] == 'TEST-001'
        print("✅ Add rule tool test passed")
    
    @pytest.mark.asyncio
    async def test_recent_judgments_tool(self):
        """Test recent judgments ADK tool"""
        result = await get_recent_judgments_tool(5)
        
        assert result['status'] == 'success'
        assert 'judgments' in result
        assert 'count' in result
        assert isinstance(result['judgments'], list)
        print("✅ Recent judgments tool test passed")

class TestJudgmentScenarios:
    """Test suite for comprehensive judgment scenarios"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.engine = JudgmentEngine()
    
    @pytest.mark.asyncio
    async def test_comprehensive_scenarios(self):
        """Test comprehensive judgment scenarios"""
        scenarios = [
            {
                'name': 'Safe Educational Content',
                'analysis': {
                    'category': 'educational',
                    'confidence': 0.9,
                    'input_text': 'learning about space',
                    'safety_concerns': [],
                    'age_appropriateness': {'elementary': True}
                },
                'expected_action': JudgmentAction.ALLOW
            },
            {
                'name': 'Concerning Social Media',
                'analysis': {
                    'category': 'social',
                    'confidence': 0.7,
                    'input_text': 'chatting with strangers online',
                    'safety_concerns': ['social interaction'],
                    'age_appropriateness': {'elementary': False}
                },
                'expected_action': JudgmentAction.RESTRICT
            },
            {
                'name': 'Entertainment Content',
                'analysis': {
                    'category': 'entertainment',
                    'confidence': 0.8,
                    'input_text': 'watching cartoons',
                    'safety_concerns': [],
                    'age_appropriateness': {'elementary': True}
                },
                'expected_action': JudgmentAction.MONITOR
            },
            {
                'name': 'Inappropriate Content',
                'analysis': {
                    'category': 'inappropriate',
                    'confidence': 0.85,
                    'input_text': 'adult content',
                    'safety_concerns': ['inappropriate content'],
                    'age_appropriateness': {'elementary': False}
                },
                'expected_action': JudgmentAction.BLOCK
            }
        ]
        
        for scenario in scenarios:
            result = await self.engine.judge_content(scenario['analysis'])
            assert result.action == scenario['expected_action'], f"Scenario '{scenario['name']}' failed"
            print(f"✅ Scenario '{scenario['name']}' passed: {result.action.value}")
    
    @pytest.mark.asyncio
    async def test_rule_priority_system(self):
        """Test rule priority system"""
        # Add high priority custom rule
        high_priority_rule = {
            'rule_id': 'HIGH-001',
            'name': 'High Priority Test',
            'description': 'High priority rule for testing',
            'conditions': {'category': 'educational'},
            'action': 'restrict',  # Override normal allow for educational
            'priority': 50,  # Very high priority
            'enabled': True
        }
        
        self.engine.add_custom_rule(high_priority_rule)
        
        # Test that high priority rule overrides default
        analysis = {
            'category': 'educational',
            'confidence': 0.9,
            'input_text': 'learning',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        result = await self.engine.judge_content(analysis)
        assert result.action == JudgmentAction.RESTRICT
        assert 'HIGH-001' in result.applied_rules
        print("✅ Rule priority system test passed")

def test_judgment_agent_creation():
    """Test ADK agent creation"""
    agent = create_judgment_agent()
    
    assert agent.name == "JudgmentAgent"
    assert len(agent.tools) == 5
    assert agent.model == "gemini-2.0-flash"
    print("✅ Judgment agent creation test passed")

# Performance and stress tests
class TestJudgmentPerformance:
    """Test suite for performance and stress testing"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.engine = JudgmentEngine()
    
    @pytest.mark.asyncio
    async def test_judgment_performance(self):
        """Test judgment performance with multiple requests"""
        import time
        
        analysis_result = {
            'category': 'educational',
            'confidence': 0.8,
            'input_text': 'learning',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        # Test 100 judgments
        start_time = time.time()
        for i in range(100):
            result = await self.engine.judge_content(analysis_result)
            assert result.action == JudgmentAction.ALLOW
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        assert avg_time < 0.1  # Should be less than 100ms per judgment
        print(f"✅ Performance test passed: {avg_time:.4f}s average per judgment")
    
    def test_rule_matching_performance(self):
        """Test rule matching performance with many rules"""
        # Add many custom rules
        for i in range(100):
            rule_data = {
                'rule_id': f'PERF-{i:03d}',
                'name': f'Performance Test Rule {i}',
                'description': f'Rule {i} for performance testing',
                'conditions': {'category': f'test_{i}'},
                'action': 'monitor',
                'priority': i,
                'enabled': True
            }
            self.engine.add_custom_rule(rule_data)
        
        # Test that rule matching is still fast
        analysis = {
            'category': 'educational',
            'confidence': 0.8,
            'input_text': 'learning',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        import time
        start_time = time.time()
        applicable_rules = self.engine._find_applicable_rules(analysis)
        end_time = time.time()
        
        assert (end_time - start_time) < 0.01  # Should be less than 10ms
        assert len(applicable_rules) > 0
        print(f"✅ Rule matching performance test passed: {len(self.engine.rules)} total rules")

# Main test runner
if __name__ == "__main__":
    async def run_all_tests():
        """Run all tests"""
        print("🚀 Starting Judgment Engine Test Suite")
        print("=" * 60)
        
        # Core functionality tests
        print("\n📋 Core Functionality Tests")
        test_engine = TestJudgmentEngine()
        test_engine.setup_method()
        
        await test_engine.test_judgment_engine_initialization()
        await test_engine.test_educational_content_judgment()
        await test_engine.test_dangerous_content_judgment()
        await test_engine.test_emergency_keywords_detection()
        await test_engine.test_age_specific_rules()
        await test_engine.test_strictness_level_impact()
        await test_engine.test_low_confidence_fallback()
        test_engine.test_custom_rule_addition()
        test_engine.test_judgment_statistics()
        test_engine.test_configuration_updates()
        
        # Helper class tests
        print("\n🔧 Helper Class Tests")
        test_helper = TestJudgmentEngineHelper()
        test_helper.setup_method()
        
        await test_helper.test_helper_initialization()
        await test_helper.test_helper_process_analysis()
        test_helper.test_helper_statistics()
        test_helper.test_helper_configuration()
        
        # ADK tools tests
        print("\n🛠️  ADK Tools Tests")
        test_adk = TestJudgmentADKTools()
        
        await test_adk.test_judge_content_tool()
        await test_adk.test_statistics_tool()
        await test_adk.test_configuration_tool()
        await test_adk.test_add_rule_tool()
        await test_adk.test_recent_judgments_tool()
        
        # Scenario tests
        print("\n🎯 Scenario Tests")
        test_scenarios = TestJudgmentScenarios()
        test_scenarios.setup_method()
        
        await test_scenarios.test_comprehensive_scenarios()
        await test_scenarios.test_rule_priority_system()
        
        # Agent creation test
        print("\n🤖 Agent Creation Tests")
        test_judgment_agent_creation()
        
        # Performance tests
        print("\n⚡ Performance Tests")
        test_performance = TestJudgmentPerformance()
        test_performance.setup_method()
        
        await test_performance.test_judgment_performance()
        test_performance.test_rule_matching_performance()
        
        print("\n" + "=" * 60)
        print("🎉 ALL JUDGMENT ENGINE TESTS PASSED!")
        print("=" * 60)
    
    # Run tests
    asyncio.run(run_all_tests()) 