#!/usr/bin/env python3
"""
AIPostGenerator - Automated Instagram Content Generator and Poster

This script automates the process of generating and posting AI-created content to Instagram.
It uses OpenAI's DALL-E for image generation and handles Instagram posting with proper scheduling.

Features:
- AI-powered image generation with configurable styles and themes
- Automated Instagram posting with customizable schedules
- Comprehensive logging and error handling
- Configuration-based content management

Required Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key
    INSTAGRAM_USERNAME: Your Instagram username
    INSTAGRAM_PASSWORD: Your Instagram password

Usage:
    1. Set up environment variables (use .env file or export directly)
    2. Configure content settings in config.yaml
    3. Run the script:
        python main.py [--config path/to/config.yaml] [--test]
"""

import os
import sys
import yaml
import random
import logging
import schedule
import time
import io
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from src.modules.image_generator import GenreArtGenerator
from src.modules.instagram_poster import InstagramPoster

# Load environment variables
load_dotenv()

class AIPostScheduler:
    """
    Main scheduler class for handling automated Instagram posts.
    
    This class manages the entire workflow of generating AI images and posting
    them to Instagram according to a configured schedule.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the AI Post Scheduler with configuration
        
        Args:
            config_path (str, optional): Path to config file. Defaults to config.yaml in project root.
        """
        # Set default config path if none provided
        if config_path is None:
            config_path = project_root / 'config.yaml'
        
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Configure logging
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'ai_post_pipeline.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Initialize components
        try:
            self.image_generator = GenreArtGenerator()
            self.instagram_poster = InstagramPoster()
            self.logger.info("Successfully initialized AI Post Scheduler")
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}")
            raise

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
                    "#GenerativeArt",
                    "#AIArt",
                    "#GenerativeAI",
                    "#ArtificialIntelligence"
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
            
            caption = random.choice(captions) + "\n\n" + " ".join(hashtags)
        
        return caption

    def post_content(self, content_type='posts'):
        """
        Generate and post content based on configuration
        
        Args:
            content_type (str): Type of content to post ('posts' or 'stories')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get content configuration
            content_config = self.config['content_generation'][content_type]
            
            if not content_config.get('enabled', False):
                self.logger.info(f"{content_type.capitalize()} generation is disabled.")
                return False

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
                return False
            
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
            self.instagram_poster.post_image(
                image_io,
                caption=caption,
                is_story=(content_type == 'stories')
            )
            
            self.logger.info(f"Successfully posted {genre} {content_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in posting {content_type}: {str(e)}")
            return False

    def run_daily_schedule(self):
        """
        Set up daily posting schedule based on configuration
        """
        daily_runs = self.config.get('scheduling', {}).get('daily_runs', [])
        
        for run_config in daily_runs:
            if run_config.get('enabled', False):
                schedule_time = run_config.get('time', '10:00')
                
                # Schedule posts
                schedule.every().day.at(schedule_time).do(self.post_content, 'posts')
                
                # Schedule stories if enabled
                if self.config['content_generation'].get('stories', {}).get('enabled', False):
                    schedule.every().day.at(schedule_time).do(self.post_content, 'stories')
                
                self.logger.info(f"Scheduled daily run at {schedule_time}")

    def start(self):
        """
        Start the scheduling and keep the script running
        """
        try:
            self.run_daily_schedule()
            self.logger.info("AI Post Scheduler started. Waiting for scheduled tasks...")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute instead of every second
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}")
            raise

def test_run(config_path=None):
    """
    Perform a test run of the content generation and posting process
    
    Args:
        config_path (str, optional): Path to config file
    """
    try:
        scheduler = AIPostScheduler(config_path)
        scheduler.post_content('posts')
    except Exception as e:
        logging.error(f"Test run failed: {str(e)}")
        sys.exit(1)

def main():
    """
    Main entry point for the AIPostGenerator
    """
    parser = argparse.ArgumentParser(description='AI-powered Instagram content generator and poster')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--test', action='store_true', help='Perform a test run')
    
    args = parser.parse_args()
    
    try:
        if args.test:
            test_run(args.config)
        else:
            scheduler = AIPostScheduler(args.config)
            scheduler.start()
    except Exception as e:
        logging.error(f"Failed to start scheduler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
