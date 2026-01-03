"""Data models for MakeExpressionJson."""

from dataclasses import dataclass


@dataclass
class GridConfig:
    """Configuration for the expression grid."""

    rows: int
    cols: int
    cell_size: int

    @property
    def total_width(self) -> int:
        """Total width of the grid in pixels."""
        return self.cols * self.cell_size

    @property
    def total_height(self) -> int:
        """Total height of the grid in pixels."""
        return self.rows * self.cell_size

    @property
    def total_cells(self) -> int:
        """Total number of cells in the grid."""
        return self.rows * self.cols


@dataclass
class ExpressionImage:
    """Represents a single expression image."""

    code: str
    label: str
    base64_data: str | None = None

    def to_data_uri(self, mime_type: str = "image/jpeg") -> str:
        """
        Convert to a data URI for embedding in HTML.

        Args:
            mime_type: MIME type of the image (default: image/jpeg)

        Returns:
            Data URI string
        """
        if not self.base64_data:
            raise ValueError(f"No base64 data available for expression: {self.code}")
        return f"data:{mime_type};base64,{self.base64_data}"


@dataclass
class ExpressionSet:
    """A complete set of 20 expressions."""

    expressions: dict[str, ExpressionImage]

    def to_json_dict(self) -> dict[str, str]:
        """
        Convert to a dictionary suitable for JSON serialization.

        Returns:
            Dictionary mapping expression codes to data URIs
        """
        return {
            code: expr.to_data_uri()
            for code, expr in self.expressions.items()
            if expr.base64_data
        }

    def get(self, code: str) -> ExpressionImage | None:
        """Get an expression by code."""
        return self.expressions.get(code)

    def __len__(self) -> int:
        return len(self.expressions)
