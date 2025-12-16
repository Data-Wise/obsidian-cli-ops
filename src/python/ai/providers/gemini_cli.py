"""
Gemini CLI Provider - Uses @google/gemini-cli for AI operations.

Fallback when API is unavailable. Good for:
- Single note analysis
- One-off comparisons
- Interactive use

Limitations:
- No embeddings (use Gemini API or Ollama)
- Rate limited (60 RPM)
- Slower than API
"""

import subprocess
import shutil
from typing import List, Dict, Any, Optional

from .base import (
    AIProvider, ProviderType, ProviderCapabilities,
    AnalysisResult, ComparisonResult
)


class GeminiCLIProvider(AIProvider):
    """Gemini CLI provider - uses npx @google/gemini-cli."""

    name = "gemini-cli"
    provider_type = ProviderType.CLI
    capabilities = ProviderCapabilities(
        embeddings=False,  # CLI doesn't support embeddings
        analysis=True,
        comparison=True,
        batch=False,  # Too slow for batch
        streaming=True
    )

    def __init__(self, timeout: int = 60):
        """Initialize Gemini CLI provider.

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout
        self._cli_path = None

    def _get_cli_command(self) -> List[str]:
        """Get the CLI command to use."""
        # Check if gemini is installed globally
        if shutil.which("gemini"):
            return ["gemini"]
        # Fall back to npx
        if shutil.which("npx"):
            return ["npx", "@google/gemini-cli"]
        raise RuntimeError(
            "Gemini CLI not found. Install with: npm install -g @google/gemini-cli"
        )

    def _run_cli(self, prompt: str) -> str:
        """Run a prompt through the Gemini CLI.

        Args:
            prompt: The prompt to send

        Returns:
            CLI response text
        """
        cmd = self._get_cli_command()
        cmd.extend(["-p", prompt])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if result.returncode != 0:
                raise RuntimeError(f"Gemini CLI error: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Gemini CLI timed out after {self.timeout}s")
        except FileNotFoundError:
            raise RuntimeError("Gemini CLI not found")

    def is_available(self) -> bool:
        """Check if Gemini CLI is available."""
        try:
            cmd = self._get_cli_command()
            result = subprocess.run(
                cmd + ["--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        available = self.is_available()
        return {
            "name": self.name,
            "available": available,
            "cli_command": self._get_cli_command() if available else None,
            "timeout": self.timeout,
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch": self.capabilities.batch,
            }
        }

    def get_embedding(self, text: str) -> List[float]:
        """Not supported by CLI."""
        raise NotImplementedError(
            "Gemini CLI doesn't support embeddings. Use gemini-api or ollama."
        )

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Not supported by CLI."""
        raise NotImplementedError(
            "Gemini CLI doesn't support embeddings. Use gemini-api or ollama."
        )

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Gemini CLI."""
        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Extract and respond with ONLY valid JSON:
{{
    "topics": ["topic1", "topic2", "topic3"],
    "themes": ["theme1", "theme2"],
    "suggested_tags": ["tag1", "tag2"],
    "quality": {{"completeness": 7, "clarity": 8}},
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        response = self._run_cli(prompt)
        data = self._parse_json_response(
            response,
            {"topics": [], "themes": [], "suggested_tags": [], "quality": {}, "suggestions": []}
        )

        return AnalysisResult(
            topics=data.get("topics", []),
            themes=data.get("themes", []),
            suggested_tags=data.get("suggested_tags", []),
            quality=data.get("quality", {"completeness": 0, "clarity": 0}),
            suggestions=data.get("suggestions", []),
            raw_response=response
        )

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Gemini CLI."""
        prompt = f"""Compare these two Obsidian notes for similarity.

Note 1: {note1_title or "Untitled"}
---
{self._truncate(note1_content, 1000)}

Note 2: {note2_title or "Untitled"}
---
{self._truncate(note2_content, 1000)}

Analyze topic overlap, content similarity, and whether they should be merged.
Respond with ONLY valid JSON:
{{
    "similarity_score": 0.75,
    "reason": "Both notes discuss similar topics...",
    "should_merge": false,
    "merge_strategy": null
}}"""

        response = self._run_cli(prompt)
        data = self._parse_json_response(
            response,
            {"similarity_score": 0.0, "reason": "", "should_merge": False}
        )

        return ComparisonResult(
            similarity_score=float(data.get("similarity_score", 0.0)),
            reason=data.get("reason", ""),
            should_merge=data.get("should_merge", False),
            merge_strategy=data.get("merge_strategy")
        )
