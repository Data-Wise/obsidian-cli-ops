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
from typing import List, Dict, Any, Optional

from .base import (
    AIProvider, ProviderType, ProviderCapabilities,
    AnalysisResult, ComparisonResult
)


class ClaudeCLIProvider(AIProvider):
    """Claude CLI provider - uses claude command."""

    name = "claude-cli"
    provider_type = ProviderType.CLI
    capabilities = ProviderCapabilities(
        embeddings=False,  # Claude doesn't provide embeddings
        analysis=True,
        comparison=True,
        batch=False,  # CLI is single-request
        streaming=True
    )

    def __init__(self, timeout: int = 120):
        """Initialize Claude CLI provider.

        Args:
            timeout: Command timeout in seconds (Claude can be slow)
        """
        self.timeout = timeout

    def _get_cli_command(self) -> str:
        """Get the CLI command path."""
        # Check common locations
        if shutil.which("claude"):
            return "claude"
        # Check npm global
        if shutil.which("npx"):
            return "npx"
        raise RuntimeError(
            "Claude CLI not found. Install Claude Code from: "
            "https://claude.ai/code"
        )

    def _run_cli(self, prompt: str) -> str:
        """Run a prompt through Claude CLI.

        Args:
            prompt: The prompt to send

        Returns:
            CLI response text
        """
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
        available = self.is_available()
        return {
            "name": self.name,
            "available": available,
            "timeout": self.timeout,
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch": self.capabilities.batch,
            }
        }

    def get_embedding(self, text: str) -> List[float]:
        """Not supported - Claude doesn't provide embeddings."""
        raise NotImplementedError(
            "Claude doesn't support embeddings. Use gemini-api or ollama."
        )

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Not supported - Claude doesn't provide embeddings."""
        raise NotImplementedError(
            "Claude doesn't support embeddings. Use gemini-api or ollama."
        )

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Claude CLI."""
        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Extract and respond with ONLY valid JSON (no markdown, no explanation):
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
        """Compare two notes using Claude CLI."""
        prompt = f"""Compare these two Obsidian notes for similarity.

Note 1: {note1_title or "Untitled"}
---
{self._truncate(note1_content, 1000)}

Note 2: {note2_title or "Untitled"}
---
{self._truncate(note2_content, 1000)}

Analyze:
1. Topic overlap
2. Content similarity
3. Whether they should be merged

Respond with ONLY valid JSON (no markdown, no explanation):
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
