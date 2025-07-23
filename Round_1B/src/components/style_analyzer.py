import logging
from collections import Counter
from typing import List, Tuple

from src.interfaces.pipeline_interfaces import IAnalyzer
from src.common.data_structures import TextSpan, StyleProfile

class StyleAnalyzer(IAnalyzer):
    """
    Analyzes stylistic properties of document text to profile the primary body text style.
    """

    def _get_most_common_size(self, spans: List[TextSpan]) -> int:
        """
        Returns the most frequent font size among text spans, or 0 if unavailable.
        """
        try:
            font_sizes = [s.font_size for s in spans]
            return Counter(font_sizes).most_common(1)[0][0]
        except IndexError:
            logging.warning("No font sizes found in provided spans.")
            return 0

    def _get_dominant_style_for_size(self, spans: List[TextSpan], target_size: int) -> Tuple[str, bool, int]:
        """
        Returns the most common (font name, boldness, color) tuple for the given font size.
        """
        relevant_spans = [s for s in spans if s.font_size == target_size]
        if not relevant_spans:
            logging.warning(f"No spans found with font size {target_size}.")
            return "", False, 0
        style_tuples = [(s.font_name, s.is_bold, s.color) for s in relevant_spans]
        style_counts = Counter(style_tuples)
        if not style_counts:
            return "", False, 0
        return style_counts.most_common(1)[0][0]

    def analyze(self, spans: List[TextSpan]) -> StyleProfile:
        """
        Returns a StyleProfile representing the dominant body text style in the spans.
        """
        if not spans:
            logging.warning("No text spans provided to StyleAnalyzer. Returning empty profile.")
            return StyleProfile()
        body_size = self._get_most_common_size(spans)
        body_font, body_bold, body_color = self._get_dominant_style_for_size(spans, body_size)
        profile = StyleProfile(
            body_text_size=body_size,
            body_font_name=body_font,
            body_is_bold=body_bold,
            body_color=body_color
        )
        logging.info(
            f"Style analysis complete. Body text profile: [Size: {profile.body_text_size}pt, Font: '{profile.body_font_name}', Bold: {profile.body_is_bold}, Color: {profile.body_color}]"
        )
        return profile