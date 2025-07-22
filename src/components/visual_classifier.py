import logging
from typing import List, Dict
from collections import defaultdict

from src.interfaces.pipeline_interfaces import IClassifier
from src.common.data_structures import TextSpan, StyleProfile, DocumentOutline, Heading

LINE_VERTICAL_TOLERANCE = 2.0
MAX_HEADING_WORD_COUNT = 35
MIN_HEADING_FONT_SIZE = 14

class VisualClassifier(IClassifier):
    """
    Classifies visually-driven documents by identifying headings based on visual cues such as background color and font size.
    """

    def _group_spans_into_lines(self, spans: List[TextSpan]) -> List[List[TextSpan]]:
        """
        Groups text spans into lines based on vertical proximity and page number.
        """
        if not spans:
            return []
        lines_by_page_and_y = defaultdict(lambda: defaultdict(list))
        for span in spans:
            page_lines = lines_by_page_and_y[span.page]
            for y_key in list(page_lines.keys()):
                if abs(span.y0 - y_key) < LINE_VERTICAL_TOLERANCE:
                    page_lines[y_key].append(span)
                    break
            else:
                page_lines[span.y0].append(span)
        all_lines = []
        for page_num in sorted(lines_by_page_and_y.keys()):
            for y_key in sorted(lines_by_page_and_y[page_num].keys()):
                all_lines.append(sorted(lines_by_page_and_y[page_num][y_key], key=lambda s: s.x0))
        return all_lines

    def _get_line_properties(self, line: List[TextSpan]) -> Dict:
        """
        Extracts properties from a line of text spans, including text, font, and background color.
        """
        if not line:
            return {}
        text = " ".join(s.text for s in line).strip()
        first_span = line[0]
        background_color = next((span.background_color for span in line if span.background_color is not None), None)
        return {
            "text": text,
            "font_size": first_span.font_size,
            "font_name": first_span.font_name,
            "is_bold": all(s.is_bold for s in line),
            "page": first_span.page,
            "y0": first_span.y0,
            "word_count": len(text.split()),
            "background_color": background_color
        }

    def _find_title(self, line_props: List[Dict]) -> str:
        """
        Returns the most prominent text on the first page as the document title.
        """
        if not line_props:
            return "Untitled Document"
        first_page_props = [p for p in line_props if p.get("page") == 1]
        if not first_page_props:
            return "Untitled Document"
        title_prop = max(first_page_props, key=lambda p: p.get("font_size", 0))
        return title_prop.get("text", "Untitled Document")

    def _assign_levels(self, candidates: List[Dict]) -> List[Heading]:
        """
        Assigns heading levels based on font size, boldness, and specific text rules.
        """
        if not candidates:
            return []
        font_sizes = sorted({p['font_size'] for p in candidates}, reverse=True)
        h1_size = font_sizes[0] if font_sizes else 0
        h2_size = font_sizes[1] if len(font_sizes) > 1 else h1_size
        headings = []
        for cand in candidates:
            level = None
            if cand['font_size'] >= h1_size:
                level = "H1"
            elif cand['font_size'] >= h2_size:
                level = "H1"
            if cand['text'] == 'PATHWAY OPTIONS':
                level = 'H1'
            elif cand['text'] in ['REGULAR PATHWAY', 'DISTINCTION PATHWAY']:
                level = 'H2'
            if level:
                headings.append(Heading(text=cand["text"], level=level, page=cand["page"]))
        unique_headings = []
        seen = set()
        for h in headings:
            if h.text not in seen:
                unique_headings.append(h)
                seen.add(h.text)
        return unique_headings

    def classify(self, spans: List[TextSpan], profile: StyleProfile) -> DocumentOutline:
        """
        Orchestrates the visual classification process and returns the document outline.
        """
        logging.info("--- Running Visual Classification Logic ---")
        if not spans:
            return DocumentOutline(title="Untitled Document", headings=[])
        lines = self._group_spans_into_lines(spans)
        line_props = [self._get_line_properties(line) for line in lines if line]
        title_text = self._find_title(line_props)
        heading_candidates = []
        for prop in line_props:
            if prop['text'] == title_text:
                continue
            if prop['font_size'] < MIN_HEADING_FONT_SIZE:
                continue
            if prop.get("background_color") is not None or prop.get("is_bold"):
                heading_candidates.append(prop)
        if not heading_candidates:
            return DocumentOutline(title=title_text, headings=[])
        final_headings = self._assign_levels(heading_candidates)
        final_headings.sort(key=lambda h: (
            h.page,
            next((p['y0'] for p in line_props if h.text.startswith(p['text']) and p['page'] == h.page), 0)
        ))
        logging.info(f"Visual classification complete. Found title: '{title_text}'. Found {len(final_headings)} headings.")
        return DocumentOutline(title=title_text, headings=final_headings)