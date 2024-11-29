from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired
)

import os
import logging
import time
from dotenv import load_dotenv
from PIL import Image
import io
import tempfile

class InstagramPoster:
    TARGET_SIZE = (1080, 1080)  # Default Instagram Post resolution
    STORY_SIZE = (1080, 1920)   # Default Instagram Story resolution
    MAX_FILE_SIZE_MB = 8        # Maximum file size for uploads (in MB)
    SUPPORTED_FORMATS = ('PNG', 'JPEG')  # Supported image formats

    def __init__(self, username=None, password=None):
        """
        Initializes the InstagramPoster class.

        Args:
            username (str, optional): Instagram username. Defaults to env variable.
            password (str, optional): Instagram password. Defaults to env variable.
        """
        self.username = username or os.getenv('INSTAGRAM_USERNAME')
        self.password = password or os.getenv('INSTAGRAM_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Instagram credentials not provided")
        
        # Create Client instance
        self.client = Client()
        
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Login during initialization
        self.login()
    
    def login(self):
        """
        Logs into the Instagram account using the provided credentials.
        """
        try:
            self.client.login(username=self.username, password=self.password)
            self.logger.info("Successfully logged into Instagram.")
            return True
        except LoginRequired as e:
            self.logger.error(f"Login required: {e}")
            raise
        except ChallengeRequired as e:
            self.logger.error(f"Challenge required during login: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during Instagram login: {type(e).__name__} - {str(e)}")
            raise

    def process_image(self, image_data, is_story=False):
        """
        Process image data to meet Instagram requirements.
        
        Args:
            image_data: Either BytesIO object or path to image file
            is_story (bool): Whether the image is for a story post
            
        Returns:
            BytesIO: Processed image data
        """
        try:
            # Handle both BytesIO and file path inputs
            if isinstance(image_data, (str, os.PathLike)):
                img = Image.open(image_data)
            elif isinstance(image_data, io.BytesIO):
                img = Image.open(image_data)
            else:
                raise ValueError("image_data must be either a file path or BytesIO object")
            
            # Set target size based on post type
            target_size = self.STORY_SIZE if is_story else self.TARGET_SIZE
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate aspect ratio
            aspect_ratio = img.width / img.height
            target_ratio = target_size[0] / target_size[1]
            
            if aspect_ratio > target_ratio:
                # Image is wider than target ratio
                new_width = target_size[0]
                new_height = int(new_width / aspect_ratio)
            else:
                # Image is taller than target ratio
                new_height = target_size[1]
                new_width = int(new_height * aspect_ratio)
            
            # Resize image maintaining aspect ratio
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create new image with padding
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            paste_x = (target_size[0] - new_width) // 2
            paste_y = (target_size[1] - new_height) // 2
            new_img.paste(img, (paste_x, paste_y))
            
            # Save to BytesIO
            output = io.BytesIO()
            new_img.save(output, format='JPEG', quality=95)
            output.seek(0)
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            raise

    def post_image(self, image_data, caption, is_story=False):
        """
        Post an image to Instagram.
        
        Args:
            image_data: Either BytesIO object or path to image file
            caption (str): Caption for the post
            is_story (bool): Whether to post as a story
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Process the image
            processed_image = self.process_image(image_data, is_story)
            
            # Create a temporary file for the processed image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(processed_image.getvalue())
                temp_path = temp_file.name
            
            try:
                if is_story:
                    result = self.client.photo_upload_to_story(temp_path, caption)
                    self.logger.info("Successfully posted story to Instagram")
                else:
                    result = self.client.photo_upload(temp_path, caption)
                    self.logger.info("Successfully posted image to Instagram feed")
                
                return True
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            self.logger.error(f"Failed to post image: {e}")
            raise

# Main script for testing
if __name__ == "__main__":
    load_dotenv()
    
    # Test the poster
    poster = InstagramPoster()
    
    # Test with a local image file
    test_image_path = "path/to/test/image.jpg"
    if os.path.exists(test_image_path):
        poster.post_image(test_image_path, "Test post from InstagramPoster")
