"""
Claude CLI Provider - Uses Claude Code CLI for AI operations.

Best for:
- High-quality analysis (Claude's reasoning)
- Complex comparisons
- When Gemini is unavailable

Limitations:
- No embeddings (use Gemini API or Ollama)
- Slower than API calls
- Requires Claude Code installed
"""

import subprocess
import shutil
from typing import List, Dict, Any

from .base import AIProvider, ProviderType, ProviderCapabilities
from ..models import AnalysisResult, ComparisonResult

# JSON schema templates for prompts
_ANALYSIS_SCHEMA = '''{
    "summary": "Brief summary of the note",
    "themes": ["theme1", "theme2"],
    "quality_score": 0.8,
    "suggestions": ["suggestion1", "suggestion2"],
    "connections": ["related topic 1", "related topic 2"]
}'''

_COMPARISON_SCHEMA = '''{
    "similarity_score": 0.75,
    "common_themes": ["shared theme 1"],
    "differences": ["key difference 1"],
    "relationship": "complementary notes on the same topic"
}'''


class ClaudeCLIProvider(AIProvider):
    """Claude CLI provider - uses claude command."""

    name = "claude-cli"
    provider_type = ProviderType.CLI
    capabilities = ProviderCapabilities(
        embeddings=False,
        batch_embeddings=False,
        analysis=True,
        comparison=True,
    )

    def __init__(self, timeout: int = 120, **kwargs):
        self.timeout = timeout

    def _get_cli_command(self) -> str:
        """Get the CLI command path."""
        if shutil.which("claude"):
            return "claude"
        if shutil.which("npx"):
            return "npx"
        raise RuntimeError(
            "Claude CLI not found. Install Claude Code from: "
            "https://claude.ai/code"
        )

    def _run_cli(self, prompt: str) -> str:
        """Run a prompt through Claude CLI."""
        cli = self._get_cli_command()

        if cli == "npx":
            cmd = ["npx", "@anthropic-ai/claude-code", "-p", prompt]
        else:
            cmd = ["claude", "-p", prompt]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude CLI timed out after {self.timeout}s")
        except FileNotFoundError:
            raise RuntimeError("Claude CLI not found")

    def is_available(self) -> bool:
        """Check if Claude CLI is available."""
        try:
            if shutil.which("claude"):
                result = subprocess.run(
                    ["claude", "--version"],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
            return False
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "name": self.name,
            "available": self.is_available(),
            "timeout": self.timeout,
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch_embeddings": self.capabilities.batch_embeddings,
            }
        }

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Claude CLI."""
        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Respond with ONLY valid JSON (no markdown, no explanation) matching this schema:
{_ANALYSIS_SCHEMA}"""

        response = self._run_cli(prompt)
        json_str = self._extract_json(response)
        return AnalysisResult.from_json(json_str)

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Claude CLI."""
        prompt = f"""Compare these two Obsidian notes for similarity.

Note 1: {note1_title or "Untitled"}
---
{self._truncate(note1_content, 1000)}

Note 2: {note2_title or "Untitled"}
---
{self._truncate(note2_content, 1000)}

Analyze topic overlap, content similarity, and their relationship.
Respond with ONLY valid JSON (no markdown, no explanation) matching this schema:
{_COMPARISON_SCHEMA}"""

        response = self._run_cli(prompt)
        json_str = self._extract_json(response)
        return ComparisonResult.from_json(json_str)
