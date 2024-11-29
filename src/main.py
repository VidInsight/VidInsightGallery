import os
import random
import logging
from dotenv import load_dotenv
import schedule
import time
import yaml

from src.modules.art_generator import GenreArtGenerator
from src.modules.instagram_poster import InstagramPoster

class AIPostPipeline:
    def __init__(self, config_path='../config.yaml'):
        """
        Initializes the AI Post Pipeline with configuration from YAML file.
        
        :param config_path: Path to the configuration YAML file
        """
        # Load environment variables
        load_dotenv()

        # Load configuration
        try:
            with open(os.path.join(os.path.dirname(__file__), config_path), 'r') as config_file:
                self.config = yaml.safe_load(config_file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}  # Fallback to empty config

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config.get('logging', {}).get('level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    self.config.get('logging', {}).get('file_path', 'ai_post_pipeline.log')
                ),
                logging.StreamHandler() if self.config.get('logging', {}).get('console_output', True) else None
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Validate environment variables
        self.instagram_username = os.getenv('INSTAGRAM_USERNAME')
        self.instagram_password = os.getenv('INSTAGRAM_PASSWORD')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        if not self.instagram_username or not self.instagram_password:
            self.logger.error("Instagram credentials are missing in environment variables.")
            raise ValueError("Instagram username or password not set.")
        
        if not self.openai_api_key:
            self.logger.error("OpenAI API key is missing in environment variables.")
            raise ValueError("OpenAI API key not set.")

        # Initialize modules
        self.image_generator = GenreArtGenerator(api_key=self.openai_api_key)
        self.instagram_poster = InstagramPoster(self.instagram_username, self.instagram_password)

    def generate_daily_content(self):
        """
        Generates and posts daily content based on configuration.
        """
        try:
            # Check if Instagram posting is enabled
            if not self.config.get('social_media', {}).get('instagram', {}).get('enabled', True):
                self.logger.info("Instagram posting is disabled in configuration.")
                return

            # Login to Instagram
            if not self.instagram_poster.login():
                self.logger.error("Failed to log in to Instagram. Skipping content generation.")
                return

            # Generate Posts
            posts_config = self.config.get('content_generation', {}).get('posts', {})
            if posts_config.get('enabled', True):
                post_count = posts_config.get('count', 2)
                post_genres = posts_config.get('genres', list(self.image_generator.genres.keys()))
                post_resolution = posts_config.get('resolution', '1080x1080')

                for _ in range(post_count):
                    genre = random.choice(post_genres)
                    images = self.image_generator.generate_art(
                        genre=genre, 
                        num_images=1, 
                        resolution=post_resolution
                    )
                    
                    if images:
                        validated_image = self.instagram_poster.validate_and_resize_image(images[0])
                        caption = self._generate_caption(genre)
                        self.instagram_poster.post_photo(validated_image, caption)
                        self.logger.info(f"Posted image for genre: {genre}")

            # Generate Stories
            stories_config = self.config.get('content_generation', {}).get('stories', {})
            if stories_config.get('enabled', True):
                story_count = stories_config.get('count', 1)
                story_genres = stories_config.get('genres', list(self.image_generator.genres.keys()))
                story_resolution = stories_config.get('resolution', '1080x1920')

                for _ in range(story_count):
                    genre = random.choice(story_genres)
                    story_images = self.image_generator.generate_art(
                        genre=genre, 
                        num_images=1, 
                        resolution=story_resolution
                    )
                    
                    if story_images:
                        validated_story = self.instagram_poster.validate_and_resize_image(story_images[0])
                        self.instagram_poster.post_story(validated_story)
                        self.logger.info(f"Posted story for genre: {genre}")

        except Exception as e:
            self.logger.error(f"Error in daily content generation: {e}")
            self._handle_error(e)

    def _generate_caption(self, genre):
        """
        Generate a creative caption based on the genre and configuration.
        
        :param genre: Art genre
        :return: Generated caption
        """
        # Base genre captions
        genre_captions = {
            "abstract": "Dive into the world of abstract art, where imagination knows no bounds! 🎨✨",
            "game": "Level up your visual experience with this gaming-inspired masterpiece! 🎮🌟",
            "movie": "Cinematic vibes captured in a single frame. Lights, camera, art! 🎬🖼️",
            "portrait": "Capturing the essence of human emotion through digital art. 👤🌈",
            "van_gogh": "Inspired by the master himself - a tribute to Van Gogh's timeless style! 🌻🖌️",
            "anime": "Anime-inspired art that tells a story beyond words. 🌟📺",
            "photography": "A moment frozen in time, reimagined through AI. 📸✨",
            "fantasy": "Step into a realm where fantasy becomes reality. 🐉🌈"
        }
        
        # Get caption configuration
        captions_config = self.config.get('captions', {})
        
        # Select caption
        caption = genre_captions.get(genre, "Art generated by AI, inspired by endless creativity! 🚀🎨")
        
        # Add emojis if enabled
        if captions_config.get('use_emojis', True):
            # Emojis are already in the predefined captions
            pass
        
        # Add hashtags based on configuration
        hashtag_style = captions_config.get('hashtag_style', 'comprehensive')
        custom_hashtags = captions_config.get('custom_hashtags', [])
        
        if hashtag_style == 'comprehensive':
            hashtags = f"\n\n#AIArt #GenerativeArt #{genre.capitalize()}Art " + \
                       " ".join(custom_hashtags)
        elif hashtag_style == 'minimal':
            hashtags = f"\n\n#{genre.capitalize()}Art"
        else:
            hashtags = ""
        
        return caption + hashtags

    def _handle_error(self, error):
        """
        Handle errors based on configuration.
        
        :param error: Exception that occurred
        """
        error_config = self.config.get('error_handling', {})
        retry_attempts = error_config.get('retry_attempts', 3)
        retry_delay = error_config.get('retry_delay_minutes', 15)
        
        # Log error details
        self.logger.error(f"Error details: {error}")
        
        # Send error notifications if enabled
        if error_config.get('send_error_notifications', False):
            notification_email = error_config.get('notification_email')
            if notification_email:
                # Implement email notification logic here
                self.logger.info(f"Error notification sent to {notification_email}")

def main():
    """
    Main function to run the AI Post Pipeline
    """
    pipeline = AIPostPipeline()
    
    # Schedule runs based on configuration
    scheduling_config = pipeline.config.get('scheduling', {}).get('daily_runs', [])
    
    # Run immediately
    pipeline.generate_daily_content()
    
    # Schedule daily runs
    for run in scheduling_config:
        if run.get('enabled', False):
            schedule.every().day.at(run['time']).do(pipeline.generate_daily_content)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()