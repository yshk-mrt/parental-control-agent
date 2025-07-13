"""
Judgment Engine for Parental Control System

This engine processes analysis results and applies configurable rules to determine
appropriate parental actions. It supports age-specific rule sets and customizable
judgment criteria.
"""

import asyncio
import json
import logging
import time
import weave
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib

from google.adk import Agent, Runner
from google.adk.tools import FunctionTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Weave for tracking
try:
    weave.init("parental-control-agent")
    #logger.info("Weave initialized for Judgment Engine")
except Exception as e:
    logger.warning(f"Weave initialization failed: {e}. Continuing without Weave tracking.")

class JudgmentAction(Enum):
    """Possible parental actions"""
    ALLOW = "allow"
    MONITOR = "monitor"
    RESTRICT = "restrict"
    BLOCK = "block"

class AgeGroup(Enum):
    """Age groups for rule sets"""
    ELEMENTARY = "elementary"  # 6-12 years
    MIDDLE_SCHOOL = "middle_school"  # 13-15 years
    HIGH_SCHOOL = "high_school"  # 16-18 years

class ContentCategory(Enum):
    """Content categories from analysis"""
    SAFE = "safe"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    SOCIAL = "social"
    CONCERNING = "concerning"
    INAPPROPRIATE = "inappropriate"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"

class StrictnessLevel(Enum):
    """Strictness levels for rules"""
    LENIENT = "lenient"
    MODERATE = "moderate"
    STRICT = "strict"

@dataclass
class JudgmentRule:
    """Individual judgment rule"""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    action: JudgmentAction
    priority: int = 0  # Higher priority rules override lower ones
    age_groups: List[AgeGroup] = field(default_factory=lambda: list(AgeGroup))
    strictness_levels: List[StrictnessLevel] = field(default_factory=lambda: list(StrictnessLevel))
    enabled: bool = True

@dataclass
class JudgmentResult:
    """Result of judgment process"""
    timestamp: datetime
    action: JudgmentAction
    confidence: float
    reasoning: str
    applied_rules: List[str]
    analysis_input: Dict[str, Any]
    override_reason: Optional[str] = None
    emergency_flag: bool = False

@dataclass
class JudgmentConfig:
    """Configuration for judgment engine"""
    age_group: AgeGroup = AgeGroup.ELEMENTARY
    strictness_level: StrictnessLevel = StrictnessLevel.MODERATE
    emergency_keywords: List[str] = field(default_factory=lambda: [
        "suicide", "self-harm", "violence", "abuse", "drugs", "weapons",
        "bomb", "explosive", "kill", "hurt", "damage", "destroy", "attack",
        "weapon", "gun", "knife", "poison", "dangerous", "harmful"
    ])
    time_based_rules: bool = True
    learning_mode: bool = False
    custom_rules: List[JudgmentRule] = field(default_factory=list)

class JudgmentEngine(weave.Model):
    """
    Judgment Engine that processes analysis results and applies rules
    
    This engine:
    1. Receives analysis results from Analysis Agent
    2. Applies age-appropriate rule sets
    3. Considers strictness levels and custom rules
    4. Determines appropriate parental actions
    5. Provides detailed reasoning for decisions
    """
    
    config: Optional[JudgmentConfig] = None
    rules: List[JudgmentRule] = field(default_factory=list)
    judgment_history: List[JudgmentResult] = field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None
    
    def __init__(self, config: Optional[JudgmentConfig] = None, age_group: Optional[str] = None, strictness_level: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize configuration
        if config:
            object.__setattr__(self, 'config', config)
        elif age_group or strictness_level:
            # Create config from individual parameters
            age_group_enum = AgeGroup(age_group) if age_group else AgeGroup.ELEMENTARY
            strictness_enum = StrictnessLevel(strictness_level) if strictness_level else StrictnessLevel.MODERATE
            object.__setattr__(self, 'config', JudgmentConfig(
                age_group=age_group_enum,
                strictness_level=strictness_enum
            ))
        else:
            object.__setattr__(self, 'config', JudgmentConfig())
        
        # Initialize rules
        object.__setattr__(self, 'rules', [])
        object.__setattr__(self, 'judgment_history', [])
        object.__setattr__(self, 'stats', {
            'total_judgments': 0,
            'action_counts': {action.value: 0 for action in JudgmentAction},
            'category_actions': {},
            'emergency_flags': 0,
            'rule_usage': {}
        })
        
        # Load default rules
        self._load_default_rules()
        
        logger.info(f"Judgment Engine initialized for {self.config.age_group.value} with {self.config.strictness_level.value} strictness")
    
    def _load_default_rules(self):
        """Load default judgment rules"""
        default_rules = [
            # Educational content rules
            JudgmentRule(
                rule_id="EDU-001",
                name="Educational Content",
                description="Allow educational content with monitoring",
                conditions={
                    "category": "educational",
                    "confidence": {"min": 0.7}
                },
                action=JudgmentAction.ALLOW,
                priority=10
            ),
            
            # Safe content rules
            JudgmentRule(
                rule_id="SAFE-001",
                name="Safe Content",
                description="Allow safe content",
                conditions={
                    "category": "safe",
                    "confidence": {"min": 0.8}
                },
                action=JudgmentAction.ALLOW,
                priority=8
            ),
            
            # Entertainment rules (age-dependent)
            JudgmentRule(
                rule_id="ENT-001",
                name="Entertainment - Elementary",
                description="Monitor entertainment content for elementary students",
                conditions={
                    "category": "entertainment",
                    "confidence": {"min": 0.6}
                },
                action=JudgmentAction.MONITOR,
                priority=5,
                age_groups=[AgeGroup.ELEMENTARY],
                strictness_levels=[StrictnessLevel.MODERATE, StrictnessLevel.STRICT]
            ),
            
            JudgmentRule(
                rule_id="ENT-002",
                name="Entertainment - High School",
                description="Allow entertainment content for high school students",
                conditions={
                    "category": "entertainment",
                    "confidence": {"min": 0.6}
                },
                action=JudgmentAction.ALLOW,
                priority=5,
                age_groups=[AgeGroup.HIGH_SCHOOL],
                strictness_levels=[StrictnessLevel.LENIENT, StrictnessLevel.MODERATE]
            ),
            
            # Social content rules
            JudgmentRule(
                rule_id="SOC-001",
                name="Social Content - Elementary",
                description="Restrict social content for elementary students",
                conditions={
                    "category": "social"
                },
                action=JudgmentAction.RESTRICT,
                priority=7,
                age_groups=[AgeGroup.ELEMENTARY],
                strictness_levels=[StrictnessLevel.MODERATE, StrictnessLevel.STRICT]
            ),
            
            JudgmentRule(
                rule_id="SOC-002",
                name="Social Content - Middle/High School",
                description="Monitor social content for older students",
                conditions={
                    "category": "social"
                },
                action=JudgmentAction.MONITOR,
                priority=6,
                age_groups=[AgeGroup.MIDDLE_SCHOOL, AgeGroup.HIGH_SCHOOL],
                strictness_levels=[StrictnessLevel.LENIENT, StrictnessLevel.MODERATE]
            ),
            
            # Concerning content rules
            JudgmentRule(
                rule_id="CONC-001",
                name="Concerning Content",
                description="Block concerning content",
                conditions={
                    "category": "concerning"
                },
                action=JudgmentAction.BLOCK,
                priority=15
            ),
            
            # Inappropriate content rules
            JudgmentRule(
                rule_id="INAP-001",
                name="Inappropriate Content",
                description="Block inappropriate content",
                conditions={
                    "category": "inappropriate"
                },
                action=JudgmentAction.BLOCK,
                priority=20
            ),
            
            # Dangerous content rules
            JudgmentRule(
                rule_id="DANG-001",
                name="Dangerous Content",
                description="Block dangerous content immediately",
                conditions={
                    "category": "dangerous"
                },
                action=JudgmentAction.BLOCK,
                priority=25
            ),
            
            # Emergency keyword rules
            JudgmentRule(
                rule_id="EMERG-001",
                name="Emergency Keywords",
                description="Block content with emergency keywords",
                conditions={
                    "emergency_keywords": True
                },
                action=JudgmentAction.BLOCK,
                priority=30
            ),
            
            # Low confidence fallback
            JudgmentRule(
                rule_id="FALL-001",
                name="Low Confidence Fallback",
                description="Monitor content with low confidence",
                conditions={
                    "confidence": {"max": 0.5}
                },
                action=JudgmentAction.MONITOR,
                priority=1
            ),
            
            # Unknown content fallback
            JudgmentRule(
                rule_id="UNK-001",
                name="Unknown Content",
                description="Monitor unknown content",
                conditions={
                    "category": "unknown"
                },
                action=JudgmentAction.MONITOR,
                priority=2
            )
        ]
        
        # Add rules to engine
        for rule in default_rules:
            self.rules.append(rule)
        
        logger.info(f"Loaded {len(default_rules)} default judgment rules")
    
    @weave.op()
    async def judge_content(self, analysis_result: Dict[str, Any]) -> JudgmentResult:
        """
        Main judgment method that processes analysis results
        
        Args:
            analysis_result: Dictionary containing analysis results from Analysis Agent
            
        Returns:
            JudgmentResult with decision and reasoning
        """
        start_time = time.time()
        
        try:
            # Extract analysis data
            category = analysis_result.get('category', 'unknown')
            confidence = analysis_result.get('confidence', 0.0)
            safety_concerns = analysis_result.get('safety_concerns', [])
            input_text = analysis_result.get('input_text', '')
            
            # Check for emergency conditions
            emergency_flag = self._check_emergency_conditions(input_text, safety_concerns)
            
            # Find applicable rules
            applicable_rules = self._find_applicable_rules(analysis_result)
            
            # Apply rules to determine action
            action, reasoning, applied_rule_ids = self._apply_rules(applicable_rules, analysis_result)
            
            # Create judgment result
            result = JudgmentResult(
                timestamp=datetime.now(),
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                applied_rules=applied_rule_ids,
                analysis_input=analysis_result,
                emergency_flag=emergency_flag
            )
            
            # Update statistics
            self._update_statistics(result)
            
            # Store in history
            self.judgment_history.append(result)
            
            judgment_time = time.time() - start_time
            logger.info(f"Judgment completed in {judgment_time:.3f}s - Action: {action.value}, Category: {category}")
            
            return result
            
        except Exception as e:
            logger.error(f"Judgment error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return fallback judgment
            return JudgmentResult(
                timestamp=datetime.now(),
                action=JudgmentAction.MONITOR,
                confidence=0.0,
                reasoning=f"Judgment failed: {str(e)}. Defaulting to monitor for safety.",
                applied_rules=["FALLBACK"],
                analysis_input=analysis_result,
                emergency_flag=True
            )
    
    def _check_emergency_conditions(self, input_text: str, safety_concerns: List[str]) -> bool:
        """Check for emergency conditions"""
        # Check emergency keywords
        text_lower = input_text.lower()
        for keyword in self.config.emergency_keywords:
            if keyword.lower() in text_lower:
                logger.warning(f"Emergency keyword detected: {keyword}")
                return True
        
        # Check safety concerns
        high_risk_concerns = ["violence", "self-harm", "dangerous activities", "inappropriate content"]
        for concern in safety_concerns:
            if any(risk in concern.lower() for risk in high_risk_concerns):
                logger.warning(f"High-risk safety concern: {concern}")
                return True
        
        return False
    
    def _find_applicable_rules(self, analysis_result: Dict[str, Any]) -> List[JudgmentRule]:
        """Find rules applicable to the analysis result"""
        applicable_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check age group compatibility
            if rule.age_groups and self.config.age_group not in rule.age_groups:
                continue
            
            # Check strictness level compatibility
            if rule.strictness_levels and self.config.strictness_level not in rule.strictness_levels:
                continue
            
            # Check rule conditions
            if self._rule_matches_conditions(rule, analysis_result):
                applicable_rules.append(rule)
        
        # Sort by priority (higher priority first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable_rules
    
    def _rule_matches_conditions(self, rule: JudgmentRule, analysis_result: Dict[str, Any]) -> bool:
        """Check if a rule's conditions match the analysis result"""
        conditions = rule.conditions
        
        # Check category condition
        if "category" in conditions:
            if analysis_result.get("category") != conditions["category"]:
                return False
        
        # Check confidence conditions
        if "confidence" in conditions:
            confidence = analysis_result.get("confidence", 0.0)
            conf_conditions = conditions["confidence"]
            
            if "min" in conf_conditions and confidence < conf_conditions["min"]:
                return False
            if "max" in conf_conditions and confidence > conf_conditions["max"]:
                return False
        
        # Check emergency keywords
        if "emergency_keywords" in conditions:
            input_text = analysis_result.get("input_text", "")
            if not self._check_emergency_conditions(input_text, analysis_result.get("safety_concerns", [])):
                return False
        
        # Check safety concerns
        if "safety_concerns" in conditions:
            safety_concerns = analysis_result.get("safety_concerns", [])
            required_concerns = conditions["safety_concerns"]
            
            if isinstance(required_concerns, list):
                if not any(concern in safety_concerns for concern in required_concerns):
                    return False
            elif isinstance(required_concerns, str):
                if required_concerns not in safety_concerns:
                    return False
        
        return True
    
    def _apply_rules(self, applicable_rules: List[JudgmentRule], analysis_result: Dict[str, Any]) -> Tuple[JudgmentAction, str, List[str]]:
        """Apply rules to determine action"""
        if not applicable_rules:
            # No applicable rules - default to monitor
            return JudgmentAction.MONITOR, "No applicable rules found. Defaulting to monitor for safety.", ["DEFAULT"]
        
        # Use highest priority rule
        primary_rule = applicable_rules[0]
        action = primary_rule.action
        applied_rule_ids = [primary_rule.rule_id]
        
        # Build reasoning
        reasoning_parts = [f"Applied rule: {primary_rule.name} - {primary_rule.description}"]
        
        # Add context from analysis
        category = analysis_result.get("category", "unknown")
        confidence = analysis_result.get("confidence", 0.0)
        reasoning_parts.append(f"Content category: {category} (confidence: {confidence:.2f})")
        
        # Add safety concerns if any
        safety_concerns = analysis_result.get("safety_concerns", [])
        if safety_concerns:
            reasoning_parts.append(f"Safety concerns: {', '.join(safety_concerns)}")
        
        # Add age and strictness context
        reasoning_parts.append(f"Age group: {self.config.age_group.value}, Strictness: {self.config.strictness_level.value}")
        
        # Check for rule conflicts and escalation
        for rule in applicable_rules[1:]:
            if rule.action.value != action.value and rule.priority >= primary_rule.priority - 5:
                # Close priority rules with different actions - escalate to more restrictive
                if self._is_more_restrictive(rule.action, action):
                    action = rule.action
                    applied_rule_ids.append(rule.rule_id)
                    reasoning_parts.append(f"Escalated due to conflicting rule: {rule.name}")
        
        reasoning = " | ".join(reasoning_parts)
        
        return action, reasoning, applied_rule_ids
    
    def _is_more_restrictive(self, action1: JudgmentAction, action2: JudgmentAction) -> bool:
        """Check if action1 is more restrictive than action2"""
        restrictiveness = {
            JudgmentAction.ALLOW: 0,
            JudgmentAction.MONITOR: 1,
            JudgmentAction.RESTRICT: 2,
            JudgmentAction.BLOCK: 3
        }
        
        return restrictiveness[action1] > restrictiveness[action2]
    
    def _update_statistics(self, result: JudgmentResult):
        """Update judgment statistics"""
        # Create a new stats dict to avoid Weave tracking issues
        new_stats = dict(self.stats)
        
        new_stats['total_judgments'] += 1
        new_stats['action_counts'][result.action.value] += 1
        
        if result.emergency_flag:
            new_stats['emergency_flags'] += 1
        
        # Update category-action mapping
        category = result.analysis_input.get('category', 'unknown')
        if category not in new_stats['category_actions']:
            new_stats['category_actions'][category] = {action.value: 0 for action in JudgmentAction}
        new_stats['category_actions'][category][result.action.value] += 1
        
        # Update rule usage
        for rule_id in result.applied_rules:
            new_stats['rule_usage'][rule_id] = new_stats['rule_usage'].get(rule_id, 0) + 1
        
        # Update the stats object
        object.__setattr__(self, 'stats', new_stats)
    
    @weave.op()
    def get_judgment_statistics(self) -> Dict[str, Any]:
        """Get comprehensive judgment statistics"""
        total = self.stats['total_judgments']
        
        return {
            'total_judgments': total,
            'action_distribution': self.stats['action_counts'],
            'action_percentages': {
                action: (count / max(total, 1)) * 100 
                for action, count in self.stats['action_counts'].items()
            },
            'category_actions': self.stats['category_actions'],
            'emergency_flags': self.stats['emergency_flags'],
            'emergency_rate': (self.stats['emergency_flags'] / max(total, 1)) * 100,
            'rule_usage': self.stats['rule_usage'],
            'most_used_rules': sorted(
                self.stats['rule_usage'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'configuration': {
                'age_group': self.config.age_group.value,
                'strictness_level': self.config.strictness_level.value,
                'total_rules': len(self.rules),
                'enabled_rules': len([r for r in self.rules if r.enabled])
            }
        }
    
    @weave.op()
    def configure_judgment_settings(self, 
                                   age_group: Optional[str] = None,
                                   strictness_level: Optional[str] = None,
                                   emergency_keywords: Optional[List[str]] = None):
        """Configure judgment settings"""
        if age_group:
            try:
                new_age_group = AgeGroup(age_group)
                object.__setattr__(self, 'config', JudgmentConfig(
                    age_group=new_age_group,
                    strictness_level=self.config.strictness_level,
                    emergency_keywords=self.config.emergency_keywords,
                    time_based_rules=self.config.time_based_rules,
                    learning_mode=self.config.learning_mode,
                    custom_rules=self.config.custom_rules
                ))
                logger.info(f"Age group updated to: {age_group}")
            except ValueError:
                logger.error(f"Invalid age group: {age_group}")
        
        if strictness_level:
            try:
                new_strictness = StrictnessLevel(strictness_level)
                object.__setattr__(self, 'config', JudgmentConfig(
                    age_group=self.config.age_group,
                    strictness_level=new_strictness,
                    emergency_keywords=self.config.emergency_keywords,
                    time_based_rules=self.config.time_based_rules,
                    learning_mode=self.config.learning_mode,
                    custom_rules=self.config.custom_rules
                ))
                logger.info(f"Strictness level updated to: {strictness_level}")
            except ValueError:
                logger.error(f"Invalid strictness level: {strictness_level}")
        
        if emergency_keywords:
            updated_config = JudgmentConfig(
                age_group=self.config.age_group,
                strictness_level=self.config.strictness_level,
                emergency_keywords=emergency_keywords,
                time_based_rules=self.config.time_based_rules,
                learning_mode=self.config.learning_mode,
                custom_rules=self.config.custom_rules
            )
            object.__setattr__(self, 'config', updated_config)
            logger.info(f"Emergency keywords updated: {len(emergency_keywords)} keywords")
    
    @weave.op()
    def add_custom_rule(self, rule: Dict[str, Any]) -> bool:
        """Add a custom judgment rule"""
        try:
            custom_rule = JudgmentRule(
                rule_id=rule['rule_id'],
                name=rule['name'],
                description=rule['description'],
                conditions=rule['conditions'],
                action=JudgmentAction(rule['action']),
                priority=rule.get('priority', 0),
                age_groups=[AgeGroup(ag) for ag in rule.get('age_groups', [])],
                strictness_levels=[StrictnessLevel(sl) for sl in rule.get('strictness_levels', [])],
                enabled=rule.get('enabled', True)
            )
            
            self.rules.append(custom_rule)
            logger.info(f"Added custom rule: {custom_rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom rule: {e}")
            return False
    
    @weave.op()
    def get_recent_judgments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent judgment results"""
        recent = self.judgment_history[-limit:] if len(self.judgment_history) >= limit else self.judgment_history
        
        return [
            {
                'timestamp': result.timestamp.isoformat(),
                'action': result.action.value,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'applied_rules': result.applied_rules,
                'category': result.analysis_input.get('category', 'unknown'),
                'emergency_flag': result.emergency_flag
            }
            for result in reversed(recent)
        ] 

# ADK FunctionTool implementations

@weave.op()
async def judge_content_tool(analysis_result: Dict[str, Any], 
                           age_group: Optional[str] = None,
                           strictness_level: Optional[str] = None) -> Dict[str, Any]:
    """
    Judge content based on analysis results
    
    Args:
        analysis_result: Analysis result from Analysis Agent
        age_group: Optional age group override
        strictness_level: Optional strictness level override
        
    Returns:
        Dictionary with judgment results
    """
    try:
        # Get or create judgment engine
        engine = get_global_judgment_engine()
        
        # Configure if overrides provided
        if age_group or strictness_level:
            engine.configure_judgment_settings(age_group, strictness_level)
        
        # Perform judgment
        result = await engine.judge_content(analysis_result)
        
        return {
            'status': 'success',
            'action': result.action.value,
            'confidence': result.confidence,
            'reasoning': result.reasoning,
            'applied_rules': result.applied_rules,
            'emergency_flag': result.emergency_flag,
            'timestamp': result.timestamp.isoformat(),
            'category': analysis_result.get('category', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Judgment tool error: {e}")
        return {
            'status': 'error',
            'message': f"Judgment failed: {str(e)}",
            'action': 'monitor',  # Safe fallback
            'emergency_flag': True
        }

@weave.op()
async def get_judgment_statistics_tool() -> Dict[str, Any]:
    """
    Get judgment statistics and performance metrics
    
    Returns:
        Dictionary with comprehensive statistics
    """
    try:
        engine = get_global_judgment_engine()
        stats = engine.get_judgment_statistics()
        
        return {
            'status': 'success',
            'statistics': stats
        }
        
    except Exception as e:
        logger.error(f"Statistics tool error: {e}")
        return {
            'status': 'error',
            'message': f"Failed to get statistics: {str(e)}"
        }

@weave.op()
async def configure_judgment_tool(age_group: str, 
                                strictness_level: str,
                                emergency_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Configure judgment engine settings
    
    Args:
        age_group: Target age group (elementary, middle_school, high_school)
        strictness_level: Strictness level (lenient, moderate, strict)
        emergency_keywords: Optional custom emergency keywords
        
    Returns:
        Configuration status
    """
    try:
        engine = get_global_judgment_engine()
        engine.configure_judgment_settings(age_group, strictness_level, emergency_keywords)
        
        return {
            'status': 'success',
            'configuration': {
                'age_group': age_group,
                'strictness_level': strictness_level,
                'emergency_keywords': emergency_keywords or engine.config.emergency_keywords
            },
            'message': f'Judgment engine configured for {age_group} with {strictness_level} strictness'
        }
        
    except Exception as e:
        logger.error(f"Configuration tool error: {e}")
        return {
            'status': 'error',
            'message': f"Configuration failed: {str(e)}"
        }

@weave.op()
async def add_custom_judgment_rule_tool(rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add custom judgment rule
    
    Args:
        rule_data: Rule configuration dictionary
        
    Returns:
        Rule addition status
    """
    try:
        engine = get_global_judgment_engine()
        success = engine.add_custom_rule(rule_data)
        
        if success:
            return {
                'status': 'success',
                'message': f"Custom rule '{rule_data['name']}' added successfully",
                'rule_id': rule_data['rule_id']
            }
        else:
            return {
                'status': 'error',
                'message': "Failed to add custom rule"
            }
            
    except Exception as e:
        logger.error(f"Add rule tool error: {e}")
        return {
            'status': 'error',
            'message': f"Failed to add rule: {str(e)}"
        }

@weave.op()
async def get_recent_judgments_tool(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent judgment results
    
    Args:
        limit: Maximum number of recent judgments to return
        
    Returns:
        Recent judgment results
    """
    try:
        engine = get_global_judgment_engine()
        recent_judgments = engine.get_recent_judgments(limit)
        
        return {
            'status': 'success',
            'judgments': recent_judgments,
            'count': len(recent_judgments)
        }
        
    except Exception as e:
        logger.error(f"Recent judgments tool error: {e}")
        return {
            'status': 'error',
            'message': f"Failed to get recent judgments: {str(e)}"
        }

# Create ADK Function Tools
judge_content_function_tool = FunctionTool(func=judge_content_tool)
get_judgment_statistics_function_tool = FunctionTool(func=get_judgment_statistics_tool)
configure_judgment_function_tool = FunctionTool(func=configure_judgment_tool)
add_custom_judgment_rule_function_tool = FunctionTool(func=add_custom_judgment_rule_tool)
get_recent_judgments_function_tool = FunctionTool(func=get_recent_judgments_tool)

# Global judgment engine instance
_global_judgment_engine = None

def get_global_judgment_engine() -> JudgmentEngine:
    """Get or create global judgment engine instance"""
    global _global_judgment_engine
    if _global_judgment_engine is None:
        _global_judgment_engine = JudgmentEngine()
    return _global_judgment_engine

def create_judgment_agent() -> Agent:
    """Create a Judgment Agent for parental control system"""
    
    return Agent(
        name="JudgmentAgent",
        model="gemini-1.5-flash",
        description="A judgment agent that processes content analysis and determines appropriate parental actions",
        instruction="""
        You are a specialized AI agent for parental control judgment and decision-making.
        
        Your capabilities include:
        1. judge_content: Process analysis results and determine appropriate parental actions
        2. get_judgment_statistics: Get judgment statistics and performance metrics
        3. configure_judgment: Configure age group, strictness level, and emergency keywords
        4. add_custom_judgment_rule: Add custom judgment rules for specific scenarios
        5. get_recent_judgments: Get recent judgment results for review
        
        Your judgment focuses on:
        - Age-appropriate content assessment
        - Parental action determination (allow, monitor, restrict, block)
        - Emergency situation detection
        - Rule-based decision making
        - Context-aware judgment with detailed reasoning
        
        You apply configurable rules based on:
        - Content category (safe, educational, entertainment, social, concerning, inappropriate, dangerous)
        - Age group (elementary, middle_school, high_school)
        - Strictness level (lenient, moderate, strict)
        - Confidence levels and safety concerns
        - Emergency keywords and high-risk content
        
        Always provide clear reasoning for your judgments and maintain consistency in rule application.
        Prioritize child safety while respecting age-appropriate freedom and learning opportunities.
        """,
        tools=[
            judge_content_function_tool,
            get_judgment_statistics_function_tool,
            configure_judgment_function_tool,
            add_custom_judgment_rule_function_tool,
            get_recent_judgments_function_tool
        ]
    )

# Helper class for direct usage (non-ADK)
class JudgmentEngineHelper:
    """
    Helper class for direct usage of Judgment Engine functionality
    
    This class provides a simple interface for using the Judgment Engine
    without ADK integration.
    """
    
    def __init__(self, config: Optional[JudgmentConfig] = None):
        self.judgment_engine = JudgmentEngine(config)
        logger.info("Judgment Engine Helper initialized")
    
    @weave.op()
    async def process_analysis_result(self, analysis_result: Dict[str, Any]) -> JudgmentResult:
        """
        Process an analysis result and return judgment
        
        Args:
            analysis_result: Analysis result from Analysis Agent
            
        Returns:
            JudgmentResult with action and reasoning
        """
        return await self.judgment_engine.judge_content(analysis_result)
    
    @weave.op()
    def get_statistics(self) -> Dict[str, Any]:
        """Get judgment statistics"""
        return self.judgment_engine.get_judgment_statistics()
    
    @weave.op()
    def configure(self, age_group: str, strictness_level: str, emergency_keywords: Optional[List[str]] = None):
        """Configure judgment settings"""
        self.judgment_engine.configure_judgment_settings(age_group, strictness_level, emergency_keywords)
    
    @weave.op()
    def add_rule(self, rule_data: Dict[str, Any]) -> bool:
        """Add custom rule"""
        return self.judgment_engine.add_custom_rule(rule_data)

# Example usage and testing
if __name__ == "__main__":
    async def test_judgment_engine():
        """Test the Judgment Engine functionality"""
        print("Testing Judgment Engine...")
        
        # Create engine helper
        engine_helper = JudgmentEngineHelper()
        
        # Test ADK agent creation
        print("\n1. Testing ADK agent creation...")
        adk_agent = create_judgment_agent()
        print(f"   Agent name: {adk_agent.name}")
        print(f"   Tool count: {len(adk_agent.tools)}")
        
        # Test configuration
        print("\n2. Testing configuration...")
        engine_helper.configure("elementary", "strict")
        
        # Test judgment
        print("\n3. Testing judgment...")
        sample_analysis = {
            'category': 'educational',
            'confidence': 0.85,
            'input_text': 'I am learning about dinosaurs',
            'safety_concerns': [],
            'age_appropriateness': {'elementary': True}
        }
        
        result = await engine_helper.process_analysis_result(sample_analysis)
        print(f"   Action: {result.action.value}")
        print(f"   Reasoning: {result.reasoning}")
        
        # Test statistics
        print("\n4. Testing statistics...")
        stats = engine_helper.get_statistics()
        print(f"   Total judgments: {stats['total_judgments']}")
        print(f"   Action distribution: {stats['action_distribution']}")
        
        print("\nJudgment Engine test completed!")
    
    # Run test
    asyncio.run(test_judgment_engine()) 