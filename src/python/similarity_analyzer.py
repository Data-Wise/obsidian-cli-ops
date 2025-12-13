#!/usr/bin/env python3
"""
Similarity Analyzer for Obsidian CLI Ops v2.0 - Phase 2

Finds similar notes, detects duplicates, and suggests merges
using AI-powered analysis.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

from db_manager import DatabaseManager
from ai_client import ClaudeClient, GeminiClient, SimilarityScore


@dataclass
class SimilarNotePair:
    """Pair of similar notes."""
    note1_id: str
    note2_id: str
    note1_title: str
    note2_title: str
    similarity_score: float
    reason: str
    should_merge: bool = False
    merge_strategy: Optional[str] = None


class SimilarityAnalyzer:
    """Analyzes note similarity using AI."""

    def __init__(self, db: DatabaseManager,
                 use_claude: bool = True,
                 use_gemini: bool = True):
        """
        Initialize similarity analyzer.

        Args:
            db: Database manager instance
            use_claude: Use Claude for reasoning (default: True)
            use_gemini: Use Gemini for embeddings (default: True)
        """
        self.db = db
        self.use_claude = use_claude
        self.use_gemini = use_gemini

        # Initialize clients
        self.claude = None
        self.gemini = None

        if use_claude:
            try:
                self.claude = ClaudeClient()
            except (ImportError, ValueError) as e:
                print(f"⚠️  Claude not available: {e}")
                self.use_claude = False

        if use_gemini:
            try:
                self.gemini = GeminiClient()
            except (ImportError, ValueError) as e:
                print(f"⚠️  Gemini not available: {e}")
                self.use_gemini = False

        if not self.use_claude and not self.use_gemini:
            raise ValueError("At least one AI provider (Claude or Gemini) must be available")

    def find_similar_notes(self, vault_id: str,
                          threshold: float = 0.7,
                          max_pairs: int = 20,
                          verbose: bool = False) -> List[SimilarNotePair]:
        """
        Find similar note pairs in a vault.

        Args:
            vault_id: Vault to analyze
            threshold: Minimum similarity score (0-1)
            max_pairs: Maximum pairs to return
            verbose: Print progress

        Returns:
            List of similar note pairs
        """
        if verbose:
            print(f"🔍 Finding similar notes (threshold: {threshold})...")

        # Get all notes
        notes = self.db.list_notes(vault_id)

        if verbose:
            print(f"   Analyzing {len(notes)} notes...")

        # Compare pairs
        similar_pairs = []
        total_comparisons = (len(notes) * (len(notes) - 1)) // 2
        comparisons_done = 0

        for i, note1 in enumerate(notes):
            for note2 in notes[i + 1:]:
                comparisons_done += 1

                if verbose and comparisons_done % 10 == 0:
                    progress = (comparisons_done / total_comparisons) * 100
                    print(f"   Progress: {progress:.1f}% ({comparisons_done}/{total_comparisons})")

                # Compare notes
                similarity = self._compare_notes(note1, note2)

                if similarity.score >= threshold:
                    # Parse merge info from reason
                    should_merge = "Merge:" in similarity.reason
                    merge_strategy = None
                    if should_merge:
                        parts = similarity.reason.split("| Merge:")
                        similarity.reason = parts[0].strip()
                        merge_strategy = parts[1].strip() if len(parts) > 1 else None

                    similar_pairs.append(SimilarNotePair(
                        note1_id=note1['id'],
                        note2_id=note2['id'],
                        note1_title=note1['title'],
                        note2_title=note2['title'],
                        similarity_score=similarity.score,
                        reason=similarity.reason,
                        should_merge=should_merge,
                        merge_strategy=merge_strategy
                    ))

                # Stop if we have enough pairs
                if len(similar_pairs) >= max_pairs:
                    if verbose:
                        print(f"   Reached max_pairs limit ({max_pairs})")
                    break

            if len(similar_pairs) >= max_pairs:
                break

        # Sort by similarity score
        similar_pairs.sort(key=lambda x: x.similarity_score, reverse=True)

        if verbose:
            print(f"   Found {len(similar_pairs)} similar pairs")

        return similar_pairs

    def _compare_notes(self, note1: Dict, note2: Dict) -> SimilarityScore:
        """
        Compare two notes using available AI providers.

        Uses Claude for reasoning, Gemini for embeddings.
        If both available, uses average of scores.

        Args:
            note1: First note
            note2: Second note

        Returns:
            Similarity score
        """
        scores = []

        # Try Claude first (better reasoning)
        if self.use_claude and self.claude:
            try:
                score = self.claude.compare_notes(
                    note1['content'] if 'content' in note1 else "",
                    note2['content'] if 'content' in note2 else "",
                    note1['title'],
                    note2['title']
                )
                scores.append(score)
            except Exception as e:
                print(f"⚠️  Claude comparison failed: {e}")

        # Try Gemini (faster embeddings)
        if self.use_gemini and self.gemini:
            try:
                # For Gemini, we need the actual content
                # Since we don't store content in database, read from file
                # For now, use metadata/title
                title1 = note1.get('title', '')
                title2 = note2.get('title', '')

                score = self.gemini.compare_notes(title1, title2)
                scores.append(score)
            except Exception as e:
                print(f"⚠️  Gemini comparison failed: {e}")

        # Return average score
        if scores:
            avg_score = sum(s.score for s in scores) / len(scores)
            combined_reason = " | ".join(set(s.reason for s in scores if s.reason))
            return SimilarityScore(
                note_id_1=note1['id'],
                note_id_2=note2['id'],
                score=avg_score,
                reason=combined_reason
            )
        else:
            return SimilarityScore(
                note_id_1=note1['id'],
                note_id_2=note2['id'],
                score=0.0,
                reason="No AI provider available"
            )

    def detect_duplicates(self, vault_id: str,
                         threshold: float = 0.9,
                         verbose: bool = False) -> List[SimilarNotePair]:
        """
        Detect likely duplicate notes.

        Args:
            vault_id: Vault to analyze
            threshold: Minimum similarity for duplicates (default: 0.9)
            verbose: Print progress

        Returns:
            List of likely duplicate pairs
        """
        if verbose:
            print(f"🔍 Detecting duplicates (threshold: {threshold})...")

        similar_pairs = self.find_similar_notes(
            vault_id,
            threshold=threshold,
            max_pairs=50,
            verbose=verbose
        )

        # Filter to only merge suggestions
        duplicates = [p for p in similar_pairs if p.should_merge or p.similarity_score >= 0.95]

        if verbose:
            print(f"   Found {len(duplicates)} likely duplicates")

        return duplicates

    def analyze_note_topics(self, vault_id: str,
                           verbose: bool = False) -> Dict:
        """
        Analyze topics across vault using Claude.

        Args:
            vault_id: Vault to analyze
            verbose: Print progress

        Returns:
            Topic analysis results
        """
        if not self.use_claude or not self.claude:
            raise ValueError("Claude is required for topic analysis")

        if verbose:
            print(f"📊 Analyzing vault topics...")

        notes = self.db.list_notes(vault_id)

        if verbose:
            print(f"   Analyzing {len(notes)} notes...")

        topics_map = {}
        for i, note in enumerate(notes):
            if verbose and (i + 1) % 10 == 0:
                print(f"   Progress: {i + 1}/{len(notes)}")

            try:
                # Analyze note (would need content, using title for now)
                analysis = self.claude.analyze_note(
                    content=note.get('title', ''),
                    title=note.get('title', '')
                )

                topics_map[note['id']] = analysis
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Error analyzing {note['title']}: {e}")
                topics_map[note['id']] = {
                    "topics": [],
                    "error": str(e)
                }

        if verbose:
            print(f"   ✓ Topic analysis complete")

        return topics_map

    def suggest_merges(self, vault_id: str,
                      threshold: float = 0.85,
                      max_suggestions: int = 10,
                      verbose: bool = False) -> List[Dict]:
        """
        Generate merge suggestions for similar notes.

        Args:
            vault_id: Vault to analyze
            threshold: Minimum similarity for merge (default: 0.85)
            max_suggestions: Maximum suggestions
            verbose: Print progress

        Returns:
            List of merge suggestions with details
        """
        if verbose:
            print(f"💡 Generating merge suggestions...")

        similar_pairs = self.find_similar_notes(
            vault_id,
            threshold=threshold,
            max_pairs=max_suggestions * 2,  # Get extra to filter
            verbose=verbose
        )

        # Create suggestions
        suggestions = []
        for pair in similar_pairs[:max_suggestions]:
            note1 = self.db.get_note(pair.note1_id)
            note2 = self.db.get_note(pair.note2_id)

            suggestions.append({
                "type": "MERGE",
                "confidence": pair.similarity_score,
                "note1": {
                    "id": pair.note1_id,
                    "title": pair.note1_title,
                    "path": note1['path'] if note1 else ""
                },
                "note2": {
                    "id": pair.note2_id,
                    "title": pair.note2_title,
                    "path": note2['path'] if note2 else ""
                },
                "reason": pair.reason,
                "strategy": pair.merge_strategy or "Combine content and update links"
            })

        if verbose:
            print(f"   Generated {len(suggestions)} merge suggestions")

        return suggestions


def main():
    """CLI interface for similarity analyzer."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python similarity_analyzer.py <command> <vault_id>")
        print("\nCommands:")
        print("  similar <vault_id>    - Find similar notes")
        print("  duplicates <vault_id> - Detect duplicates")
        print("  topics <vault_id>     - Analyze topics")
        print("  suggest <vault_id>    - Suggest merges")
        sys.exit(1)

    command = sys.argv[1]
    vault_id = sys.argv[2]

    # Initialize
    db = DatabaseManager()
    analyzer = SimilarityAnalyzer(db)

    try:
        if command == "similar":
            pairs = analyzer.find_similar_notes(vault_id, verbose=True)
            print(f"\n📊 Similar Notes:")
            for pair in pairs[:10]:
                print(f"\n  {pair.note1_title} ↔ {pair.note2_title}")
                print(f"  Similarity: {pair.similarity_score:.2f}")
                print(f"  Reason: {pair.reason}")

        elif command == "duplicates":
            duplicates = analyzer.detect_duplicates(vault_id, verbose=True)
            print(f"\n🔍 Likely Duplicates:")
            for dup in duplicates:
                print(f"\n  {dup.note1_title} ≈ {dup.note2_title}")
                print(f"  Similarity: {dup.similarity_score:.2f}")
                if dup.merge_strategy:
                    print(f"  Strategy: {dup.merge_strategy}")

        elif command == "topics":
            topics = analyzer.analyze_note_topics(vault_id, verbose=True)
            print(f"\n📊 Topics Found:")
            # Aggregate topics
            all_topics = {}
            for note_id, analysis in topics.items():
                for topic in analysis.get('topics', []):
                    all_topics[topic] = all_topics.get(topic, 0) + 1

            for topic, count in sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {topic}: {count} notes")

        elif command == "suggest":
            suggestions = analyzer.suggest_merges(vault_id, verbose=True)
            print(f"\n💡 Merge Suggestions:")
            for i, sug in enumerate(suggestions, 1):
                print(f"\n{i}. {sug['note1']['title']} + {sug['note2']['title']}")
                print(f"   Confidence: {sug['confidence']:.0%}")
                print(f"   Reason: {sug['reason']}")
                print(f"   Strategy: {sug['strategy']}")

        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
