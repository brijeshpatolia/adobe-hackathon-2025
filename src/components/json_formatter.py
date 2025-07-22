import json
import logging
from src.interfaces.pipeline_interfaces import IFormatter
from src.common.data_structures import DocumentOutline

class JSONFormatter(IFormatter):
    """
    Serializes a DocumentOutline object to a JSON-formatted string.
    """
    def format(self, outline: DocumentOutline) -> str:
        """
        Convert a DocumentOutline to a JSON string with an indent of 2.
        Args:
            outline: DocumentOutline instance to serialize.
        Returns:
            str: JSON-formatted string representation of the outline.
        """
        try:
            output_dict = {
                "title": outline.title,
                "outline": [
                    {"level": h.level, "text": h.text, "page": h.page}
                    for h in outline.headings
                ]
            }
            return json.dumps(output_dict, indent=2)
        except Exception as e:
            logging.error(f"Failed to format document outline to JSON: {e}", exc_info=True)
            return "{}"