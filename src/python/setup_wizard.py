#!/usr/bin/env python3
"""
AI Setup Wizard for Obsidian CLI Ops v2.0

Interactive setup wizard for configuring AI providers.
Provides two paths: Quick Start (recommended) and Custom Setup (advanced).
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Installing rich library for better UI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich import box


class SystemDetector:
    """Detects system capabilities and installed tools."""

    @staticmethod
    def detect() -> Dict:
        """
        Detect system information.

        Returns:
            Dict with system info (os, python_version, ram_gb, ollama_installed, etc.)
        """
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "ram_gb": SystemDetector._get_ram_gb(),
            "ollama_installed": SystemDetector._check_ollama(),
            "ollama_running": SystemDetector._check_ollama_running(),
            "sentence_transformers_installed": SystemDetector._check_package("sentence_transformers"),
            "requests_installed": SystemDetector._check_package("requests"),
            "numpy_installed": SystemDetector._check_package("numpy"),
        }
        return info

    @staticmethod
    def _get_ram_gb() -> int:
        """Get system RAM in GB."""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=5
                )
                bytes_ram = int(result.stdout.strip())
                return bytes_ram // (1024 ** 3)
            elif platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            return kb // (1024 ** 2)
            return 8  # Default assumption
        except:
            return 8

    @staticmethod
    def _check_ollama() -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(
                ["which", "ollama"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def _check_ollama_running() -> bool:
        """Check if Ollama server is running."""
        if not SystemDetector._check_package("requests"):
            return False

        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    def _check_package(package_name: str) -> bool:
        """Check if a Python package is installed."""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False


class AISetupWizard:
    """Interactive setup wizard for AI integration."""

    def __init__(self):
        """Initialize wizard."""
        self.console = Console()
        self.config_dir = Path.home() / ".config" / "obs"
        self.config_file = self.config_dir / "ai_config.json"
        self.system_info = None

    def run(self, mode: str = "interactive") -> bool:
        """
        Run the setup wizard.

        Args:
            mode: "interactive" (default) or "quick"

        Returns:
            True if setup successful
        """
        self._show_welcome()

        # Detect system
        with self.console.status("[bold green]Detecting your system..."):
            self.system_info = SystemDetector.detect()

        self._show_system_info()

        # Choose path
        if mode == "quick":
            return self.quick_start()
        else:
            choice = self._ask_path()
            if choice == "1":
                return self.quick_start()
            else:
                return self.custom_setup()

    def _show_welcome(self):
        """Show welcome message."""
        welcome = Panel(
            "[bold cyan]🚀 Obsidian CLI Ops - AI Setup Wizard[/bold cyan]\n\n"
            "This wizard will help you set up AI-powered features:\n"
            "  • Note similarity detection\n"
            "  • Duplicate finding\n"
            "  • Topic analysis\n"
            "  • Smart recommendations\n\n"
            "[dim]Choose between Quick Start (recommended) or Custom Setup[/dim]",
            box=box.DOUBLE,
            expand=False
        )
        self.console.print(welcome)
        self.console.print()

    def _show_system_info(self):
        """Show detected system information."""
        table = Table(title="🖥️  System Detection", box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Operating System", self.system_info["os"])
        table.add_row("Python Version", self.system_info["python_version"])
        table.add_row("RAM", f"{self.system_info['ram_gb']} GB")
        table.add_row("Ollama Installed", "✓ Yes" if self.system_info["ollama_installed"] else "✗ No")
        if self.system_info["ollama_installed"]:
            table.add_row("Ollama Running", "✓ Yes" if self.system_info["ollama_running"] else "✗ No")

        self.console.print(table)
        self.console.print()

    def _ask_path(self) -> str:
        """Ask user to choose setup path."""
        self.console.print(Panel(
            "[bold]Choose your path:[/bold]\n\n"
            "[green]1. Quick Start ⭐ RECOMMENDED[/green]\n"
            "   \"Just make it work!\"\n"
            "   ✓ Auto-detects best option\n"
            "   ✓ Installs for you\n"
            "   ⏱️  5 minutes\n\n"
            "[yellow]2. Custom Setup[/yellow]\n"
            "   \"I know what I'm doing\"\n"
            "   ✓ Choose provider and model\n"
            "   ✓ Fine-tune settings\n"
            "   ⏱️  10-15 minutes",
            box=box.ROUNDED,
            expand=False
        ))

        return Prompt.ask(
            "\n[bold]Your choice[/bold]",
            choices=["1", "2"],
            default="1"
        )

    def quick_start(self) -> bool:
        """Quick start setup - auto-detects and installs best option."""
        self.console.print("\n[bold green]🚀 Quick Start Mode[/bold green]\n")

        # Recommend provider based on system
        provider, reason = self._recommend_provider()

        self.console.print(Panel(
            f"[bold]Recommendation: {provider.upper()}[/bold]\n\n"
            f"{reason}\n\n"
            "[dim]This will work best for your system.[/dim]",
            box=box.ROUNDED,
            expand=False
        ))

        proceed = Confirm.ask("\n[bold]Proceed with this setup?[/bold]", default=True)
        if not proceed:
            self.console.print("[yellow]Setup cancelled. Run again to choose Custom Setup.[/yellow]")
            return False

        # Install and configure
        if provider == "huggingface":
            return self._setup_huggingface_quick()
        elif provider == "ollama":
            return self._setup_ollama_quick()
        else:
            self.console.print("[red]Unknown provider[/red]")
            return False

    def _recommend_provider(self) -> Tuple[str, str]:
        """
        Recommend best provider based on system.

        Returns:
            (provider_name, reason)
        """
        # If Ollama already running, recommend it
        if self.system_info["ollama_running"]:
            return ("ollama",
                    "✓ Ollama is already running on your system\n"
                    "✓ Fast local processing\n"
                    "✓ Zero cost, complete privacy")

        # If sentence-transformers already installed, recommend it
        if self.system_info["sentence_transformers_installed"]:
            return ("huggingface",
                    "✓ HuggingFace library is already installed\n"
                    "✓ Pure Python, works everywhere\n"
                    "✓ Free forever, 100% local")

        # Default to HuggingFace for most users
        return ("huggingface",
                "✓ Best for beginners\n"
                "✓ Pure Python, no external services\n"
                "✓ Free forever, 100% local\n"
                "✓ Balanced speed and quality")

    def _setup_huggingface_quick(self) -> bool:
        """Quick setup for HuggingFace."""
        self.console.print("\n[bold]Setting up HuggingFace (Local AI)[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            # Install sentence-transformers
            if not self.system_info["sentence_transformers_installed"]:
                task = progress.add_task("Installing sentence-transformers...", total=None)
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"],
                        check=True,
                        capture_output=True
                    )
                    progress.update(task, description="✓ Installed sentence-transformers")
                except subprocess.CalledProcessError as e:
                    progress.update(task, description="✗ Failed to install sentence-transformers")
                    self.console.print(f"[red]Error: {e}[/red]")
                    return False
            else:
                progress.add_task("✓ sentence-transformers already installed", total=1, completed=1)

            # Test installation
            task = progress.add_task("Testing HuggingFace client...", total=None)
            try:
                from ai_client import get_ai_client
                client = get_ai_client("huggingface", model_name="all-MiniLM-L6-v2")

                # Test embedding generation
                test_embedding = client.get_embedding("Test note for obsidian")

                progress.update(task, description=f"✓ HuggingFace client working ({len(test_embedding)} dimensions)")
            except Exception as e:
                progress.update(task, description="✗ HuggingFace client test failed")
                self.console.print(f"[red]Error: {e}[/red]")
                return False

            # Save configuration
            task = progress.add_task("Saving configuration...", total=None)
            config = {
                "version": "2.0.0",
                "setup_completed": True,
                "setup_date": subprocess.run(
                    ["date", "+%Y-%m-%d %H:%M:%S"],
                    capture_output=True, text=True
                ).stdout.strip(),
                "provider": {
                    "primary": "huggingface",
                    "config": {
                        "model_name": "all-MiniLM-L6-v2"
                    }
                },
                "system_info": self.system_info
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            progress.update(task, description=f"✓ Configuration saved to {self.config_file}")

        self.console.print("\n[bold green]✓ Setup Complete![/bold green]\n")
        self._show_next_steps("huggingface")
        return True

    def _setup_ollama_quick(self) -> bool:
        """Quick setup for Ollama."""
        self.console.print("\n[bold]Setting up Ollama (Local AI)[/bold]\n")

        # Check if Ollama is installed
        if not self.system_info["ollama_installed"]:
            self.console.print(Panel(
                "[yellow]⚠️  Ollama not found[/yellow]\n\n"
                "Please install Ollama first:\n\n"
                "[bold]Option 1: Homebrew (recommended)[/bold]\n"
                "  brew install ollama\n\n"
                "[bold]Option 2: Cask (GUI app)[/bold]\n"
                "  brew install --cask ollama-app\n\n"
                "[bold]Option 3: Official installer[/bold]\n"
                "  Visit: https://ollama.com/download\n\n"
                "After installing, run: [bold]ollama serve[/bold]\n"
                "Then run this setup wizard again.",
                box=box.ROUNDED
            ))
            return False

        # Check if Ollama is running
        if not self.system_info["ollama_running"]:
            self.console.print("[yellow]⚠️  Ollama is installed but not running[/yellow]")
            self.console.print("Starting Ollama server in background...")
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                import time
                time.sleep(3)  # Wait for server to start
                self.system_info["ollama_running"] = SystemDetector._check_ollama_running()
            except:
                pass

            if not self.system_info["ollama_running"]:
                self.console.print("[red]Failed to start Ollama. Please run 'ollama serve' manually.[/red]")
                return False

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            # Pull recommended model
            task = progress.add_task("Pulling qwen2.5:0.5b model (500MB, fast)...", total=None)
            try:
                subprocess.run(
                    ["ollama", "pull", "qwen2.5:0.5b"],
                    check=True,
                    capture_output=True
                )
                progress.update(task, description="✓ Model qwen2.5:0.5b ready")
            except subprocess.CalledProcessError:
                progress.update(task, description="✗ Failed to pull model")
                self.console.print("[red]Failed to download model[/red]")
                return False

            # Pull embedding model
            task = progress.add_task("Pulling nomic-embed-text model...", total=None)
            try:
                subprocess.run(
                    ["ollama", "pull", "nomic-embed-text"],
                    check=True,
                    capture_output=True
                )
                progress.update(task, description="✓ Embedding model ready")
            except subprocess.CalledProcessError:
                progress.update(task, description="✗ Failed to pull embedding model")
                return False

            # Test installation
            task = progress.add_task("Testing Ollama client...", total=None)
            try:
                from ai_client import get_ai_client
                client = get_ai_client("ollama",
                                      embedding_model="nomic-embed-text",
                                      chat_model="qwen2.5:0.5b")

                test_embedding = client.get_embedding("Test note")
                progress.update(task, description=f"✓ Ollama client working ({len(test_embedding)} dimensions)")
            except Exception as e:
                progress.update(task, description="✗ Ollama client test failed")
                self.console.print(f"[red]Error: {e}[/red]")
                return False

            # Save configuration
            task = progress.add_task("Saving configuration...", total=None)
            config = {
                "version": "2.0.0",
                "setup_completed": True,
                "setup_date": subprocess.run(
                    ["date", "+%Y-%m-%d %H:%M:%S"],
                    capture_output=True, text=True
                ).stdout.strip(),
                "provider": {
                    "primary": "ollama",
                    "config": {
                        "embedding_model": "nomic-embed-text",
                        "chat_model": "qwen2.5:0.5b"
                    }
                },
                "system_info": self.system_info
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            progress.update(task, description=f"✓ Configuration saved to {self.config_file}")

        self.console.print("\n[bold green]✓ Setup Complete![/bold green]\n")
        self._show_next_steps("ollama")
        return True

    def custom_setup(self) -> bool:
        """Custom setup - user chooses provider and model."""
        self.console.print("\n[bold yellow]🛠️  Custom Setup Mode[/bold yellow]\n")
        self.console.print("[dim]Choose your preferred AI provider and model[/dim]\n")

        # Show provider options
        provider = self._choose_provider()
        if not provider:
            return False

        # Provider-specific setup
        if provider == "huggingface":
            return self._setup_huggingface_custom()
        elif provider == "ollama":
            return self._setup_ollama_custom()
        else:
            self.console.print("[red]Unknown provider[/red]")
            return False

    def _choose_provider(self) -> Optional[str]:
        """Show provider selection menu."""
        table = Table(title="AI Provider Options", box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=5)
        table.add_column("Provider", style="bold")
        table.add_column("Details", style="dim")

        table.add_row(
            "1",
            "HuggingFace ⭐",
            "FREE forever • 100% local • Pure Python\n"
            "Speed: Medium • Quality: Good"
        )
        table.add_row(
            "2",
            "Ollama",
            "FREE forever • 100% local • Fast embeddings\n"
            "Requires: ollama install"
        )

        self.console.print(table)

        choice = Prompt.ask(
            "\n[bold]Choose provider[/bold]",
            choices=["1", "2", "q"],
            default="1"
        )

        if choice == "q":
            return None
        elif choice == "1":
            return "huggingface"
        elif choice == "2":
            return "ollama"

    def _setup_huggingface_custom(self) -> bool:
        """Custom setup for HuggingFace with model selection."""
        self.console.print("\n[bold]HuggingFace Model Selection[/bold]\n")

        # Show model options
        table = Table(title="Available Models", box=box.ROUNDED)
        table.add_column("Option", width=5)
        table.add_column("Model", style="bold")
        table.add_column("Details", style="dim")

        table.add_row(
            "1",
            "all-MiniLM-L6-v2",
            "Size: 80MB • Dimension: 384\n"
            "Speed: Fast • Best for: Testing"
        )
        table.add_row(
            "2",
            "all-mpnet-base-v2 ⭐",
            "Size: 420MB • Dimension: 768\n"
            "Speed: Medium • Best for: Production"
        )
        table.add_row(
            "3",
            "bge-large-en-v1.5",
            "Size: 1.3GB • Dimension: 1024\n"
            "Speed: Slow • Best for: Quality"
        )

        self.console.print(table)

        choice = Prompt.ask(
            "\n[bold]Choose model[/bold]",
            choices=["1", "2", "3"],
            default="2"
        )

        model_map = {
            "1": "all-MiniLM-L6-v2",
            "2": "all-mpnet-base-v2",
            "3": "bge-large-en-v1.5"
        }
        model_name = model_map[choice]

        # Install and test (similar to quick start but with chosen model)
        self.console.print(f"\n[bold]Installing {model_name}...[/bold]\n")

        # Rest is same as _setup_huggingface_quick but with chosen model
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            if not self.system_info["sentence_transformers_installed"]:
                task = progress.add_task("Installing sentence-transformers...", total=None)
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"],
                        check=True,
                        capture_output=True
                    )
                    progress.update(task, description="✓ Installed sentence-transformers")
                except subprocess.CalledProcessError as e:
                    progress.update(task, description="✗ Failed")
                    self.console.print(f"[red]Error: {e}[/red]")
                    return False

            task = progress.add_task(f"Loading {model_name}...", total=None)
            try:
                from ai_client import get_ai_client
                client = get_ai_client("huggingface", model_name=model_name)
                test_embedding = client.get_embedding("Test")
                progress.update(task, description=f"✓ Model loaded ({len(test_embedding)} dimensions)")
            except Exception as e:
                progress.update(task, description="✗ Failed")
                self.console.print(f"[red]Error: {e}[/red]")
                return False

            task = progress.add_task("Saving configuration...", total=None)
            config = {
                "version": "2.0.0",
                "setup_completed": True,
                "setup_date": subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"],
                                            capture_output=True, text=True).stdout.strip(),
                "provider": {
                    "primary": "huggingface",
                    "config": {"model_name": model_name}
                },
                "system_info": self.system_info
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            progress.update(task, description=f"✓ Saved to {self.config_file}")

        self.console.print("\n[bold green]✓ Setup Complete![/bold green]\n")
        self._show_next_steps("huggingface")
        return True

    def _setup_ollama_custom(self) -> bool:
        """Custom setup for Ollama with model selection."""
        # Similar to _setup_ollama_quick but with model choices
        self.console.print("\n[bold]Ollama Model Selection[/bold]\n")

        if not self.system_info["ollama_installed"]:
            self.console.print("[red]Ollama not installed. Please install first.[/red]")
            return False

        # Show model options
        table = Table(title="Available Models", box=box.ROUNDED)
        table.add_column("Option", width=5)
        table.add_column("Model", style="bold")
        table.add_column("Details", style="dim")

        table.add_row("1", "qwen2.5:0.5b ⭐", "Size: 500MB • Speed: Fast • Best for: Most users")
        table.add_row("2", "llama3.1", "Size: 4GB • Speed: Slow • Best for: Quality")
        table.add_row("3", "mistral", "Size: 4GB • Speed: Medium • Best for: Balance")

        self.console.print(table)

        choice = Prompt.ask("\n[bold]Choose model[/bold]", choices=["1", "2", "3"], default="1")

        model_map = {"1": "qwen2.5:0.5b", "2": "llama3.1", "3": "mistral"}
        chat_model = model_map[choice]

        # Setup with chosen model
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            task = progress.add_task(f"Pulling {chat_model}...", total=None)
            try:
                subprocess.run(["ollama", "pull", chat_model], check=True, capture_output=True)
                progress.update(task, description=f"✓ {chat_model} ready")
            except:
                progress.update(task, description="✗ Failed")
                return False

            task = progress.add_task("Pulling nomic-embed-text...", total=None)
            try:
                subprocess.run(["ollama", "pull", "nomic-embed-text"], check=True, capture_output=True)
                progress.update(task, description="✓ Embedding model ready")
            except:
                progress.update(task, description="✗ Failed")
                return False

            task = progress.add_task("Testing...", total=None)
            try:
                from ai_client import get_ai_client
                client = get_ai_client("ollama", embedding_model="nomic-embed-text", chat_model=chat_model)
                test_embedding = client.get_embedding("Test")
                progress.update(task, description=f"✓ Working ({len(test_embedding)} dimensions)")
            except Exception as e:
                progress.update(task, description="✗ Failed")
                self.console.print(f"[red]Error: {e}[/red]")
                return False

            config = {
                "version": "2.0.0",
                "setup_completed": True,
                "setup_date": subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"],
                                            capture_output=True, text=True).stdout.strip(),
                "provider": {
                    "primary": "ollama",
                    "config": {"embedding_model": "nomic-embed-text", "chat_model": chat_model}
                },
                "system_info": self.system_info
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

        self.console.print("\n[bold green]✓ Setup Complete![/bold green]\n")
        self._show_next_steps("ollama")
        return True

    def _show_next_steps(self, provider: str):
        """Show next steps after successful setup."""
        if provider == "huggingface":
            next_steps = (
                "[bold]Try these commands:[/bold]\n\n"
                "  # Test embeddings\n"
                "  obs ai test\n\n"
                "  # Find similar notes\n"
                "  obs ai similar <vault_id>\n\n"
                "  # Detect duplicates\n"
                "  obs ai duplicates <vault_id>\n\n"
                "[dim]Your setup uses HuggingFace (100% free, local, private)[/dim]"
            )
        else:  # ollama
            next_steps = (
                "[bold]Try these commands:[/bold]\n\n"
                "  # Test embeddings\n"
                "  obs ai test\n\n"
                "  # Find similar notes\n"
                "  obs ai similar <vault_id>\n\n"
                "  # Compare with reasoning\n"
                "  obs ai compare <note1> <note2> --reasoning\n\n"
                "[dim]Your setup uses Ollama (100% free, local, private)[/dim]"
            )

        self.console.print(Panel(next_steps, box=box.ROUNDED, title="🎉 Next Steps"))

    def show_config(self):
        """Show current configuration."""
        if not self.config_file.exists():
            self.console.print("[yellow]No configuration found. Run 'obs ai setup' first.[/yellow]")
            return

        with open(self.config_file) as f:
            config = json.load(f)

        table = Table(title="Current AI Configuration", box=box.ROUNDED)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Setup Completed", "✓ Yes" if config.get("setup_completed") else "✗ No")
        table.add_row("Setup Date", config.get("setup_date", "Unknown"))
        table.add_row("Provider", config.get("provider", {}).get("primary", "Unknown"))

        provider_config = config.get("provider", {}).get("config", {})
        for key, value in provider_config.items():
            table.add_row(f"  {key}", str(value))

        self.console.print(table)
        self.console.print(f"\n[dim]Config file: {self.config_file}[/dim]")


def main():
    """CLI interface for setup wizard."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Setup Wizard for Obsidian CLI Ops")
    parser.add_argument("--quick", action="store_true", help="Quick start mode")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    args = parser.parse_args()

    wizard = AISetupWizard()

    if args.show_config:
        wizard.show_config()
    elif args.quick:
        wizard.run(mode="quick")
    else:
        wizard.run(mode="interactive")


if __name__ == '__main__':
    main()
