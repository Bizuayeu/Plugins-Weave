"""Protocol definitions for usecases layer.

This module defines abstract interfaces (Protocols) for the main use case classes,
enabling dependency injection and easier testing with mock objects.

Example usage:
    ```python
    from usecases.protocols import ImageSplitterProtocol

    def process_image(splitter: ImageSplitterProtocol) -> None:
        # Works with ImageSplitter or any mock that satisfies the protocol
        images = splitter.split_from_file("path/to/image.png")
    ```
"""

from typing import Protocol, runtime_checkable

from PIL import Image

from domain.models import ExpressionSet


@runtime_checkable
class ImageSplitterProtocol(Protocol):
    """Protocol for image splitting functionality.

    Defines the interface for splitting a grid image into individual expression images.

    Required methods:
        - validate_image: Validate image dimensions
        - split: Split a PIL Image into expression images
        - split_from_file: Split an image file into expression images
    """

    def validate_image(self, image: Image.Image) -> tuple[bool, str]:
        """Validate that the image can be split into the expected grid.

        Args:
            image: PIL Image object to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...

    def split(self, image: Image.Image) -> list[tuple[str, Image.Image]]:
        """Split a grid image into individual expression images.

        Args:
            image: PIL Image containing the expression grid

        Returns:
            List of (expression_code, cropped_image) tuples
        """
        ...

    def split_from_file(self, file_path: str) -> list[tuple[str, Image.Image]]:
        """Split a grid image file into individual expression images.

        Args:
            file_path: Path to the grid image file

        Returns:
            List of (expression_code, cropped_image) tuples
        """
        ...


@runtime_checkable
class Base64EncoderProtocol(Protocol):
    """Protocol for Base64 encoding functionality.

    Defines the interface for encoding images to Base64 format.

    Required methods:
        - encode_image: Encode a single image to Base64
        - encode_expressions: Encode multiple expression images
        - to_json_dict: Convert an ExpressionSet to JSON-serializable dict
    """

    def encode_image(self, image: Image.Image) -> str:
        """Encode a PIL Image to Base64.

        Args:
            image: PIL Image object to encode

        Returns:
            Base64 encoded string
        """
        ...

    def encode_expressions(self, images: list[tuple[str, Image.Image]]) -> ExpressionSet:
        """Encode a list of expression images to an ExpressionSet.

        Args:
            images: List of (expression_code, image) tuples

        Returns:
            ExpressionSet with Base64-encoded images
        """
        ...

    def to_json_dict(self, expression_set: ExpressionSet) -> dict[str, str]:
        """Convert an ExpressionSet to a JSON-serializable dictionary.

        Args:
            expression_set: The expression set to convert

        Returns:
            Dictionary mapping codes to data URIs
        """
        ...
