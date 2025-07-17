# src/components/json_formatter.py

import json
import logging
from src.interfaces.pipeline_interfaces import IFormatter
from src.common.data_structures import DocumentOutline

class JSONFormatter(IFormatter):
    """
    Concrete implementation of the IFormatter interface.
    This class is responsible for serializing the final DocumentOutline
    object into the specified JSON format for submission.
    """
    def format(self, outline: DocumentOutline) -> str:
        """
        Converts the DocumentOutline object to a JSON string with an indent of 2,
        as specified in the hackathon documentation.

        Args:
            outline: The structured document outline from the classifier.

        Returns:
            A JSON formatted string.
        """
        try:
            output_dict = {
                "title": outline.title,
                "outline": [
                    {"level": h.level, "text": h.text, "page": h.page}
                    for h in outline.headings
                ]
            }
            # The challenge specifies an indent of 2 in its sample output.
            return json.dumps(output_dict, indent=2)
        except Exception as e:
            logging.error(f"Failed to format document outline to JSON. Error: {e}", exc_info=True)
            return "{}" # Return an empty JSON object on failure