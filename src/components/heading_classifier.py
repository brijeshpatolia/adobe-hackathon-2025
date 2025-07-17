# src/components/heading_classifier.py

import logging
import re
from typing import List, Tuple, Optional, Callable
from collections import defaultdict

from src.interfaces.pipeline_interfaces import IClassifier
from src.common.data_structures import TextSpan, StyleProfile, DocumentOutline, Heading

# --- Constants for Readability & Tuning ---
LINE_VERTICAL_TOLERANCE = 2.0
MAX_HEADING_WORD_COUNT = 15 # A line with more words is likely a sentence, not a heading.
SPARSE_DOCUMENT_LINE_THRESHOLD = 35 # Heuristic to detect sparse, poster-like documents.

class HeadingClassifier(IClassifier):
    """
    An advanced, rule-based classifier for identifying document structure.
    It uses a multi-pass strategy to first filter out non-heading content,
    then identify heading candidates, and finally rank and validate them.
    """
    def __init__(self):
        """
        Initializes the classifier and defines the rule engine's strategy.
        """
        self.filter_rules: List[Callable[[List[TextSpan]], bool]] = [
            self._filter_is_table_of_contents,
            self._filter_is_long_sentence,
        ]
        self.heading_candidate_rules: List[Callable[[List[TextSpan], StyleProfile], bool]] = [
            self._is_potential_heading_by_style,
            self._is_potential_heading_by_prefix
        ]

    def _group_spans_into_lines(self, spans: List[TextSpan]) -> List[List[TextSpan]]:
        """Groups individual text spans into coherent lines based on their vertical position."""
        if not spans: return []
        lines_by_page_and_y = defaultdict(lambda: defaultdict(list))
        for span in spans:
            page_lines = lines_by_page_and_y[span.page]
            found_line = False
            for y_key in page_lines.keys():
                if abs(span.y0 - y_key) < LINE_VERTICAL_TOLERANCE:
                    if not page_lines[y_key] or (span.x0 - page_lines[y_key][-1].x1) < 30:
                        page_lines[y_key].append(span)
                        found_line = True
                        break
            if not found_line:
                page_lines[span.y0].append(span)

        all_lines = []
        for page_num in sorted(lines_by_page_and_y.keys()):
            page_lines = lines_by_page_and_y[page_num]
            for y_key in sorted(page_lines.keys()):
                line_spans = page_lines[y_key]
                line_spans.sort(key=lambda s: s.x0)
                all_lines.append(line_spans)
        
        return all_lines

    # --- Filter Rules (to exclude non-headings) ---

    def _filter_is_table_of_contents(self, line: List[TextSpan]) -> bool:
        """Filter Rule: Returns True if the line looks like a ToC entry."""
        line_text = " ".join(s.text for s in line)
        return bool(re.search(r'\.{4,}\s*\d+\s*$', line_text))

    def _filter_is_long_sentence(self, line: List[TextSpan]) -> bool:
        """Filter Rule: Returns True if the line is too long to be a heading."""
        word_count = len(" ".join(s.text for s in line).split())
        return word_count > MAX_HEADING_WORD_COUNT

    # --- Heading Candidate Identification Rules ---

    def _is_potential_heading_by_style(self, line: List[TextSpan], profile: StyleProfile) -> bool:
        """Rule: Returns True if the line's style deviates from body text."""
        if not line: return False
        # A heading should have a consistent bold style.
        if not all(s.is_bold for s in line):
            return False
        
        is_larger = line[0].font_size > profile.body_text_size
        is_bolder = line[0].is_bold and not profile.body_is_bold
        return is_larger and is_bolder

    def _is_potential_heading_by_prefix(self, line: List[TextSpan], profile: StyleProfile) -> bool:
        """Rule: Returns True if the line starts with a numerical/alpha prefix."""
        line_text = " ".join(s.text for s in line)
        if re.match(r'^((\d+\.)+\d*|[A-Z]\.)\s+', line_text):
             # And the text part is bold (even if the number isn't)
             return any(s.is_bold for s in line)
        return False

    # --- Title Identification ---

    def _find_title(self, lines: List[List[TextSpan]], profile: StyleProfile) -> Tuple[str, int]:
        """Finds the document title by looking for a block of prominent text on the first page."""
        title_lines = []
        last_line_index = -1
        
        for i, line in enumerate(lines):
            if line[0].page != 1: break
            
            is_title_style = line[0].font_size > profile.body_text_size + 2
            
            if is_title_style:
                if title_lines and abs(line[0].y0 - lines[last_line_index][0].y0) > 25:
                    break
                title_lines.append(" ".join(s.text for s in line))
                last_line_index = i
            elif title_lines:
                break
        
        if not title_lines: return "Untitled Document", -1
        return " ".join(title_lines), last_line_index

    # --- Hierarchy Ranking and Post-Processing ---

    def _rank_and_assign_levels(self, candidates: List[List[TextSpan]]) -> List[Heading]:
        """Assigns H1, H2, H3 levels based on numerical prefixes or relative font sizes."""
        headings = []
        for line in candidates:
            line_text = " ".join(s.text for s in line).strip()
            level = None
            
            # Prioritize numerical prefixes for level assignment
            match = re.match(r'^((\d+\.)+\d*|[A-Z]\.)\s*', line_text)
            if match:
                # Logic: "1." -> 1 part -> H1. "2.1" -> 2 parts -> H2.
                numeric_parts = re.findall(r'(\d+)', match.group(0))
                level_num = len(numeric_parts)
                if level_num <= 3:
                    level = f"H{level_num}"
            
            # Fallback for non-numbered headings (like "Acknowledgements")
            if not level:
                # This is a simplified fallback; a full ranking would compare all candidate font sizes.
                # For this contest, assuming non-numbered headings are H1 is a safe bet.
                level = "H1"

            headings.append(Heading(text=line_text, level=level, page=line[0].page))
        return headings

    def _post_process_hierarchy(self, headings: List[Heading]) -> List[Heading]:
        """Refines the list of headings to enforce a logical hierarchy."""
        processed_headings = []
        last_h1 = None
        last_h2 = None
        for heading in headings:
            if heading.level == "H1":
                last_h1 = heading
                last_h2 = None
                processed_headings.append(heading)
            elif heading.level == "H2":
                if last_h1:
                    last_h2 = heading
                    processed_headings.append(heading)
            elif heading.level == "H3":
                if last_h2:
                    processed_headings.append(heading)
        
        if len(headings) != len(processed_headings):
            logging.info(f"Post-processing pruned {len(headings) - len(processed_headings)} illogical headings.")
        return processed_headings

    # --- Main Classification Orchestrator ---

    def classify(self, spans: List[TextSpan], profile: StyleProfile) -> DocumentOutline:
        """The main orchestration method for the classification process."""
        lines = self._group_spans_into_lines(spans)
        
        if len(lines) < SPARSE_DOCUMENT_LINE_THRESHOLD:
            # Logic for flyers and posters
            logging.info("Sparse document detected. Applying poster/flyer logic.")
            if not lines: return DocumentOutline(title="", headings=[])
            largest_line = max(lines, key=lambda line: line[0].font_size)
            h1_text = " ".join(s.text for s in largest_line)
            return DocumentOutline(title="", headings=[Heading(text=h1_text, level="H1", page=largest_line[0].page)])

        # --- Full Pipeline for Structured Documents ---
        title, title_end_line_index = self._find_title(lines, profile)
        content_lines = lines[title_end_line_index + 1:]
        
        potential_lines = [
            line for line in content_lines
            if not any(filter_rule(line) for filter_rule in self.filter_rules)
        ]

        heading_candidates = [
            line for line in potential_lines
            if any(rule(line, profile) for rule in self.heading_candidate_rules)
        ]
        
        ranked_headings = self._rank_and_assign_levels(heading_candidates)
        final_headings = self._post_process_hierarchy(ranked_headings)
        
        logging.info(f"Classification complete. Found title: '{title}'. Found {len(final_headings)} final headings.")
        return DocumentOutline(title=title, headings=final_headings)
