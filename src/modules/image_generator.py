import os
import logging
import requests
import random
from dotenv import load_dotenv

# Load environment variables at the beginning
load_dotenv()

class GenreArtGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("API key is not provided. Set it via the 'OPENAI_API_KEY' environment variable or pass it explicitly.")
        
        self.endpoint = "https://api.openai.com/v1/images/generations"
        
        # Logging configuration
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        # Genre-specific data
        self.genres = {
            "abstract": {
                "sub-genres": ["Minimalist", "Cubist", "Fluid Art", "Surreal Abstract"],
                "themes": ["geometric chaos", "color burst", "dreamscapes"],
                "styles": ["modern", "surreal", "cubist"],
                "palettes": ["neon", "gradient", "monochrome"]
            },
            "game": {
                "sub-genres": ["Fantasy", "Sci-Fi", "Cyberpunk", "Steampunk", "Pixel Art"],
                "themes": ["fantasy world", "cyberpunk city", "alien planet"],
                "styles": ["3D render", "pixel art", "hand-painted"],
                "palettes": ["vivid", "dark", "neon lights"]
            },
            "movie": {
                "sub-genres": ["Noir", "Sci-Fi", "Fantasy", "Historical Drama", "Horror"],
                "themes": ["sci-fi epic", "historical drama", "cosmic horror"],
                "styles": ["cinematic", "realistic", "dramatic"],
                "palettes": ["warm tones", "cool tones", "monochrome"]
            },
            "portrait": {
                "sub-genres": ["Classical", "Digital", "Fantasy Portrait", "Realistic AI Portrait"],
                "themes": ["mystical figure", "regal elegance", "fantasy character"],
                "styles": ["classical", "realistic", "digital painting"],
                "palettes": ["soft pastels", "vivid", "monochrome"]
            },
            "van_gogh": {
                "sub-genres": ["Starry Night", "Sunflowers", "Wheat Field", "Post-Impressionist Portraits"],
                "themes": ["starry night", "sunflower field", "vibrant countryside"],
                "styles": ["Van Gogh"],
                "palettes": ["warm yellows", "cool blues", "earth tones"]
            },
            "anime": {
                "sub-genres": ["Shonen", "Shojo", "Cyberpunk Anime", "Fantasy Anime"],
                "themes": ["heroic battles", "romantic landscapes", "cyberpunk future"],
                "styles": ["anime-style", "digital art"],
                "palettes": ["vivid", "soft tones", "high contrast"]
            },
            "photography": {
                "sub-genres": ["Black-and-White Photography", "HDR Photography", "Minimalist Photography"],
                "themes": ["urban exploration", "nature's beauty", "minimalist design"],
                "styles": ["photorealistic", "cinematic"],
                "palettes": ["monochrome", "soft gradients", "natural colors"]
            },
            "fantasy": {
                "sub-genres": ["Dark Fantasy", "High Fantasy", "Mythological", "Dystopian Fantasy"],
                "themes": ["mystical realms", "ancient gods", "post-apocalyptic worlds"],
                "styles": ["fantasy painting", "dark surrealism"],
                "palettes": ["vivid", "muted earth tones", "dreamlike"]
            }
        }

    def generate_art(self, genre, sub_genre=None, num_images=3, resolution="1024x1024", extra_details=None):
        """
        Generate a specified number of images for a given genre and sub-genre.

        :param genre: Art genre (e.g., abstract, game, movie, etc.)
        :param sub_genre: Specific sub-genre (e.g., Cubist for abstract)
        :param num_images: Number of images to generate
        :param resolution: Resolution of the generated images
        :param extra_details: Additional details for the prompt
        :return: List of file paths for generated images
        """
        if genre not in self.genres:
            raise ValueError(f"Genre '{genre}' is not supported. Available genres: {', '.join(self.genres.keys())}")
        
        genre_details = self.genres[genre]
        
        if sub_genre and sub_genre not in genre_details["sub-genres"]:
            raise ValueError(f"Sub-genre '{sub_genre}' is not valid for genre '{genre}'. "
                             f"Available sub-genres: {', '.join(genre_details['sub-genres'])}")

        generated_images = []

        for i in range(num_images):
            # Generate prompt components
            theme = random.choice(genre_details["themes"])
            style = random.choice(genre_details["styles"])
            palette = random.choice(genre_details["palettes"])
            
            self.logger.info(f"Generating image {i+1} with: Genre='{genre}', Sub-genre='{sub_genre}', "
                             f"Theme='{theme}', Style='{style}', Palette='{palette}'")
            
            # Generate art and save the file
            save_path = self.generate_art_image(
                theme, style, palette, resolution, genre, sub_genre, extra_details
            )
            if save_path:
                generated_images.append(save_path)
        
        return generated_images

    def generate_art_image(self, theme, style, palette, resolution, genre, sub_genre, extra_details=None):
        """
        Core function to generate high-quality images using the OpenAI API.

        :param theme: Art theme
        :param style: Art style
        :param palette: Color palette
        :param resolution: Image resolution
        :param genre: Art genre
        :param sub_genre: Sub-genre of the art
        :param extra_details: Additional details for the prompt
        :return: File path of the generated image
        """
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        # Enhanced prompt with more context and detail
        enhanced_prompt = self._create_enhanced_genre_prompt(theme, style, palette, genre, sub_genre, extra_details)
        
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=resolution,
                quality="hd",  # Upgrade to HD quality
                n=1,
                response_format="url"
            )
            
            image_url = response.data[0].url
            
            # Download the image
            img_data = requests.get(image_url).content
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), 'generated_images')
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the image
            filename = f"{genre}_{sub_genre}_{theme}_{style}_{palette}_hd.png".replace(" ", "_")
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as handler:
                handler.write(img_data)
            
            self.logger.info(f"High-quality image saved: {filepath}")
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error generating high-quality image: {e}")
            return None

    def _create_enhanced_genre_prompt(self, theme, style, palette, genre, sub_genre, extra_details=None):
        """
        Create an enhanced, detailed prompt for image generation.
        
        :param theme: Art theme
        :param style: Art style
        :param palette: Color palette
        :param genre: Art genre
        :param sub_genre: Sub-genre of the art
        :param extra_details: Additional details for the prompt
        :return: Enhanced prompt string
        """
        # Base prompt structure with increased detail and context
        base_prompt = (
            f"A highly detailed, professional {style} artwork in the {genre} genre, "
            f"specifically in the {sub_genre} sub-genre. Theme: {theme}. "
            f"Color palette: {palette} tones. "
            "Exceptional artistic quality, intricate details, "
            "perfect composition, cinematic lighting, "
            "sharp focus, high resolution digital art. "
        )
        
        # Add extra details if provided
        if extra_details:
            base_prompt += f"Additional context: {extra_details}. "
        
        # Add some randomness and artistic flair
        artistic_modifiers = [
            "Hyper-realistic rendering. ",
            "Stunning visual complexity. ",
            "Breathtaking artistic interpretation. ",
            "Masterful use of light and shadow. ",
            "Exceptional level of detail and precision. "
        ]
        base_prompt += random.choice(artistic_modifiers)
        
        return base_prompt