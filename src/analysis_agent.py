"""
Analysis Agent for Parental Control System

This agent coordinates the analysis of user input and screen content using
the Gemini multimodal tool. It provides context analysis, application detection,
and content assessment capabilities.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
import os

from google.adk import Agent, Runner
from google.adk.tools import FunctionTool

from gemini_multimodal import (
    GeminiMultimodalAnalyzer,
    analyze_text_content_tool,
    analyze_multimodal_content_tool,
    get_analysis_summary_tool,
    configure_analysis_settings_tool
)
from screen_capture import (
    capture_screen_tool,
    get_monitor_info_tool,
    cleanup_temp_files_tool
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Structured result from content analysis"""
    timestamp: datetime
    input_text: str
    screenshot_path: Optional[str]
    category: str
    confidence: float
    age_appropriateness: Dict[str, Any]
    safety_concerns: List[str]
    educational_value: str
    parental_action: str
    context_summary: str
    application_detected: str
    detailed_analysis: Dict[str, Any]

@dataclass
class ApplicationContext:
    """Information about the detected application"""
    name: str
    type: str  # browser, application, game, etc.
    url: Optional[str]  # if browser
    confidence: float
    context_clues: List[str]

class AnalysisCache:
    """Simple cache for analysis results to improve performance"""
    
    def __init__(self, cache_dir: str = "temp/analysis_cache", max_age_minutes: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(minutes=max_age_minutes)
    
    def _get_cache_key(self, input_text: str, screenshot_path: Optional[str]) -> str:
        """Generate cache key from input and screenshot"""
        content = input_text or ""
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                content += f.read().hex()[:100]  # First 100 chars of hex
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, input_text: str, screenshot_path: Optional[str]) -> Optional[AnalysisResult]:
        """Get cached analysis result"""
        try:
            cache_key = self._get_cache_key(input_text, screenshot_path)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if not cache_file.exists():
                return None
            
            # Check if cache is still valid
            if datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime) > self.max_age:
                cache_file.unlink()  # Remove expired cache
                return None
            
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, input_text: str, screenshot_path: Optional[str], result: AnalysisResult):
        """Cache analysis result"""
        try:
            cache_key = self._get_cache_key(input_text, screenshot_path)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def cleanup_old_cache(self):
        """Remove old cache files"""
        try:
            cutoff_time = datetime.now() - self.max_age
            for cache_file in self.cache_dir.glob("*.pkl"):
                if datetime.fromtimestamp(cache_file.stat().st_mtime) < cutoff_time:
                    cache_file.unlink()
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")

class AnalysisAgent:
    """
    Analysis Agent that coordinates content analysis using Gemini multimodal tool
    
    This agent:
    1. Receives input text and screenshot data
    2. Analyzes content using Gemini multimodal AI
    3. Detects applications and context
    4. Provides structured analysis results
    5. Caches results for performance
    """
    
    def __init__(self, 
                 age_group: str = "elementary",
                 strictness_level: str = "moderate",
                 cache_enabled: bool = True):
        self.age_group = age_group
        self.strictness_level = strictness_level
        self.cache_enabled = cache_enabled
        
        # Initialize cache
        if cache_enabled:
            self.cache = AnalysisCache()
        
        # Initialize tools
        self.gemini_tool = GeminiMultimodalAnalyzer()
        
        # Analysis statistics
        self.stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'categories': {}
        }
        
        logger.info(f"Analysis Agent initialized for {age_group} with {strictness_level} strictness")
    
    async def analyze_input_context(self, 
                                  input_text: str, 
                                  screenshot_path: Optional[str] = None) -> AnalysisResult:
        """
        Analyze input text and screen context
        
        Args:
            input_text: The keyboard input text to analyze
            screenshot_path: Optional path to screenshot image
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        try:
            # Check cache first
            if self.cache_enabled:
                cached_result = self.cache.get(input_text, screenshot_path)
                if cached_result:
                    self.stats['cache_hits'] += 1
                    logger.info("Analysis result retrieved from cache")
                    return cached_result
                self.stats['cache_misses'] += 1
            
            # Perform analysis
            start_time = time.time()
            
            # Use multimodal analysis if we have both text and image
            if screenshot_path and os.path.exists(screenshot_path):
                analysis_result = await self._analyze_multimodal_content(input_text, screenshot_path)
            else:
                analysis_result = await self._analyze_text_content(input_text)
            
            # Detect application context
            app_context = await self._detect_application_context(screenshot_path)
            
            # Create structured result
            result = AnalysisResult(
                timestamp=datetime.now(),
                input_text=input_text,
                screenshot_path=screenshot_path,
                category=analysis_result.get('category', 'unknown'),
                confidence=analysis_result.get('confidence', 0.0),
                age_appropriateness=analysis_result.get('age_appropriateness', {}),
                safety_concerns=analysis_result.get('safety_concerns', []),
                educational_value=analysis_result.get('educational_value', ''),
                parental_action=analysis_result.get('parental_action', 'monitor'),
                context_summary=analysis_result.get('context_summary', ''),
                application_detected=app_context.name if app_context else 'unknown',
                detailed_analysis=analysis_result
            )
            
            # Cache the result
            if self.cache_enabled:
                self.cache.set(input_text, screenshot_path, result)
            
            # Update statistics
            self.stats['total_analyses'] += 1
            category = result.category
            self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
            
            analysis_time = time.time() - start_time
            logger.info(f"Analysis completed in {analysis_time:.2f}s - Category: {category}, Action: {result.parental_action}")
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Analysis error: {e}")
            
            # Return safe fallback result
            return AnalysisResult(
                timestamp=datetime.now(),
                input_text=input_text,
                screenshot_path=screenshot_path,
                category='unknown',
                confidence=0.0,
                age_appropriateness={},
                safety_concerns=['Analysis failed - manual review recommended'],
                educational_value='Unknown',
                parental_action='monitor',
                context_summary='Analysis failed due to technical error',
                application_detected='unknown',
                detailed_analysis={'error': str(e)}
            )
    
    async def _analyze_multimodal_content(self, input_text: str, screenshot_path: str) -> Dict[str, Any]:
        """Analyze content using both text and image"""
        try:
            # Create a mock ToolContext for configuration
            class MockToolContext:
                def __init__(self):
                    self.state = {}
            
            tool_context = MockToolContext()
            tool_context.state = {
                'target_age_group': self.age_group,
                'strict_mode': self.strictness_level == 'strict'
            }
            
            # Configure analysis settings
            configure_analysis_settings_tool(tool_context)
            
            # Create tool context for multimodal analysis
            tool_context.state.update({
                'current_input_text': input_text,
                'current_screenshot_path': screenshot_path
            })
            
            # Perform multimodal analysis
            result = analyze_multimodal_content_tool(tool_context)
            
            return result.get('analysis', {})
            
        except Exception as e:
            logger.error(f"Multimodal analysis error: {e}")
            # Fallback to text-only analysis
            return await self._analyze_text_content(input_text)
    
    async def _analyze_text_content(self, input_text: str) -> Dict[str, Any]:
        """Analyze text content only"""
        try:
            # Create a mock ToolContext for configuration
            class MockToolContext:
                def __init__(self):
                    self.state = {}
            
            tool_context = MockToolContext()
            tool_context.state = {
                'target_age_group': self.age_group,
                'strict_mode': self.strictness_level == 'strict'
            }
            
            # Configure analysis settings
            configure_analysis_settings_tool(tool_context)
            
            # Create tool context for text analysis
            tool_context.state.update({
                'current_input_text': input_text
            })
            
            # Perform text analysis
            result = analyze_text_content_tool(tool_context)
            
            return result.get('analysis', {})
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'parental_action': 'monitor',
                'context_summary': f'Analysis failed: {str(e)}'
            }
    
    async def _detect_application_context(self, screenshot_path: Optional[str]) -> Optional[ApplicationContext]:
        """Detect current application from screenshot"""
        if not screenshot_path or not os.path.exists(screenshot_path):
            return None
        
        try:
            # Use Gemini to analyze the screenshot for application context
            app_analysis_prompt = """
            Analyze this screenshot and identify:
            1. What application or website is being used?
            2. What type of application is it (browser, game, educational software, etc.)?
            3. If it's a browser, what website or service is being accessed?
            4. What context clues led to this identification?
            
            Respond in JSON format:
            {
                "application_name": "name of application",
                "application_type": "browser/game/educational/productivity/social/other",
                "website_url": "if browser, the website being accessed",
                "confidence": 0.95,
                "context_clues": ["list of visual clues that led to identification"]
            }
            """
            
            # This would use the Gemini tool to analyze the screenshot
            # For now, we'll implement a simple heuristic approach
            return ApplicationContext(
                name="Unknown Application",
                type="unknown",
                url=None,
                confidence=0.5,
                context_clues=["Screenshot analysis not yet implemented"]
            )
            
        except Exception as e:
            logger.error(f"Application detection error: {e}")
            return None
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        cache_hit_rate = 0.0
        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
        
        return {
            'total_analyses': self.stats['total_analyses'],
            'cache_hit_rate': cache_hit_rate,
            'error_rate': self.stats['errors'] / max(1, self.stats['total_analyses']),
            'category_distribution': self.stats['categories'],
            'cache_enabled': self.cache_enabled
        }
    
    def configure_settings(self, age_group: str, strictness_level: str):
        """Update analysis settings"""
        self.age_group = age_group
        self.strictness_level = strictness_level
        logger.info(f"Analysis settings updated: {age_group}, {strictness_level}")
    
    def cleanup_cache(self):
        """Clean up old cache files"""
        if self.cache_enabled:
            self.cache.cleanup_old_cache()
            logger.info("Cache cleanup completed")

# ADK FunctionTool implementations

async def analyze_input_context_tool(input_text: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze input text and screen context using Analysis Agent
    
    Args:
        input_text: The keyboard input text to analyze
        screenshot_path: Optional path to screenshot image
        
    Returns:
        Dictionary with analysis results
    """
    agent = get_global_analysis_engine()
    result = await agent.analyze_input_context(input_text, screenshot_path)
    
    return {
        'timestamp': result.timestamp.isoformat(),
        'category': result.category,
        'confidence': result.confidence,
        'age_appropriateness': result.age_appropriateness,
        'safety_concerns': result.safety_concerns,
        'educational_value': result.educational_value,
        'parental_action': result.parental_action,
        'context_summary': result.context_summary,
        'application_detected': result.application_detected
    }

async def get_analysis_statistics_tool() -> Dict[str, Any]:
    """Get analysis statistics from the Analysis Agent"""
    agent = get_global_analysis_engine()
    return agent.get_analysis_statistics()

async def configure_analysis_agent_tool(age_group: str, strictness_level: str) -> Dict[str, str]:
    """
    Configure Analysis Agent settings
    
    Args:
        age_group: Target age group (elementary, middle_school, high_school)
        strictness_level: Strictness level (lenient, moderate, strict)
        
    Returns:
        Configuration status
    """
    agent = get_global_analysis_engine()
    agent.configure_settings(age_group, strictness_level)
    
    return {
        'status': 'success',
        'age_group': age_group,
        'strictness_level': strictness_level,
        'message': f'Analysis agent configured for {age_group} with {strictness_level} strictness'
    }

async def cleanup_analysis_cache_tool() -> Dict[str, str]:
    """Clean up old analysis cache files"""
    agent = get_global_analysis_engine()
    agent.cleanup_cache()
    
    return {
        'status': 'success',
        'message': 'Analysis cache cleaned up successfully'
    }

# Create FunctionTool instances
analyze_input_context_function_tool = FunctionTool(func=analyze_input_context_tool)
get_analysis_statistics_function_tool = FunctionTool(func=get_analysis_statistics_tool)
configure_analysis_agent_function_tool = FunctionTool(func=configure_analysis_agent_tool)
cleanup_analysis_cache_function_tool = FunctionTool(func=cleanup_analysis_cache_tool)

# Global analysis engine instance for ADK integration
_global_analysis_engine = None

def get_global_analysis_engine() -> AnalysisAgent:
    """Get or create global analysis engine instance"""
    global _global_analysis_engine
    if _global_analysis_engine is None:
        _global_analysis_engine = AnalysisAgent()
    return _global_analysis_engine

# Analysis Agent factory function for ADK integration
def create_analysis_agent() -> Agent:
    """Create an Analysis Agent for parental control system"""
    
    return Agent(
        name="AnalysisAgent",
        model="gemini-2.0-flash",
        description="A comprehensive analysis agent that coordinates content analysis using multimodal AI for parental control assessment",
        instruction="""
        You are a specialized AI agent for parental control content analysis and child safety assessment.
        
        Your capabilities include:
        1. analyze_input_context: Analyze keyboard input and screen context for comprehensive assessment
        2. get_analysis_statistics: Get analysis statistics and performance metrics
        3. configure_analysis_agent: Configure analysis settings for age group and strictness
        4. cleanup_analysis_cache: Clean up old analysis cache files
        5. analyze_text_content: Analyze text content for age-appropriateness
        6. analyze_multimodal_content: Analyze text and images together
        7. get_analysis_summary: Generate usage patterns and trends
        8. configure_analysis_settings: Adjust Gemini analysis parameters
        9. capture_screen: Take screenshots for context analysis
        10. get_monitor_info: Get monitor information
        11. cleanup_temp_files: Clean up temporary files
        
        Your analysis focuses on:
        - Age-appropriate content assessment
        - Safety concerns (violence, adult content, inappropriate language, dangerous activities)
        - Educational value assessment
        - Context understanding (what the child is doing/viewing)
        - Application detection and context analysis
        - Performance optimization through caching
        - Parental action recommendations (allow, monitor, restrict, block)
        
        Always provide clear, actionable recommendations for parents while maintaining child privacy and safety.
        Use multimodal analysis when both text and image data are available for the most comprehensive assessment.
        Cache results for performance optimization while respecting privacy.
        """,
        tools=[
            analyze_input_context_function_tool,
            get_analysis_statistics_function_tool,
            configure_analysis_agent_function_tool,
            cleanup_analysis_cache_function_tool,
            analyze_text_content_tool,
            analyze_multimodal_content_tool,
            get_analysis_summary_tool,
            configure_analysis_settings_tool,
            capture_screen_tool,
            get_monitor_info_tool,
            cleanup_temp_files_tool
        ]
    )

# Helper class for direct usage (non-ADK)
class AnalysisAgentHelper:
    """
    Helper class for direct usage of Analysis Agent functionality
    
    This class provides a simple interface for using the Analysis Agent
    without ADK integration.
    """
    
    def __init__(self):
        self.analysis_engine = get_global_analysis_engine()
        logger.info("Analysis Agent Helper initialized")
    
    async def process_input_event(self, input_text: str, screenshot_path: Optional[str] = None) -> AnalysisResult:
        """
        Process an input event and return analysis results
        
        Args:
            input_text: The keyboard input text
            screenshot_path: Optional screenshot path
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        return await self.analysis_engine.analyze_input_context(input_text, screenshot_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return self.analysis_engine.get_analysis_statistics()
    
    def configure(self, age_group: str, strictness_level: str):
        """Configure analysis settings"""
        self.analysis_engine.configure_settings(age_group, strictness_level)

# Example usage and testing
if __name__ == "__main__":
    async def test_analysis_agent():
        """Test the Analysis Agent functionality"""
        print("Testing Analysis Agent...")
        
        # Create agent helper
        agent_helper = AnalysisAgentHelper()
        
        # Test ADK agent creation
        print("\n1. Testing ADK agent creation...")
        adk_agent = create_analysis_agent()
        print(f"   Agent name: {adk_agent.name}")
        print(f"   Tool count: {len(adk_agent.tools)}")
        
        # Test configuration
        print("\n2. Testing configuration...")
        agent_helper.configure("elementary", "strict")
        
        # Test statistics
        print("\n3. Testing statistics...")
        stats = agent_helper.get_statistics()
        print(f"   Total analyses: {stats['total_analyses']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
        
        print("\nAnalysis Agent test completed!")
    
    # Run test
    asyncio.run(test_analysis_agent()) 