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
import weave
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

# Initialize Weave for tracking
try:
    weave.init("parental-control-agent")
    logger.info("Weave initialized successfully")
except Exception as e:
    logger.warning(f"Weave initialization failed: {e}. Continuing without Weave tracking.")

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
    """High-performance cache for analysis results"""
    
    def __init__(self, cache_dir: str = "temp/analysis_cache", max_age_minutes: int = 30):
        self.cache_dir = Path(cache_dir)
        self.max_age_minutes = max_age_minutes
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @weave.op()
    def _get_cache_key(self, input_text: str, screenshot_path: Optional[str]) -> str:
        """Generate MD5 cache key from input"""
        content = f"{input_text}:{screenshot_path or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @weave.op()
    def get(self, input_text: str, screenshot_path: Optional[str]) -> Optional[AnalysisResult]:
        """Get cached analysis result"""
        cache_key = self._get_cache_key(input_text, screenshot_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        # Check if cache is expired
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(minutes=self.max_age_minutes):
            cache_file.unlink(missing_ok=True)
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            cache_file.unlink(missing_ok=True)
            return None
    
    @weave.op()
    def set(self, input_text: str, screenshot_path: Optional[str], result: AnalysisResult):
        """Cache analysis result"""
        cache_key = self._get_cache_key(input_text, screenshot_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    @weave.op()
    def cleanup_old_cache(self):
        """Clean up old cache files"""
        cutoff_time = datetime.now() - timedelta(minutes=self.max_age_minutes)
        
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_time:
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

class AnalysisAgent(weave.Model):
    """
    Analysis Agent that coordinates content analysis using Gemini multimodal tool
    
    This agent:
    1. Receives input text and screenshot data
    2. Analyzes content using Gemini multimodal AI
    3. Detects applications and context
    4. Provides structured analysis results
    5. Caches results for performance
    """
    
    age_group: str = "elementary"
    strictness_level: str = "moderate"
    cache_enabled: bool = True
    cache: Optional[AnalysisCache] = None
    gemini_tool: Optional[GeminiMultimodalAnalyzer] = None
    stats: Optional[Dict[str, Any]] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize cache
        if self.cache_enabled:
            object.__setattr__(self, 'cache', AnalysisCache())
        
        # Initialize tools
        object.__setattr__(self, 'gemini_tool', GeminiMultimodalAnalyzer())
        
        # Analysis statistics
        object.__setattr__(self, 'stats', {
            'total_analyses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'categories': {}
        })
        
        logger.info(f"Analysis Agent initialized for {self.age_group} with {self.strictness_level} strictness")
    
    @weave.op()
    async def predict(self, input_text: str, screenshot_path: Optional[str] = None) -> AnalysisResult:
        """Main prediction method for Weave Model compatibility"""
        return await self.analyze_input_context(input_text, screenshot_path)
    
    @weave.op()
    async def analyze_input_context(self, 
                                  input_text: str, 
                                  screenshot_path: Optional[str] = None) -> AnalysisResult:
        """
        Analyze input text and screen context for comprehensive assessment
        
        Args:
            input_text: The keyboard input text to analyze
            screenshot_path: Optional path to screenshot image
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        start_time = time.time()
        
        # Check cache first
        if self.cache_enabled:
            cached_result = self.cache.get(input_text, screenshot_path)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.info("Analysis result retrieved from cache")
                return cached_result
            else:
                self.stats['cache_misses'] += 1
        
        try:
            # Configure analysis settings
            class MockToolContext:
                def __init__(self, age_group, strictness_level):
                    self.state = {
                        'target_age_group': age_group,
                        'strict_mode': strictness_level == 'strict'
                    }
            
            context = MockToolContext(self.age_group, self.strictness_level)
            configure_analysis_settings_tool(context)
            
            # Perform analysis based on available data
            if screenshot_path and os.path.exists(screenshot_path):
                analysis_data = await self._analyze_multimodal_content(input_text, screenshot_path)
            else:
                analysis_data = await self._analyze_text_content(input_text)
            
            # Detect application context
            app_context = await self._detect_application_context(screenshot_path)
            
            # Create structured result
            result = AnalysisResult(
                timestamp=datetime.now(),
                input_text=input_text,
                screenshot_path=screenshot_path,
                category=analysis_data.get('category', 'unknown'),
                confidence=analysis_data.get('confidence', 0.0),
                age_appropriateness=analysis_data.get('age_appropriateness', {}),
                safety_concerns=analysis_data.get('safety_concerns', []),
                educational_value=analysis_data.get('educational_value', 'Unknown'),
                parental_action=analysis_data.get('parental_action', 'monitor'),
                context_summary=analysis_data.get('context_summary', 'Analysis completed'),
                application_detected=app_context.name if app_context else 'unknown',
                detailed_analysis=analysis_data.get('detailed_analysis', {})
            )
            
            # Cache result
            if self.cache_enabled:
                self.cache.set(input_text, screenshot_path, result)
            
            # Update statistics
            self.stats['total_analyses'] += 1
            category = result.category
            self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
            
            analysis_time = time.time() - start_time
            logger.info(f"Analysis completed in {analysis_time:.2f}s - Category: {result.category}, Action: {result.parental_action}")
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Analysis error: {e}")
            
            # Return fallback result
            return AnalysisResult(
                timestamp=datetime.now(),
                input_text=input_text,
                screenshot_path=screenshot_path,
                category='unknown',
                confidence=0.0,
                age_appropriateness={},
                safety_concerns=['Analysis failed - manual review recommended'],
                educational_value='Unknown due to analysis error',
                parental_action='monitor',
                context_summary='Analysis failed - please review manually',
                application_detected='unknown',
                detailed_analysis={'error': str(e)}
            )
    
    @weave.op()
    async def _analyze_multimodal_content(self, input_text: str, screenshot_path: str) -> Dict[str, Any]:
        """Analyze content using multimodal AI (text + image)"""
        try:
            class MockToolContext:
                def __init__(self, input_text, screenshot_path):
                    self.state = {
                        'current_input_text': input_text,
                        'current_screenshot_base64': '',  # Would need to load actual image
                        'screenshot_mime_type': 'image/jpeg'
                    }
                    
                def get_session(self):
                    return None
            
            context = MockToolContext(input_text, screenshot_path)
            result = analyze_multimodal_content_tool(context)
            return result
        except Exception as e:
            logger.error(f"Multimodal analysis error: {e}")
            return await self._analyze_text_content(input_text)
    
    @weave.op()
    async def _analyze_text_content(self, input_text: str) -> Dict[str, Any]:
        """Analyze content using text-only AI"""
        try:
            class MockToolContext:
                def __init__(self, input_text):
                    self.state = {
                        'current_input_text': input_text
                    }
                    
                def get_session(self):
                    return None
            
            context = MockToolContext(input_text)
            result = analyze_text_content_tool(context)
            return result
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'age_appropriateness': {},
                'safety_concerns': ['Analysis failed'],
                'educational_value': 'Unknown',
                'parental_action': 'monitor',
                'context_summary': f'Analysis failed: {str(e)}',
                'detailed_analysis': {'error': str(e)}
            }
    
    @weave.op()
    async def _detect_application_context(self, screenshot_path: Optional[str]) -> Optional[ApplicationContext]:
        """Detect application context from screenshot"""
        if not screenshot_path or not os.path.exists(screenshot_path):
            return None
        
        try:
            # Placeholder for application detection logic
            # This would analyze the screenshot to identify the current application
            return ApplicationContext(
                name="unknown",
                type="application",
                url=None,
                confidence=0.5,
                context_clues=["screenshot_analysis"]
            )
        except Exception as e:
            logger.error(f"Application detection error: {e}")
            return None
    
    @weave.op()
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get comprehensive analysis statistics"""
        total = self.stats['total_analyses']
        cache_total = self.stats['cache_hits'] + self.stats['cache_misses']
        
        return {
            'total_analyses': total,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_hit_rate': self.stats['cache_hits'] / max(cache_total, 1),
            'errors': self.stats['errors'],
            'error_rate': self.stats['errors'] / max(total, 1),
            'categories': self.stats['categories'],
            'category_distribution': self.stats['categories']
        }
    
    @weave.op()
    def configure_settings(self, age_group: str, strictness_level: str):
        """Configure analysis settings"""
        self.age_group = age_group
        self.strictness_level = strictness_level
        logger.info(f"Analysis settings updated: {age_group}, {strictness_level}")
    
    @weave.op()
    def cleanup_cache(self):
        """Clean up old cache files"""
        if self.cache_enabled:
            self.cache.cleanup_old_cache()
            logger.info("Cache cleanup completed")

# ADK FunctionTool implementations

@weave.op()
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

@weave.op()
async def get_analysis_statistics_tool() -> Dict[str, Any]:
    """Get analysis statistics from the Analysis Agent"""
    agent = get_global_analysis_engine()
    return agent.get_analysis_statistics()

@weave.op()
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

@weave.op()
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
    
    @weave.op()
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
    
    @weave.op()
    def get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return self.analysis_engine.get_analysis_statistics()
    
    @weave.op()
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