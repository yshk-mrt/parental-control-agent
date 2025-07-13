import asyncio
import base64
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

import google.generativeai as genai
from google.adk.tools import FunctionTool, ToolContext
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContentCategory(Enum):
    """Content categories for parental control assessment"""
    SAFE = "safe"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    SOCIAL = "social"
    CONCERNING = "concerning"
    INAPPROPRIATE = "inappropriate"
    DANGEROUS = "dangerous"

class AgeGroup(Enum):
    """Age groups for content assessment"""
    ELEMENTARY = "elementary"  # 6-12 years
    MIDDLE_SCHOOL = "middle_school"  # 13-15 years
    HIGH_SCHOOL = "high_school"  # 16-18 years

@dataclass
class ContentAnalysisResult:
    """Result of content analysis"""
    category: ContentCategory
    confidence: float
    age_appropriate: Dict[AgeGroup, bool]
    concerns: List[str]
    educational_value: Optional[str]
    recommendations: List[str]
    context_summary: str
    detected_elements: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MultimodalAnalysisConfig:
    """Configuration for multimodal analysis"""
    # Age assessment settings
    target_age_group: AgeGroup = AgeGroup.ELEMENTARY
    strict_mode: bool = True
    
    # Content filtering settings
    check_violence: bool = True
    check_adult_content: bool = True
    check_inappropriate_language: bool = True
    check_dangerous_activities: bool = True
    
    # Educational assessment
    assess_educational_value: bool = True
    
    # Performance settings
    max_response_tokens: int = 1000
    temperature: float = 0.1  # Low temperature for consistent results

class GeminiMultimodalAnalyzer:
    """Gemini multimodal content analyzer for parental control"""
    
    def __init__(self, config: Optional[MultimodalAnalysisConfig] = None):
        self.config = config or MultimodalAnalysisConfig()
        
        # Initialize Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Analysis history for context
        self.analysis_history = []
        
    def _create_analysis_prompt(self, text_input: str, has_image: bool = False) -> str:
        """Create a comprehensive analysis prompt for parental control"""
        
        age_group_desc = {
            AgeGroup.ELEMENTARY: "elementary school children (ages 6-12)",
            AgeGroup.MIDDLE_SCHOOL: "middle school students (ages 13-15)",
            AgeGroup.HIGH_SCHOOL: "high school students (ages 16-18)"
        }
        
        target_age = age_group_desc[self.config.target_age_group]
        
        prompt = f"""
You are an expert AI assistant specializing in parental control and child safety assessment. 
Analyze the provided content (text{' and image' if has_image else ''}) for appropriateness for {target_age}.

ANALYSIS REQUIREMENTS:
1. Content Category Assessment:
   - Classify content into: safe, educational, entertainment, social, concerning, inappropriate, dangerous
   - Provide confidence score (0.0-1.0)

2. Age Appropriateness:
   - Evaluate for elementary (6-12), middle_school (13-15), high_school (16-18)
   - Consider developmental appropriateness

3. Safety Concerns:
   {'- Check for violence, adult content, inappropriate language, dangerous activities' if self.config.strict_mode else '- Basic safety assessment'}

4. Educational Value:
   {'- Assess learning potential and educational benefits' if self.config.assess_educational_value else '- Brief educational assessment'}

5. Context Analysis:
   - Summarize what the child is doing/viewing
   - Identify key elements in the content
   - Understand the overall context

TEXT INPUT: "{text_input}"

RESPOND IN VALID JSON FORMAT ONLY:
{{
  "category": "safe|educational|entertainment|social|concerning|inappropriate|dangerous",
  "confidence": 0.95,
  "age_appropriate": {{
    "elementary": true,
    "middle_school": true,
    "high_school": true
  }},
  "concerns": ["list of specific concerns if any"],
  "educational_value": "description of educational aspects or null",
  "recommendations": ["list of recommendations for parents"],
  "context_summary": "brief summary of what the child is doing/viewing",
  "detected_elements": ["list of key elements detected in content"],
  "safety_assessment": {{
    "violence": false,
    "adult_content": false,
    "inappropriate_language": false,
    "dangerous_activities": false
  }},
  "parental_action": "allow|monitor|restrict|block",
  "explanation": "brief explanation of the assessment"
}}

IMPORTANT: Return ONLY the JSON object, no additional text.
"""
        return prompt.strip()
    
    def _parse_analysis_response(self, response_text: str) -> ContentAnalysisResult:
        """Parse the Gemini response into a structured result"""
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Map to our data structure
            category = ContentCategory(data.get('category', 'safe'))
            confidence = float(data.get('confidence', 0.0))
            
            # Parse age appropriateness
            age_appropriate = {}
            age_data = data.get('age_appropriate', {})
            for age_group in AgeGroup:
                age_appropriate[age_group] = age_data.get(age_group.value, True)
            
            # Extract other fields
            concerns = data.get('concerns', [])
            educational_value = data.get('educational_value')
            recommendations = data.get('recommendations', [])
            context_summary = data.get('context_summary', '')
            detected_elements = data.get('detected_elements', [])
            
            return ContentAnalysisResult(
                category=category,
                confidence=confidence,
                age_appropriate=age_appropriate,
                concerns=concerns,
                educational_value=educational_value,
                recommendations=recommendations,
                context_summary=context_summary,
                detected_elements=detected_elements
            )
            
        except json.JSONDecodeError as e:
            # Fallback parsing for malformed JSON
            return ContentAnalysisResult(
                category=ContentCategory.CONCERNING,
                confidence=0.5,
                age_appropriate={age: False for age in AgeGroup},
                concerns=["Failed to parse AI response", str(e)],
                educational_value=None,
                recommendations=["Manual review required"],
                context_summary="Analysis failed - manual review needed",
                detected_elements=["parsing_error"]
            )
        except Exception as e:
            # General error handling
            return ContentAnalysisResult(
                category=ContentCategory.CONCERNING,
                confidence=0.0,
                age_appropriate={age: False for age in AgeGroup},
                concerns=["Analysis error", str(e)],
                educational_value=None,
                recommendations=["Technical issue - retry analysis"],
                context_summary="Technical error occurred",
                detected_elements=["error"]
            )
    
    async def analyze_with_prompt(self, custom_prompt: str) -> str:
        """Analyze content with a custom prompt and return raw response"""
        try:
            response = await self.model.generate_content_async(custom_prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini analysis failed: {str(e)}")
    
    def analyze_text_only(self, text: str) -> ContentAnalysisResult:
        """Analyze text-only content"""
        try:
            prompt = self._create_analysis_prompt(text, has_image=False)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_response_tokens,
                    temperature=self.config.temperature,
                )
            )
            
            result = self._parse_analysis_response(response.text)
            self.analysis_history.append(result)
            
            return result
            
        except Exception as e:
            return ContentAnalysisResult(
                category=ContentCategory.CONCERNING,
                confidence=0.0,
                age_appropriate={age: False for age in AgeGroup},
                concerns=["Analysis failed", str(e)],
                educational_value=None,
                recommendations=["Technical issue - manual review required"],
                context_summary="Failed to analyze content",
                detected_elements=["error"]
            )
    
    def analyze_multimodal(self, text: str, image_data: str, image_mime_type: str = "image/jpeg") -> ContentAnalysisResult:
        """Analyze text and image content together"""
        try:
            prompt = self._create_analysis_prompt(text, has_image=True)
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Create image part
            image_part = {
                "mime_type": image_mime_type,
                "data": image_bytes
            }
            
            # Generate content with multimodal input
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_response_tokens,
                    temperature=self.config.temperature,
                )
            )
            
            result = self._parse_analysis_response(response.text)
            self.analysis_history.append(result)
            
            return result
            
        except Exception as e:
            return ContentAnalysisResult(
                category=ContentCategory.CONCERNING,
                confidence=0.0,
                age_appropriate={age: False for age in AgeGroup},
                concerns=["Multimodal analysis failed", str(e)],
                educational_value=None,
                recommendations=["Technical issue - manual review required"],
                context_summary="Failed to analyze multimodal content",
                detected_elements=["error"]
            )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of recent analysis history"""
        if not self.analysis_history:
            return {"status": "no_history", "message": "No analysis history available"}
        
        recent_analyses = self.analysis_history[-10:]  # Last 10 analyses
        
        # Count categories
        category_counts = {}
        for analysis in recent_analyses:
            category = analysis.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(a.confidence for a in recent_analyses) / len(recent_analyses)
        
        # Count concerns
        all_concerns = []
        for analysis in recent_analyses:
            all_concerns.extend(analysis.concerns)
        
        return {
            "status": "success",
            "total_analyses": len(recent_analyses),
            "category_distribution": category_counts,
            "average_confidence": round(avg_confidence, 2),
            "recent_concerns": list(set(all_concerns)),
            "latest_analysis": {
                "category": recent_analyses[-1].category.value,
                "confidence": recent_analyses[-1].confidence,
                "timestamp": recent_analyses[-1].timestamp
            }
        }

# Global analyzer instance
_analyzer_instance = None

def get_analyzer_instance(config: Optional[MultimodalAnalysisConfig] = None) -> GeminiMultimodalAnalyzer:
    """Get or create the global analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = GeminiMultimodalAnalyzer(config)
    return _analyzer_instance

# ADK Function Tools

def analyze_text_content_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Analyze text content using Gemini for parental control assessment.
    
    Use this tool to analyze keyboard input text for age-appropriateness and safety.
    
    Returns:
        dict: Analysis result with safety assessment and recommendations.
        Success: {'status': 'success', 'analysis': {...}, 'parental_action': 'allow|monitor|restrict|block'}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        # Get text from tool context state (from keylogger)
        text_input = tool_context.state.get('current_input_text', '')
        
        if not text_input or not text_input.strip():
            return {
                "status": "no_input",
                "message": "No text input available for analysis",
                "analysis": None
            }
        
        # Get analyzer with appropriate config
        config = MultimodalAnalysisConfig(
            target_age_group=AgeGroup.ELEMENTARY,  # Default to elementary
            strict_mode=True
        )
        analyzer = get_analyzer_instance(config)
        
        # Analyze text
        result = analyzer.analyze_text_only(text_input)
        
        # Helper function to determine parental action
        def determine_parental_action(category):
            if category in [ContentCategory.SAFE, ContentCategory.EDUCATIONAL]:
                return "allow"
            elif category in [ContentCategory.ENTERTAINMENT, ContentCategory.SOCIAL]:
                return "monitor"
            elif category == ContentCategory.CONCERNING:
                return "restrict"
            else:  # INAPPROPRIATE, DANGEROUS
                return "block"
        
        # Update tool context state
        tool_context.state["last_text_analysis"] = {
            "timestamp": result.timestamp,
            "category": result.category.value,
            "confidence": result.confidence,
            "concerns": result.concerns
        }
        
        return {
            "status": "success",
            "analysis": {
                "category": result.category.value,
                "confidence": result.confidence,
                "age_appropriate": {age.value: appropriate for age, appropriate in result.age_appropriate.items()},
                "concerns": result.concerns,
                "educational_value": result.educational_value,
                "recommendations": result.recommendations,
                "context_summary": result.context_summary,
                "detected_elements": result.detected_elements
            },
            "parental_action": determine_parental_action(result.category),
            "input_analyzed": text_input[:100] + "..." if len(text_input) > 100 else text_input
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Text analysis failed: {str(e)}",
            "analysis": None
        }

def analyze_multimodal_content_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Analyze text and image content together using Gemini multimodal capabilities.
    
    Use this tool to analyze keyboard input combined with screen capture for comprehensive assessment.
    
    Returns:
        dict: Multimodal analysis result with comprehensive safety assessment.
        Success: {'status': 'success', 'analysis': {...}, 'parental_action': 'allow|monitor|restrict|block'}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        # Get text and image data from tool context state
        text_input = tool_context.state.get('current_input_text', '')
        image_data = tool_context.state.get('current_screenshot_base64', '')
        image_mime_type = tool_context.state.get('screenshot_mime_type', 'image/jpeg')
        
        if not text_input or not text_input.strip():
            return {
                "status": "no_text_input",
                "message": "No text input available for multimodal analysis",
                "analysis": None
            }
        
        if not image_data:
            return {
                "status": "no_image_input",
                "message": "No image data available for multimodal analysis",
                "analysis": None
            }
        
        # Get analyzer with appropriate config
        config = MultimodalAnalysisConfig(
            target_age_group=AgeGroup.ELEMENTARY,  # Default to elementary
            strict_mode=True,
            assess_educational_value=True
        )
        analyzer = get_analyzer_instance(config)
        
        # Analyze multimodal content
        result = analyzer.analyze_multimodal(text_input, image_data, image_mime_type)
        
        # Update tool context state
        tool_context.state["last_multimodal_analysis"] = {
            "timestamp": result.timestamp,
            "category": result.category.value,
            "confidence": result.confidence,
            "concerns": result.concerns,
            "context_summary": result.context_summary
        }
        
        # Determine parental action based on analysis
        if result.category in [ContentCategory.SAFE, ContentCategory.EDUCATIONAL]:
            parental_action = "allow"
        elif result.category in [ContentCategory.ENTERTAINMENT, ContentCategory.SOCIAL]:
            parental_action = "monitor"
        elif result.category == ContentCategory.CONCERNING:
            parental_action = "restrict"
        else:  # INAPPROPRIATE, DANGEROUS
            parental_action = "block"
        
        return {
            "status": "success",
            "analysis": {
                "category": result.category.value,
                "confidence": result.confidence,
                "age_appropriate": {age.value: appropriate for age, appropriate in result.age_appropriate.items()},
                "concerns": result.concerns,
                "educational_value": result.educational_value,
                "recommendations": result.recommendations,
                "context_summary": result.context_summary,
                "detected_elements": result.detected_elements
            },
            "parental_action": parental_action,
            "input_analyzed": text_input[:100] + "..." if len(text_input) > 100 else text_input,
            "multimodal": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Multimodal analysis failed: {str(e)}",
            "analysis": None
        }

def get_analysis_summary_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get summary of recent content analysis history.
    
    Use this tool to understand patterns in the child's computer usage and content consumption.
    
    Returns:
        dict: Analysis summary with usage patterns and trends.
        Success: {'status': 'success', 'summary': {...}}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        analyzer = get_analyzer_instance()
        summary = analyzer.get_analysis_summary()
        
        # Update tool context state
        tool_context.state["analysis_summary_generated"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "summary": summary,
            "recommendations": [
                "Monitor content categories with higher concern levels",
                "Encourage educational content consumption",
                "Review and discuss concerning content with child",
                "Adjust parental controls based on usage patterns"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate analysis summary: {str(e)}",
            "summary": None
        }

def configure_analysis_settings_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Configure analysis settings for parental control assessment.
    
    Use this tool to adjust age group, strictness, and other analysis parameters.
    
    Returns:
        dict: Configuration update result.
        Success: {'status': 'success', 'config': {...}}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        # Get configuration from tool context state
        age_group_str = tool_context.state.get('target_age_group', 'elementary')
        strict_mode = tool_context.state.get('strict_mode', True)
        
        # Map age group string to enum
        age_group_map = {
            'elementary': AgeGroup.ELEMENTARY,
            'middle_school': AgeGroup.MIDDLE_SCHOOL,
            'high_school': AgeGroup.HIGH_SCHOOL
        }
        
        age_group = age_group_map.get(age_group_str, AgeGroup.ELEMENTARY)
        
        # Create new configuration
        config = MultimodalAnalysisConfig(
            target_age_group=age_group,
            strict_mode=strict_mode,
            assess_educational_value=True
        )
        
        # Update global analyzer instance
        global _analyzer_instance
        _analyzer_instance = GeminiMultimodalAnalyzer(config)
        
        # Update tool context state
        tool_context.state["analysis_config_updated"] = datetime.now().isoformat()
        tool_context.state["current_age_group"] = age_group.value
        tool_context.state["current_strict_mode"] = strict_mode
        
        return {
            "status": "success",
            "config": {
                "age_group": age_group.value,
                "strict_mode": strict_mode,
                "assess_educational_value": config.assess_educational_value
            },
            "message": "Analysis settings updated successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to configure analysis settings: {str(e)}",
            "config": None
        }

# Create ADK Function Tools
analyze_text_content_function_tool = FunctionTool(func=analyze_text_content_tool)
analyze_multimodal_content_function_tool = FunctionTool(func=analyze_multimodal_content_tool)
get_analysis_summary_function_tool = FunctionTool(func=get_analysis_summary_tool)
configure_analysis_settings_function_tool = FunctionTool(func=configure_analysis_settings_tool)

# Example analysis agent
def create_gemini_analysis_agent() -> Agent:
    """Create a Gemini multimodal analysis agent"""
    
    return Agent(
        name="GeminiAnalysisAgent",
        model="gemini-1.5-flash",
        description="A multimodal AI agent that analyzes text and images for parental control and child safety assessment",
        instruction="""
        You are a specialized AI agent for parental control and child safety assessment using Google's Gemini multimodal capabilities.
        
        Your capabilities include:
        1. analyze_text_content: Analyze keyboard input text for age-appropriateness and safety
        2. analyze_multimodal_content: Analyze text and screen captures together for comprehensive assessment
        3. get_analysis_summary: Generate usage patterns and trends from analysis history
        4. configure_analysis_settings: Adjust age group and strictness settings
        
        Your analysis focuses on:
        - Age-appropriate content assessment
        - Safety concerns (violence, adult content, inappropriate language, dangerous activities)
        - Educational value assessment
        - Context understanding (what the child is doing/viewing)
        - Parental action recommendations (allow, monitor, restrict, block)
        
        Always provide clear, actionable recommendations for parents while maintaining child privacy and safety.
        Use multimodal analysis when both text and image data are available for the most comprehensive assessment.
        """,
        tools=[
            analyze_text_content_function_tool,
            analyze_multimodal_content_function_tool,
            get_analysis_summary_function_tool,
            configure_analysis_settings_function_tool
        ]
    )

# Direct execution mode (for testing)
if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    # Test Gemini multimodal analysis
    console.print("[bold green]Gemini Multimodal Analysis Test[/]")
    
    try:
        # Test configuration
        config = MultimodalAnalysisConfig(
            target_age_group=AgeGroup.ELEMENTARY,
            strict_mode=True
        )
        analyzer = GeminiMultimodalAnalyzer(config)
        
        # Test text analysis
        console.print("\n[bold blue]Testing Text Analysis...[/]")
        test_text = "I'm doing my math homework. 2 + 2 = 4"
        result = analyzer.analyze_text_only(test_text)
        
        console.print(f"Category: {result.category.value}")
        console.print(f"Confidence: {result.confidence}")
        console.print(f"Context: {result.context_summary}")
        console.print(f"Concerns: {result.concerns}")
        
        # Test analysis summary
        console.print("\n[bold blue]Testing Analysis Summary...[/]")
        summary = analyzer.get_analysis_summary()
        console.print(f"Summary: {summary}")
        
        console.print("\n[bold green]✅ Gemini Multimodal Analysis Test Complete![/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Test failed: {e}[/]")
        console.print("[yellow]Make sure GOOGLE_API_KEY is set in your .env file[/]") 