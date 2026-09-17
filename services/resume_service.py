"""Resume extraction and AI parsing independent of Streamlit state."""

from dataclasses import dataclass
from typing import Dict, Optional

from rag import ResumeParser
from utils.pdf_extractor import ResumeExtractor


@dataclass(frozen=True)
class ResumeProcessingResult:
    """Result returned after extracting and optionally parsing a resume."""

    text: str
    parsed: Optional[Dict]
    parse_warning: Optional[str] = None

    @property
    def candidate_name(self) -> str:
        if not self.parsed:
            return ""
        return str(self.parsed.get("name") or "")


def process_resume(
    file_bytes: bytes,
    filename: str,
    api_key: str,
    *,
    previous_text: str = "",
    previous_parse: Optional[Dict] = None,
) -> ResumeProcessingResult:
    """Extract resume text and parse a new resume once.

    A successful parse is reused when the uploaded content matches the resume
    already stored in the current session.
    """
    text = ResumeExtractor.extract_text(file_bytes, filename)
    if not text:
        raise ValueError("Could not extract text from the uploaded resume.")

    if text == previous_text and previous_parse is not None:
        return ResumeProcessingResult(text=text, parsed=previous_parse)

    try:
        parsed = ResumeParser(api_key).parse_resume_sync(text)
    except Exception as exc:
        return ResumeProcessingResult(
            text=text,
            parsed=None,
            parse_warning=f"AI parsing failed: {exc}",
        )

    if parsed.get("error"):
        return ResumeProcessingResult(
            text=text,
            parsed=None,
            parse_warning="AI parsing did not return a usable resume profile.",
        )

    return ResumeProcessingResult(text=text, parsed=parsed)
