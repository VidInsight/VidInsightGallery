"""
my_project: A package for generating stunning art and managing Instagram posts.

Modules:
    - art_generator: Contains the GenreArtGenerator class for generating genre-based art.
    - instagram_poster: Contains the InstagramPoster class for managing Instagram posts and stories.
"""

from .image_generator import GenreArtGenerator
from .instagram_poster import InstagramPoster

__all__ = ["GenreArtGenerator", "InstagramPoster"]