import logging
from collections import Counter
from typing import List, Tuple

from src.interfaces.pipeline_interfaces import IAnalyzer
from src.common.data_structures import TextSpan, StyleProfile

class StyleAnalyzer(IAnalyzer):
    """
    Analyzes the stylistic properties of a document's text to create a
    detailed profile of the body text, which serves as a baseline for classification.
    """

    def _get_most_common_size(self, spans: List[TextSpan]) -> int:
        """
        Calculates the most frequently occurring font size (the statistical mode)
        in the document, which is the most reliable indicator of body text.

        Returns:
            The most common font size as an integer, or 0 if none can be found.
        """
        try:
            font_sizes = [s.font_size for s in spans]
            size_counts = Counter(font_sizes)
            return size_counts.most_common(1)[0][0]
        except IndexError:
            logging.warning("Could not determine the most common font size from the provided spans.")
            return 0

    def _get_dominant_style_for_size(self, spans: List[TextSpan], target_size: int) -> Tuple[str, bool, int]:
        """
        Finds the most common style (font name, weight, and color) for a given font size.

        Args:
            spans: The list of all text spans in the document.
            target_size: The specific font size to analyze (e.g., the body text size).

        Returns:
            A tuple containing the most common font name, boldness, and color.
        """
        # Filter for spans that match the target size.
        relevant_spans = [s for s in spans if s.font_size == target_size]

        if not relevant_spans:
            logging.warning(f"No spans found with the target size {target_size} to analyze for style.")
            return "", False, 0

        # Create a tuple of style properties to find the most common combination.
        style_tuples = [(s.font_name, s.is_bold, s.color) for s in relevant_spans]
        style_counts = Counter(style_tuples)

        if not style_counts:
            return "", False, 0

        # The most common style tuple gives us all the properties we need.
        dominant_style = style_counts.most_common(1)[0][0]
        return dominant_style[0], dominant_style[1], dominant_style[2]


    def analyze(self, spans: List[TextSpan]) -> StyleProfile:
        """
        Analyzes text spans to find the primary style of the body text.
        The main method now orchestrates calls to private helper methods.

        Args:
            spans: A list of TextSpan objects from the PDFExtractor.

        Returns:
            A detailed StyleProfile object.
        """
        if not spans:
            logging.warning("No text spans provided to StyleAnalyzer. Returning empty profile.")
            return StyleProfile()

        # Step 1: Determine the size of the body text.
        body_size = self._get_most_common_size(spans)

        # Step 2: Determine the dominant style for that body text size.
        body_font, body_bold, body_color = self._get_dominant_style_for_size(spans, body_size)

        # Step 3: Assemble the final profile.
        profile = StyleProfile(
            body_text_size=body_size,
            body_font_name=body_font,
            body_is_bold=body_bold,
            body_color=body_color
        )
        
        logging.info(f"Style analysis complete. Body text profile: [Size: {profile.body_text_size}pt, Font: '{profile.body_font_name}', Bold: {profile.body_is_bold}, Color: {profile.body_color}]")
        
        return profile