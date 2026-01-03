"""Base64 encoding logic for expression images."""

import base64
from io import BytesIO

from PIL import Image

from domain import EXPRESSION_LABELS
from domain.models import ExpressionImage, ExpressionSet


class Base64Encoder:
    """Encodes expression images to Base64 format."""

    def __init__(self, quality: int = 85, format: str = "JPEG"):
        """
        Initialize the encoder.

        Args:
            quality: JPEG quality (1-100, default: 85)
            format: Output format (default: JPEG)

        Raises:
            ValueError: If quality is not in range 1-100
        """
        if not 1 <= quality <= 100:
            raise ValueError(f"Quality must be 1-100, got {quality}")
        self.quality = quality
        self.format = format

    def encode_image(self, image: Image.Image) -> str:
        """
        Encode a PIL Image to Base64.

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded string
        """
        buffer = BytesIO()
        image.save(buffer, format=self.format, quality=self.quality)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def encode_expressions(self, images: list[tuple[str, Image.Image]]) -> ExpressionSet:
        """
        Encode a list of expression images to an ExpressionSet.

        Args:
            images: List of (expression_code, image) tuples

        Returns:
            ExpressionSet with Base64-encoded images
        """
        expressions: dict[str, ExpressionImage] = {}

        for code, image in images:
            label = EXPRESSION_LABELS.get(code, code)
            base64_data = self.encode_image(image)
            expressions[code] = ExpressionImage(
                code=code,
                label=label,
                base64_data=base64_data,
            )

        return ExpressionSet(expressions=expressions)

    def to_json_dict(self, expression_set: ExpressionSet) -> dict[str, str]:
        """
        Convert an ExpressionSet to a JSON-serializable dictionary.

        Args:
            expression_set: The expression set to convert

        Returns:
            Dictionary mapping codes to data URIs
        """
        mime_type = "image/jpeg" if self.format == "JPEG" else f"image/{self.format.lower()}"
        return {
            code: expr.to_data_uri(mime_type) for code, expr in expression_set.expressions.items()
        }
