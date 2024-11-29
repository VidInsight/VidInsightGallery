from instagrapi import Client
import os
import logging
import time
from dotenv import load_dotenv
from PIL import Image

class InstagramPoster:
    TARGET_SIZE = (1080, 1920)  # Default Instagram Story resolution
    MAX_FILE_SIZE_MB = 8       # Maximum file size for uploads (in MB)
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg')  # Supported image formats

    def __init__(self, username, password):
        """
        Initializes the InstagramPoster class.

        :param username: Instagram username
        :param password: Instagram password
        """
        self.client = Client()
        self.username = username
        self.password = password

        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def login(self):
        """
        Logs into the Instagram account using the provided credentials.

        :return: True if login is successful, False otherwise
        """
        try:
            self.client.login(self.username, self.password)
            self.logger.info("Successfully logged into Instagram.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log in: {e}")
            return False

    def validate_and_resize_image(self, image_path, target_size=None, padding_color=(0, 0, 0)):
        """
        Validates and resizes the image to meet Instagram Story requirements.

        :param image_path: Path to the image file
        :param target_size: Target resolution (width, height) for Stories (default: 1080x1920)
        :param padding_color: RGB color for padding (default: black)
        :return: Path to the validated and resized image
        """
        try:
            # Use default target size if not provided
            if target_size is None:
                target_size = self.TARGET_SIZE

            # Open the image
            img = Image.open(image_path)

            # Check file size
            file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                self.logger.warning(f"Image size {file_size_mb}MB exceeds max limit of {self.MAX_FILE_SIZE_MB}MB")

            # Check file format
            if not image_path.lower().endswith(self.SUPPORTED_FORMATS):
                raise ValueError(f"Unsupported image format. Supported formats: {self.SUPPORTED_FORMATS}")

            # Calculate aspect ratio and resize
            img.thumbnail(target_size, Image.Resampling.LANCZOS)  # Updated from ANTIALIAS
            
            # Create a new image with the target size and paste the resized image
            new_img = Image.new('RGB', target_size, padding_color)
            paste_x = (target_size[0] - img.width) // 2
            paste_y = (target_size[1] - img.height) // 2
            new_img.paste(img, (paste_x, paste_y))

            # Save the resized image
            output_path = os.path.join(os.path.dirname(image_path), f"resized_{os.path.basename(image_path)}")
            new_img.save(output_path)

            self.logger.info(f"Adjusting aspect ratio for image: {image_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            return image_path  # Return original path if resizing fails

    def validate_image(self, image_path):
        """
        Validates if the image is supported and meets Instagram's file size requirements.

        :param image_path: Path to the image file
        :return: True if valid, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            if not image_path.lower().endswith(self.SUPPORTED_FORMATS):
                raise ValueError(f"Unsupported image format: {image_path}")

            file_size = os.path.getsize(image_path) / (1024 * 1024)  # Convert bytes to MB
            if file_size > self.MAX_FILE_SIZE_MB:
                raise ValueError(f"Image file is too large ({file_size:.2f} MB): {image_path}")

            return True
        except Exception as e:
            self.logger.error(f"Image validation failed: {e}")
            return False

    def post_story(self, image_path):
        """
        Uploads an image to Instagram as a Story.

        :param image_path: Path to the image file
        :return: True if the upload is successful, False otherwise
        """
        try:
            if not self.validate_image(image_path):
                return False

            validated_path = self.validate_and_resize_image(image_path)

            # Upload the image as a Story
            self.logger.info(f"Uploading image as a story: {validated_path}")
            self.client.photo_upload_to_story(validated_path)
            self.logger.info(f"Image uploaded successfully as a story: {validated_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error uploading image as a story: {e}")
            return False

    def post_stories_batch(self, image_paths, retry_attempts=3, delay=2):
        """
        Posts multiple images to Instagram as Stories sequentially.

        :param image_paths: List of image file paths
        :param retry_attempts: Number of retry attempts for failed uploads
        :param delay: Delay in seconds between each upload
        """
        for i, image_path in enumerate(image_paths):
            success = False

            for attempt in range(1, retry_attempts + 1):
                self.logger.info(f"Attempting to upload story {i+1}/{len(image_paths)}: {image_path} (Attempt {attempt})")
                success = self.post_story(image_path)
                if success:
                    break
                self.logger.warning(f"Retrying in {delay} seconds...")
                time.sleep(delay)

            if not success:
                self.logger.error(f"Failed to upload story after {retry_attempts} attempts: {image_path}")

    def upload_post(self, image_path, caption=''):
        """
        Uploads an image post to Instagram.

        :param image_path: Path to the image file to upload
        :param caption: Optional caption for the post
        :return: True if upload is successful, False otherwise
        """
        try:
            # Validate image before upload
            validated_image_path = self.validate_and_resize_image(image_path)
            
            # Upload the image
            media = self.client.photo_upload(validated_image_path, caption)
            
            self.logger.info(f"Successfully uploaded post. Media ID: {media.pk}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload post: {e}")
            return False

# Main script for testing
if __name__ == "__main__":
    load_dotenv()

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    if not username or not password:
        raise EnvironmentError("Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your environment variables.")

    poster = InstagramPoster(username, password)

    if poster.login():
        current_dir = os.getcwd()
        image_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.lower().endswith(poster.SUPPORTED_FORMATS)]

        if image_files:
            poster.post_stories_batch(image_files)
        else:
            poster.logger.info("No image files found in the current directory.")