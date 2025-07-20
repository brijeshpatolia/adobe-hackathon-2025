# src/components/heading_classifier.py

import logging
import re
from typing import List, Tuple, Dict
from collections import defaultdict, Counter

# Assuming these are in your project structure
from src.interfaces.pipeline_interfaces import IClassifier
from src.common.data_structures import TextSpan, StyleProfile, DocumentOutline, Heading

# --- Constants for Readability & Tuning ---
LINE_VERTICAL_TOLERANCE = 2.0
MIN_HEADING_FONT_SIZE_INCREASE = 2
MAX_HEADING_WORD_COUNT = 35 # Increased for long headings
FORM_DETECTION_THRESHOLD_RATIO = 0.8 
# NEW: Define header/footer vertical position thresholds (e.g., top/bottom 15% of a standard page)
HEADER_Y_THRESHOLD = 120 # Points from top
FOOTER_Y_THRESHOLD = 700 # Points from top

class HeadingClassifier(IClassifier):
    """
    A robust, multi-heuristic classifier that correctly identifies document structure
    by filtering out headers/footers, tables of contents, and detecting document types
    like forms before applying a refined style-based hierarchy analysis.
    """

    def _group_spans_into_lines(self, spans: List[TextSpan]) -> List[List[TextSpan]]:
        """Groups individual text spans into coherent lines based on their vertical position."""
        if not spans:
            return []
        
        lines_by_page_and_y = defaultdict(lambda: defaultdict(list))
        for span in spans:
            page_lines = lines_by_page_and_y[span.page]
            found_line = False
            for y_key in list(page_lines.keys()):
                if abs(span.y0 - y_key) < LINE_VERTICAL_TOLERANCE:
                    page_lines[y_key].append(span)
                    found_line = True
                    break
            if not found_line:
                page_lines[span.y0].append(span)

        all_lines = []
        for page_num in sorted(lines_by_page_and_y.keys()):
            page_lines = lines_by_page_and_y[page_num]
            for y_key in sorted(page_lines.keys()):
                line_spans = sorted(page_lines[y_key], key=lambda s: s.x0)
                all_lines.append(line_spans)
        
        return all_lines

    def _get_line_properties(self, line: List[TextSpan]) -> Dict:
        """Calculates key properties of a line of text."""
        if not line: return {}
        
        text = " ".join(s.text for s in line).strip()
        first_span = line[0]
        
        return {
            "text": text, "font_size": first_span.font_size, "font_name": first_span.font_name,
            "is_bold": all(s.is_bold for s in line), "page": first_span.page, "y0": first_span.y0,
            "word_count": len(text.split())
        }
    
    def _filter_headers_and_footers(self, line_props: List[Dict]) -> List[Dict]:
        """
        **CRUCIAL FIX**: Removes repetitive header and footer lines.
        This is the main fix for the "Overview" spam.
        """
        potential_headers = defaultdict(int)
        potential_footers = defaultdict(int)

        # Identify lines that appear frequently in header/footer areas
        for prop in line_props:
            if prop['y0'] < HEADER_Y_THRESHOLD:
                potential_headers[prop['text']] += 1
            elif prop['y0'] > FOOTER_Y_THRESHOLD:
                potential_footers[prop['text']] += 1
        
        # Find headers/footers that appear on at least 2 pages
        headers = {text for text, count in potential_headers.items() if count >= 2}
        footers = {text for text, count in potential_footers.items() if count >= 2}
        
        # Filter out the identified lines
        return [
            prop for prop in line_props 
            if prop['text'] not in headers and prop['text'] not in footers
        ]

    def _is_table_of_contents_entry(self, line_text: str) -> bool:
        """Detects ToC entries."""
        return bool(re.search(r'.+\s*\.{4,}\s*\d+\s*$', line_text))

    def _find_title(self, line_props: List[Dict]) -> Tuple[str, int]:
        """Identifies the document title from the most prominent text on the first page."""
        if not line_props:
            return "Untitled Document", -1

        first_page_props = [p for p in line_props if p.get("page") == 1]
        if not first_page_props:
            return "Untitled Document", -1

        max_font_size = max((p.get("font_size", 0) for p in first_page_props), default=0)
        
        title_lines = []
        title_end_index = -1
        # Capture all contiguous lines on page 1 that have the max font size
        for i, prop in enumerate(line_props):
            if prop.get("page") == 1 and prop.get("font_size") == max_font_size:
                title_lines.append(prop["text"])
                title_end_index = i
            elif title_lines: # Stop after the first non-title line
                break
        
        return " ".join(title_lines) or "Untitled Document", title_end_index

    def _rank_heading_styles(self, candidates: List[Dict]) -> List[Tuple]:
        """Ranks heading styles primarily by font size, then by frequency."""
        style_counts = Counter((p["font_size"], p["font_name"], p["is_bold"]) for p in candidates)
        return sorted(style_counts, key=lambda style: (style[0], style_counts[style]), reverse=True)

    def _assign_levels(self, candidates: List[Dict], style_rank: List[Tuple]) -> List[Heading]:
        """
        Assigns H1-H3 levels based on a refined hierarchy logic.
        """
        headings = []
        if not style_rank: return []
        
        # Group styles by their font size to determine hierarchical level
        ranked_font_sizes = sorted(list(set(s[0] for s in style_rank)), reverse=True)
        level_map = {size: f"H{i+1}" for i, size in enumerate(ranked_font_sizes[:3])}

        for cand in candidates:
            line_text = cand["text"]
            level = None
            
            # Priority 1: Numerical prefixes (e.g., "2.1")
            match = re.match(r'^((\d+\.)+\d*)\s+', line_text)
            if match:
                level_num = len(re.findall(r'(\d+)', match.group(0)))
                if 1 <= level_num <= 3: level = f"H{level_num}"
            
            # Priority 2: Style-based hierarchy based on font size
            if not level:
                level = level_map.get(cand["font_size"])

            if level:
                headings.append(Heading(text=line_text, level=level, page=cand["page"]))

        return headings

    def classify(self, spans: List[TextSpan], profile: StyleProfile) -> DocumentOutline:
        """The main orchestration method for the classification process."""
        if not spans:
            return DocumentOutline(title="Untitled Document", headings=[])
            
        lines = self._group_spans_into_lines(spans)
        line_props = [self._get_line_properties(line) for line in lines if line]
        
        # **STEP 1: Filter out headers and footers BEFORE any other analysis**
        clean_line_props = self._filter_headers_and_footers(line_props)

        title_text, title_end_index = self._find_title(clean_line_props)
        
        heading_candidates = []
        for prop in clean_line_props:
            # Skip any remaining lines on the first page
            if prop['page'] == 1:
                continue

            if self._is_table_of_contents_entry(prop["text"]):
                continue

            is_stylistically_distinct = (
                (prop["is_bold"] and not profile.body_is_bold) or
                (prop["font_size"] >= profile.body_text_size + MIN_HEADING_FONT_SIZE_INCREASE)
            )

            if is_stylistically_distinct and prop["word_count"] < MAX_HEADING_WORD_COUNT:
                heading_candidates.append(prop)
        
        if not heading_candidates:
             return DocumentOutline(title=title_text, headings=[])
        
        ranked_styles = self._rank_heading_styles(heading_candidates)
        final_headings = self._assign_levels(heading_candidates, ranked_styles)
        
        final_headings.sort(key=lambda h: (h.page, next((p['y0'] for p in clean_line_props if h.text.startswith(p['text']) and p['page'] == h.page), 0)))

        logging.info(f"Classification complete. Found title: '{title_text}'. Found {len(final_headings)} headings.")
        return DocumentOutline(title=title_text, headings=final_headings)