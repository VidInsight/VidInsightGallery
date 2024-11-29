import os
import sys
import yaml
import random
import logging
import io
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.modules.image_generator import GenreArtGenerator
from src.modules.instagram_poster import InstagramPoster

# Load environment variables
load_dotenv()

class AIPostTester:
    def __init__(self):
        """Initialize the tester with configuration and required components."""
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize components
        self.image_generator = GenreArtGenerator(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize Instagram poster
        self.instagram = InstagramPoster()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def generate_caption(self, genre, style=None, theme=None):
        """
        Generate a dynamic caption based on configuration
        
        Args:
            genre (str): The primary genre of the image
            style (str, optional): The artistic style used
            theme (str, optional): The thematic element used
        
        Returns:
            str: Generated caption with hashtags
        """
        captions_config = self.config.get('captions', {})
        
        # Base captions with genre
        base_captions = [
            f"🎨 {genre.capitalize()} AI-generated art exploring creativity and technology",
            f"✨ Diving into the world of {genre} through AI-powered imagination",
            f"🤖 Pushing artistic boundaries with {genre} themed AI art"
        ]
        
        # Add style and theme details
        captions = []
        for base in base_captions:
            caption = base
            if style:
                caption += f" in {style} style"
            if theme:
                caption += f", exploring the theme of {theme}"
            captions.append(caption)
        
        # Add hashtags if enabled
        if captions_config.get('use_emojis', True):
            hashtag_style = captions_config.get('hashtag_style', 'comprehensive')
            
            if hashtag_style == 'comprehensive':
                hashtags = captions_config.get('custom_hashtags', []) + [
                    f"#{genre.capitalize()}Art", 
                    "#AICreativity", 
                    "#GenerativeArt"
                ]
                
                # Add style and theme specific hashtags
                if style:
                    hashtags.append(f"#{style.replace(' ', '')}Art")
                if theme:
                    hashtags.append(f"#{theme.replace(' ', '').replace('\'', '')}")
                
            elif hashtag_style == 'minimal':
                hashtags = [f"#{genre.capitalize()}Art"]
            else:
                hashtags = []
            
            # Select a random caption and add hashtags
            caption = random.choice(captions) + "\n\n" + " ".join(hashtags)
            
            return caption
        
        # If no hashtags, just return the caption
        return random.choice(captions)

    def test_post(self, content_type='posts'):
        """
        Test the posting functionality by generating and posting content
        
        Args:
            content_type (str): Type of content to post ('posts' or 'stories')
        """
        try:
            # Get content configuration
            content_config = self.config['content_generation'][content_type]
            
            # Get random genre from configured genres
            genre = random.choice(content_config['genres'])
            
            # Get style and theme for the genre
            style = random.choice(content_config['styles'].get(genre, [None]))
            theme = random.choice(content_config['themes'].get(genre, [None]))
            palette = random.choice(content_config['palettes'].get(genre, [None]))
            
            self.logger.info(f"Generating {genre} image with style: {style}, theme: {theme}, palette: {palette}")
            
            # Generate image
            generated_images = self.image_generator.generate_art(
                genre=genre,
                num_images=1,
                resolution=content_config.get('resolution', "1024x1024"),
                extra_details=None
            )
            
            if not generated_images:
                self.logger.error("Failed to generate image")
                return
            
            # Get the first generated image and its metadata
            image_data = generated_images[0]
            
            # Generate caption using metadata
            caption = self.generate_caption(
                genre=image_data['metadata']['genre'],
                style=image_data['metadata']['style'],
                theme=image_data['metadata']['theme']
            )
            
            # Create BytesIO object from image data
            image_io = io.BytesIO(image_data['image_data'])
            
            # Post to Instagram
            self.instagram.post_image(
                image_io,
                caption=caption,
                is_story=(content_type == 'stories')
            )
            
        except Exception as e:
            self.logger.error(f"Error in test_post: {str(e)}")
            raise

def main():
    # Instantiate the tester
    tester = AIPostTester()
    
    # Test posting posts
    tester.logger.info("🚀 Starting POST test...")
    tester.test_post('posts')
    
    # Test posting stories (if enabled)
    if tester.config['content_generation'].get('stories', {}).get('enabled', False):
        tester.logger.info("\n🌟 Starting STORY test...")
        tester.test_post('stories')
    
    # Exit with appropriate status
    sys.exit(0)

if __name__ == "__main__":
    main()
