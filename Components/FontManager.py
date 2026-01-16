"""
Enhanced font styling and configuration module for subtitle rendering
"""
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import ImageFont
import logging

logger = logging.getLogger(__name__)

@dataclass
class FontStyle:
    """Font style configuration"""
    family: str
    size: int
    color: str
    stroke_color: str
    stroke_width: int
    background_color: Optional[str] = None
    background_opacity: float = 0.7
    position: str = "bottom"  # top, middle, bottom
    alignment: str = "center"  # left, center, right
    animation: Optional[str] = None  # fade-in, slide-up, typewriter
    
class FontManager:
    """Manages font configurations and styling options"""
    
    def __init__(self):
        self.font_paths = self._discover_fonts()
        self.predefined_styles = self._create_predefined_styles()
    
    def _discover_fonts(self) -> Dict[str, str]:
        """Discover available fonts on the system"""
        font_paths = {}
        
        # Common font directories across platforms
        font_dirs = [
            "/System/Library/Fonts",  # macOS
            "/usr/share/fonts",       # Linux
            "/Windows/Fonts",         # Windows
            "~/.fonts",              # User fonts
            "./fonts"                # Local fonts directory
        ]
        
        # Common font files to look for
        font_files = [
            "Arial.ttf", "arial.ttf",
            "Franklin Gothic Medium.ttf", "FranklinGothicMedium.ttf",
            "Helvetica.ttc", "helvetica.ttc",
            "Roboto-Bold.ttf", "roboto-bold.ttf",
            "OpenSans-Bold.ttf", "opensans-bold.ttf",
            "DejaVuSans-Bold.ttf", "dejavusans-bold.ttf",
            "Impact.ttf", "impact.ttf",
            "Montserrat-Bold.ttf", "montserrat-bold.ttf"
        ]
        
        for font_dir in font_dirs:
            expanded_dir = os.path.expanduser(font_dir)
            if os.path.exists(expanded_dir):
                for font_file in font_files:
                    font_path = os.path.join(expanded_dir, font_file)
                    if os.path.exists(font_path):
                        font_name = os.path.splitext(font_file)[0].lower()
                        font_paths[font_name] = font_path
        
        # Add fallback fonts
        if not font_paths:
            font_paths = {
                "default": None,  # Will use system default
                "dejavu-sans-bold": None,
                "arial": None
            }
        
        return font_paths
    
    def _create_predefined_styles(self) -> Dict[str, FontStyle]:
        """Create predefined font style configurations"""
        styles = {
            "youtube_shorts": FontStyle(
                family="franklin-gothic-medium",
                size=48,
                color="white",
                stroke_color="black",
                stroke_width=3,
                background_color=None,
                position="bottom",
                alignment="center",
                animation="fade-in"
            ),
            "tiktok_style": FontStyle(
                family="impact",
                size=52,
                color="white",
                stroke_color="black",
                stroke_width=4,
                background_color="rgba(0,0,0,0.6)",
                position="bottom",
                alignment="center",
                animation="slide-up"
            ),
            "instagram_reels": FontStyle(
                family="roboto-bold",
                size=44,
                color="white",
                stroke_color="black",
                stroke_width=2,
                background_color=None,
                position="bottom",
                alignment="center",
                animation="typewriter"
            ),
            "minimal_clean": FontStyle(
                family="helvetica",
                size=40,
                color="white",
                stroke_color=None,
                stroke_width=0,
                background_color="rgba(0,0,0,0.8)",
                position="bottom",
                alignment="center",
                animation=None
            ),
            "bold_impact": FontStyle(
                family="impact",
                size=56,
                color="yellow",
                stroke_color="black",
                stroke_width=5,
                background_color=None,
                position="middle",
                alignment="center",
                animation="fade-in"
            ),
            "elegant_serif": FontStyle(
                family="georgia",
                size=42,
                color="white",
                stroke_color="navy",
                stroke_width=2,
                background_color="rgba(0,0,0,0.7)",
                position="bottom",
                alignment="center",
                animation=None
            )
        }
        
        return styles
    
    def get_font_path(self, font_family: str) -> Optional[str]:
        """Get the file path for a font family"""
        font_key = font_family.lower().replace(" ", "-")
        return self.font_paths.get(font_key)
    
    def get_available_fonts(self) -> List[str]:
        """Get list of available font families"""
        return list(self.font_paths.keys())
    
    def get_predefined_styles(self) -> List[str]:
        """Get list of predefined style names"""
        return list(self.predefined_styles.keys())
    
    def get_style(self, style_name: str) -> Optional[FontStyle]:
        """Get a predefined style by name"""
        return self.predefined_styles.get(style_name)
    
    def create_custom_style(self, 
                          name: str,
                          family: str = "arial",
                          size: int = 48,
                          color: str = "white",
                          stroke_color: str = "black",
                          stroke_width: int = 3,
                          **kwargs) -> FontStyle:
        """Create a custom font style"""
        style = FontStyle(
            family=family,
            size=size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            **kwargs
        )
        
        # Store the custom style
        self.predefined_styles[name] = style
        return style
    
    def validate_font(self, font_family: str) -> bool:
        """Check if a font is available"""
        font_path = self.get_font_path(font_family)
        if font_path and os.path.exists(font_path):
            try:
                # Try to load the font
                ImageFont.truetype(font_path, 12)
                return True
            except Exception as e:
                logger.warning(f"Font validation failed for {font_family}: {str(e)}")
                return False
        return False
    
    def get_font_recommendations(self, use_case: str = "youtube_shorts") -> List[str]:
        """Get font recommendations for specific use cases"""
        recommendations = {
            "youtube_shorts": ["franklin-gothic-medium", "impact", "roboto-bold", "arial"],
            "tiktok": ["impact", "montserrat-bold", "roboto-bold", "helvetica"],
            "instagram": ["roboto-bold", "montserrat-bold", "opensans-bold", "helvetica"],
            "professional": ["helvetica", "arial", "roboto-bold", "opensans-bold"],
            "creative": ["impact", "montserrat-bold", "franklin-gothic-medium"],
            "readable": ["arial", "helvetica", "roboto-bold", "opensans-bold"]
        }
        
        return recommendations.get(use_case, recommendations["youtube_shorts"])

# Color schemes for different moods/themes
COLOR_SCHEMES = {
    "classic": {
        "text": "white",
        "stroke": "black",
        "background": "rgba(0,0,0,0.7)"
    },
    "vibrant": {
        "text": "yellow",
        "stroke": "red",
        "background": "rgba(0,0,0,0.8)"
    },
    "neon": {
        "text": "#00ff00",
        "stroke": "#ff00ff",
        "background": "rgba(0,0,0,0.9)"
    },
    "elegant": {
        "text": "white",
        "stroke": "navy",
        "background": "rgba(0,0,0,0.6)"
    },
    "warm": {
        "text": "#ffcc00",
        "stroke": "#cc3300",
        "background": "rgba(0,0,0,0.7)"
    },
    "cool": {
        "text": "#00ccff",
        "stroke": "#003366",
        "background": "rgba(0,0,0,0.7)"
    }
}

# Animation configurations
ANIMATION_CONFIGS = {
    "fade-in": {
        "duration": 0.5,
        "easing": "ease-in"
    },
    "slide-up": {
        "duration": 0.3,
        "distance": 50,
        "easing": "ease-out"
    },
    "typewriter": {
        "char_delay": 0.05,
        "cursor": True
    },
    "bounce": {
        "duration": 0.6,
        "height": 20,
        "easing": "bounce"
    },
    "zoom": {
        "duration": 0.4,
        "scale": 1.2,
        "easing": "ease-in-out"
    }
}

# Singleton instance
_font_manager = None

def get_font_manager() -> FontManager:
    """Get singleton instance of font manager"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager

def create_subtitle_config(style_name: str = "youtube_shorts", **overrides) -> dict:
    """
    Create a subtitle configuration dictionary for moviepy
    
    Args:
        style_name: Name of predefined style or custom parameters
        **overrides: Override specific style parameters
        
    Returns:
        Dictionary with moviepy-compatible subtitle configuration
    """
    font_manager = get_font_manager()
    style = font_manager.get_style(style_name)
    
    if not style:
        # Create default style if not found
        style = FontStyle(
            family="arial",
            size=48,
            color="white",
            stroke_color="black",
            stroke_width=3,
            position="bottom",
            alignment="center"
        )
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(style, key):
            setattr(style, key, value)
    
    # Get font path
    font_path = font_manager.get_font_path(style.family)
    
    # Build moviepy config
    config = {
        'fontsize': style.size,
        'color': style.color,
        'align': style.alignment,
        'method': 'caption'
    }
    
    # Add font path if available
    if font_path:
        config['font'] = font_path
    
    # Add stroke if specified
    if style.stroke_color and style.stroke_width > 0:
        config['stroke_color'] = style.stroke_color
        config['stroke_width'] = style.stroke_width
    
    return config