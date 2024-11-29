import os
import logging
import requests
import random
from dotenv import load_dotenv
import httpx
import io
import base64

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

    def generate_art(self, genre, sub_genre=None, num_images=1, resolution="1024x1024", extra_details=None):
        """
        Generate an image for a given genre and sub-genre, returning it as bytes in memory.

        Args:
            genre (str): Art genre (e.g., abstract, game, movie, etc.)
            sub_genre (str, optional): Specific sub-genre (e.g., Cubist for abstract)
            num_images (int, optional): Number of images to generate (default: 1)
            resolution (str, optional): Resolution of the generated images
            extra_details (str, optional): Additional details for the prompt

        Returns:
            list: List of image data as bytes objects
        """
        if genre not in self.genres:
            raise ValueError(f"Genre '{genre}' is not supported. Available genres: {', '.join(self.genres.keys())}")
        
        genre_details = self.genres[genre]
        
        if sub_genre and sub_genre not in genre_details["sub-genres"]:
            raise ValueError(f"Sub-genre '{sub_genre}' is not valid for genre '{genre}'. "
                             f"Available sub-genres: {', '.join(genre_details['sub-genres'])}")

        generated_images = []

        for _ in range(num_images):
            # Select random components if not specified
            selected_theme = random.choice(genre_details["themes"])
            selected_style = random.choice(genre_details["styles"])
            selected_palette = random.choice(genre_details["palettes"])
            
            # Construct the prompt
            prompt = f"Create a {genre} artwork"
            if sub_genre:
                prompt += f" in {sub_genre} style"
            prompt += f" with {selected_theme} theme, using {selected_style} artistic style"
            prompt += f" and a {selected_palette} color palette"
            if extra_details:
                prompt += f". Additional details: {extra_details}"

            try:
                # Create a custom HTTP client without proxy configuration
                client = httpx.Client(timeout=30.0)
                
                # Prepare the headers and data
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # Parse resolution into width and height
                width, height = map(int, resolution.split('x'))
                
                # Prepare the request data according to DALL-E API specifications
                data = {
                    "model": "dall-e-3",  # Specify DALL-E 3 model
                    "prompt": prompt,
                    "n": 1,  # DALL-E 3 only supports n=1
                    "size": f"{width}x{height}",
                    "quality": "standard",
                    "response_format": "b64_json"
                }

                self.logger.info(f"Sending request to OpenAI with prompt: {prompt}")
                
                # Make the API request
                response = client.post(self.endpoint, headers=headers, json=data)
                
                if response.status_code != 200:
                    error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                    self.logger.error(f"OpenAI API error: {error_detail}")
                    raise Exception(f"OpenAI API error: {error_detail}")
                
                response_data = response.json()
                
                # Get the image data from the response
                image_data = response_data["data"][0]["b64_json"]
                
                # Convert base64 to bytes
                image_bytes = base64.b64decode(image_data)
                
                generated_images.append({
                    'image_data': image_bytes,
                    'metadata': {
                        'genre': genre,
                        'sub_genre': sub_genre,
                        'theme': selected_theme,
                        'style': selected_style,
                        'palette': selected_palette
                    }
                })
                
                self.logger.info(f"Successfully generated {genre} image")
                
            except Exception as e:
                self.logger.error(f"Error generating image: {str(e)}")
                raise

        return generated_images

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Test different genres
    test_genres = ['game', 'abstract', 'movie', 'portrait', 'photography', 'fantasy']
    
    # Initialize generator
    generator = GenreArtGenerator()

    # Test image generation for each genre
    for genre in test_genres:
        print(f"\n🎨 Testing genre: {genre}")
        
        try:
            # Generate multiple images
            images = generator.generate_art(
                genre=genre, 
                num_images=2,  # Generate 2 images per genre
                extra_details='High-quality test generation'
            )
            
            # Print results
            if images:
                print(f"✅ Successfully generated {len(images)} images for {genre}")
                for img in images:
                    print(f"   🖼️ Image metadata: {img['metadata']}")
            else:
                print(f"❌ Failed to generate images for {genre}")
        
        except Exception as e:
            print(f"🚨 Error generating {genre} images: {e}")

    print("\n🏁 Image generation test completed.")