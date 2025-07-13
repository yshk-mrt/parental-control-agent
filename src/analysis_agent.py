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
    #logger.info("Weave initialized successfully")
except Exception as e:
    logger.warning(f"Weave initialization failed: {e}. Continuing without Weave tracking.")

# Timing utilities for performance analysis
def get_precise_timestamp():
    """Get high-precision timestamp for performance analysis"""
    return time.time()

def log_timing(phase: str, timestamp: float, input_text: str = "", extra_info: str = ""):
    """Log timing information for performance analysis"""
    logger.info(f"⏱️ TIMING [{phase}] {timestamp:.6f}s - {input_text[:20]}{'...' if len(input_text) > 20 else ''} {extra_info}")

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
        else:
            object.__setattr__(self, 'cache', None)
        
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
    async def predict(self, input_text: str, screenshot_path: Optional[str] = None) -> Optional[AnalysisResult]:
        """Main prediction method for Weave Model compatibility"""
        return await self.analyze_input_context(input_text, screenshot_path, force_analysis=True)
    
    def _is_potentially_inappropriate(self, input_text: str) -> bool:
        """Check if input contains potentially inappropriate content that should be analyzed immediately"""
        # Common inappropriate words/phrases that should be analyzed even if short
        inappropriate_keywords = [
            'fuck', 'shit', 'damn', 'hell', 'bitch', 'ass', 'crap',
            'piss', 'bastard', 'whore', 'slut', 'nigger', 'faggot',
            'retard', 'gay', 'lesbian', 'porn', 'sex', 'dick', 'cock',
            'pussy', 'boob', 'tit', 'nude', 'naked', 'kill', 'die',
            'suicide', 'murder', 'rape', 'drug', 'weed', 'cocaine',
            'heroin', 'meth', 'alcohol', 'beer', 'wine', 'drunk',
            'hate', 'violence', 'bomb', 'gun', 'weapon', 'blood'
        ]
        
        # Check if input contains any inappropriate keywords
        input_lower = input_text.lower().strip()
        
        # Check for exact matches or words within the text
        for keyword in inappropriate_keywords:
            if keyword in input_lower:
                return True
        
        # Check for suspicious patterns (multiple special characters, excessive caps, etc.)
        if len(input_lower) >= 3:
            # Check for excessive special characters
            special_chars = sum(1 for c in input_text if not c.isalnum() and not c.isspace())
            if special_chars > len(input_text) * 0.3:  # More than 30% special characters
                return True
            
            # Check for excessive caps
            if input_text.isupper() and len(input_text) > 3:
                return True
        
        return False
    
    async def _check_input_completeness(self, input_text: str) -> Dict[str, Any]:
        """Use LLM to check if input appears to be complete or incomplete"""
        # Handle empty or whitespace-only inputs
        if not input_text or not input_text.strip():
            return {"is_complete": False, "confidence": 0.9, "reason": "Empty or whitespace-only input"}
            
        # Handle very short inputs
        if len(input_text.strip()) < 2:
            return {"is_complete": False, "confidence": 0.8, "reason": "Too short"}
        
        # Use Gemini to assess input completeness
        try:
            
            # Create a specialized prompt for completeness checking
            from gemini_multimodal import GeminiMultimodalAnalyzer
            analyzer = GeminiMultimodalAnalyzer()
            
            # Check completeness using LLM
            prompt = f"""Analyze the following text input and determine if it appears to be complete or incomplete:

Input: "{input_text}"

Consider:
- Does it seem like the user finished typing their thought?
- Does it end mid-word or mid-sentence?
- Is it a complete phrase, question, or statement?
- Does it have enough context to be meaningful?

Examples:
- "Hi" - complete greeting
- "Hi from" - incomplete, seems cut off
- "Hi from afr" - incomplete, cut off mid-word
- "Hi from africa" - complete phrase
- "Hello world" - complete phrase
- "What is" - incomplete question
- "What is 2+2?" - complete question

Respond with JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}"""
            
            response = await analyzer.analyze_with_prompt(prompt)
            
            # Parse the response
            import json
            try:
                # Clean the response
                response_clean = response.strip()
                
                # Remove markdown code blocks if present
                if response_clean.startswith('```json'):
                    response_clean = response_clean[7:]
                elif response_clean.startswith('```'):
                    response_clean = response_clean[3:]
                
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
                
                response_clean = response_clean.strip()
                
                result = json.loads(response_clean)
                return {
                    "is_complete": result.get("is_complete", True),
                    "confidence": result.get("confidence", 0.5),
                    "reason": result.get("reason", "LLM analysis")
                }
            except Exception as e:
                logger.warning(f"JSON parsing failed: {e}, response: {response[:200]}...")
                # Fallback to simple heuristics if JSON parsing fails
                return {"is_complete": True, "confidence": 0.5, "reason": "Fallback analysis"}
                
        except Exception as e:
            logger.warning(f"LLM completeness check failed: {e}")
            # Fallback to simple heuristics
            return {"is_complete": True, "confidence": 0.5, "reason": "Error fallback"}
    
    @weave.op()
    async def analyze_input_context(self, 
                                  input_text: str, 
                                  screenshot_path: Optional[str] = None,
                                  force_analysis: bool = False) -> Optional[AnalysisResult]:
        """
        Analyze input text and screen context for comprehensive assessment
        
        Args:
            input_text: The keyboard input text to analyze
            screenshot_path: Optional path to screenshot image
            force_analysis: Force analysis even for incomplete inputs (e.g., when Enter is pressed)
            
        Returns:
            AnalysisResult with comprehensive analysis, or None if input is incomplete
        """
        start_time = time.time()
        
        # Analysis timing - entry point
        timestamp_analysis_start = get_precise_timestamp()
        log_timing("ANALYSIS_START", timestamp_analysis_start, input_text)
        
        # Check for incomplete input using LLM (unless forced)
        if not force_analysis:
            # Skip completeness check for potentially inappropriate content
            # Even short words like "fuck" should be analyzed immediately
            if self._is_potentially_inappropriate(input_text):
                logger.info(f"Potentially inappropriate content detected, forcing analysis: '{input_text[:20]}...'")
                force_analysis = True
            else:
                completeness_check = await self._check_input_completeness(input_text)
                if not completeness_check["is_complete"]:
                    logger.info(f"LLM detected incomplete input: '{input_text}' - {completeness_check['reason']} - Deferring analysis")
                    
                    # Return None to indicate that processing should be deferred
                    return None
        
        # Check cache first
        if self.cache_enabled and self.cache:
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
            timestamp_gemini_start = get_precise_timestamp()
            log_timing("GEMINI_ANALYSIS_START", timestamp_gemini_start, input_text)
            
            if screenshot_path and os.path.exists(screenshot_path):
                analysis_data = await self._analyze_multimodal_content(input_text, screenshot_path)
            else:
                analysis_data = await self._analyze_text_content(input_text)
            
            timestamp_gemini_end = get_precise_timestamp()
            log_timing("GEMINI_ANALYSIS_END", timestamp_gemini_end, input_text, f"gemini_time={(timestamp_gemini_end-timestamp_gemini_start):.2f}s")
            
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
            if self.cache_enabled and self.cache:
                self.cache.set(input_text, screenshot_path, result)
            
            # Update statistics
            self.stats['total_analyses'] += 1
            category = result.category
            self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
            
            analysis_time = time.time() - start_time
            
            # Analysis timing - completion
            timestamp_analysis_end = get_precise_timestamp()
            log_timing("ANALYSIS_END", timestamp_analysis_end, input_text, f"total_analysis_time={(timestamp_analysis_end-timestamp_analysis_start):.2f}s")
            
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
                def __init__(self, input_text, screenshot_path, age_group, strictness_level):
                    self.state = {
                        'current_input_text': input_text,
                        'current_screenshot_base64': '',  # Would need to load actual image
                        'screenshot_mime_type': 'image/jpeg',
                        'target_age_group': age_group,
                        'strict_mode': strictness_level == 'strict'
                    }
                    
                def get_session(self):
                    return None
            
            context = MockToolContext(input_text, screenshot_path, self.age_group, self.strictness_level)
            result = analyze_multimodal_content_tool(context)
            
            # Extract analysis data from the result
            if result.get('status') == 'success':
                analysis = result.get('analysis', {})
                return {
                    'category': analysis.get('category', 'unknown'),
                    'confidence': analysis.get('confidence', 0.0),
                    'age_appropriateness': analysis.get('age_appropriate', {}),
                    'safety_concerns': analysis.get('concerns', []),
                    'educational_value': analysis.get('educational_value', 'Unknown'),
                    'parental_action': result.get('parental_action', 'monitor'),
                    'context_summary': analysis.get('context_summary', 'Analysis completed'),
                    'detailed_analysis': analysis
                }
            else:
                logger.error(f"Multimodal analysis failed: {result.get('message', 'Unknown error')}")
                return await self._analyze_text_content(input_text)
        except Exception as e:
            logger.error(f"Multimodal analysis error: {e}")
            return await self._analyze_text_content(input_text)
    
    @weave.op()
    async def _analyze_text_content(self, input_text: str) -> Dict[str, Any]:
        """Analyze content using text-only AI"""
        try:
            class MockToolContext:
                def __init__(self, input_text, age_group, strictness_level):
                    self.state = {
                        'current_input_text': input_text,
                        'target_age_group': age_group,
                        'strict_mode': strictness_level == 'strict'
                    }
                    
                def get_session(self):
                    return None
            
            context = MockToolContext(input_text, self.age_group, self.strictness_level)
            result = analyze_text_content_tool(context)
            
            # Extract analysis data from the result
            if result.get('status') == 'success':
                analysis = result.get('analysis', {})
                return {
                    'category': analysis.get('category', 'unknown'),
                    'confidence': analysis.get('confidence', 0.0),
                    'age_appropriateness': analysis.get('age_appropriate', {}),
                    'safety_concerns': analysis.get('concerns', []),
                    'educational_value': analysis.get('educational_value', 'Unknown'),
                    'parental_action': result.get('parental_action', 'monitor'),
                    'context_summary': analysis.get('context_summary', 'Analysis completed'),
                    'detailed_analysis': analysis
                }
            else:
                logger.error(f"Text analysis failed: {result.get('message', 'Unknown error')}")
                return {
                    'category': 'unknown',
                    'confidence': 0.0,
                    'age_appropriateness': {},
                    'safety_concerns': ['Analysis failed'],
                    'educational_value': 'Unknown',
                    'parental_action': 'monitor',
                    'context_summary': f'Analysis failed: {result.get("message", "Unknown error")}',
                    'detailed_analysis': {'error': result.get('message', 'Unknown error')}
                }
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
        if self.cache_enabled and self.cache:
            self.cache.cleanup_old_cache()
            logger.info("Cache cleanup completed")
        else:
            logger.info("Cache is disabled, no cleanup needed")

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
    result = await agent.analyze_input_context(input_text, screenshot_path, force_analysis=True)
    
    if result is None:
        return {
            'status': 'incomplete',
            'message': 'Input appears incomplete, analysis deferred'
        }
    
    return {
        'status': 'success',
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
        model="gemini-1.5-flash",
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
    async def process_input_event(self, input_text: str, screenshot_path: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Process an input event and return analysis results
        
        Args:
            input_text: The keyboard input text
            screenshot_path: Optional screenshot path
            
        Returns:
            AnalysisResult with comprehensive analysis, or None if incomplete
        """
        return await self.analysis_engine.analyze_input_context(input_text, screenshot_path, force_analysis=False)
    
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