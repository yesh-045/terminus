import asyncio
import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Input, Label, Static, Tree, OptionList
from textual.widgets.tree import TreeNode
from textual.events import Key
from textual.reactive import reactive

from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel as RichPanel
from rich.text import Text as RichText
from rich.table import Table as RichTable
from rich.syntax import Syntax as RichSyntax

from terminus.core.session import session
from terminus.infrastructure.models import model_manager
from terminus.infrastructure.persistence import persistence
from terminus.infrastructure.state_manager import state_manager
from terminus.core.agent import process_request
from terminus.core.commands import handle_command


class ModelSelectionModal(ModalScreen[str]):
    """Modal screen for selecting an AI model."""

    def __init__(self, models: List[Any], current_model: str):
        super().__init__()
        self.models = models
        self.current_model = current_model

    def compose(self) -> ComposeResult:
        options = []
        for m in self.models:
            selected = m.name == self.current_model
            prefix = "● " if selected else "○ "
            options.append(f"{prefix}{m.display_name} ({m.name})")

        yield Grid(
            Label("Select AI Model", id="modal_title"),
            OptionList(*options, id="model_list"),
            Button("Cancel", variant="error", id="btn_cancel"),
            id="modal_dialog"
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_index = event.option_index
        selected_model = self.models[selected_index].name
        self.dismiss(selected_model)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(self.current_model)


class ConfirmationModal(ModalScreen[str]):
    """Modal screen for tool execution confirmation."""

    def __init__(self, title: str, preview: Any, footer: Optional[str] = None):
        super().__init__()
        self.title_text = title
        self.preview_content = preview
        self.footer_text = footer

    def compose(self) -> ComposeResult:
        # Resolve the preview content as a renderable
        if isinstance(self.preview_content, str):
            preview_widget = Static(self.preview_content, id="confirm_preview_text")
        elif isinstance(self.preview_content, tuple):
            text_lines = []
            for item in self.preview_content:
                if item:
                    text_lines.append(str(item))
            preview_widget = Static("\n".join(text_lines), id="confirm_preview_text")
        else:
            # Wrap Rich renderables in a Static widget
            preview_widget = Static(self.preview_content, id="confirm_preview_rich")

        yield Grid(
            Label(f"[!] Action Required: {self.title_text}", id="confirm_title"),
            preview_widget,
            Label(self.footer_text or "", id="confirm_footer"),
            Horizontal(
                Button("Yes, run", variant="success", id="btn_yes"),
                Button("Always allow", variant="warning", id="btn_always"),
                Button("Cancel", variant="error", id="btn_cancel"),
                id="confirm_buttons"
            ),
            id="confirm_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_yes":
            self.dismiss("yes")
        elif event.button.id == "btn_always":
            self.dismiss("always")
        else:
            self.dismiss("no")


class MessageCard(Static):
    """A widget to represent a message card in the chat log."""

    def __init__(self, msg_type: str, content: Any):
        super().__init__(classes=f"msg_card msg_{msg_type}")
        self.msg_type = msg_type
        self.message_text = content

    def on_mount(self) -> None:
        self.update_content()

    def update_content(self) -> None:
        if self.msg_type == "info":
            self.update(RichText(f"• {self.message_text}", style="#ffb86c"))
        elif self.msg_type == "success":
            self.update(RichText(f"✓ {self.message_text}", style="green"))
        elif self.msg_type == "error":
            self.update(RichText(f"✗ {self.message_text}", style="red"))
        elif self.msg_type == "warning":
            self.update(RichText(f"⚠ {self.message_text}", style="yellow"))
        elif self.msg_type == "bullet":
            self.update(RichText(f"  - {self.message_text}", style="grey58"))
        elif self.msg_type == "muted":
            self.update(RichText(f"{self.message_text}", style="grey42"))
        elif self.msg_type == "thinking":
            self.update(RichText(f"› {self.message_text}", style="grey58"))
        elif self.msg_type == "agent":
            # Render Markdown beautifully with a clean assistant header
            self.update(RichMarkdown(f"### ❯ Terminus\n\n{self.message_text}"))
        elif self.msg_type == "user":
            self.update(RichText.from_markup(f"[bold white]❯ You[/]\n[white]{self.message_text}[/]"))
        elif self.msg_type == "plan":
            self.update(RichMarkdown(f"### ❯ Plan\n\n{self.message_text}"))
        elif self.msg_type == "tool_panel":
            content, title, footer = self.message_text
            # Format preview cleanly
            if isinstance(content, str):
                body = RichSyntax(content, "json", theme="nord")
            else:
                body = content
            self.update(RichPanel(body, title=title, subtitle=footer, border_style="#ffb86c"))
        elif self.msg_type == "error_panel":
            message, detail, title = self.message_text
            body = f"{message}\n\n{detail}" if detail else message
            self.update(RichPanel(body, title=title, border_style="red"))
        elif self.msg_type == "info_panel":
            content, title = self.message_text
            self.update(RichPanel(content, title=title, border_style="blue"))
        elif self.msg_type in ["panel", "confirmation_panel"]:
            # Wrap Rich renderables or strings directly
            self.update(self.message_text)
        else:
            self.update(str(self.message_text))


class ThinkingBlock(Static):
    """Collapsible dropdown showing reasoning steps + tool calls, like Claude/ChatGPT."""

    _counter: int = 0  # class-level counter for unique IDs

    def __init__(self):
        ThinkingBlock._counter += 1
        self._id = ThinkingBlock._counter
        super().__init__(classes="thinking_block")
        self._steps: list[str] = []

    def compose(self) -> ComposeResult:
        with Collapsible(
            title="Thinking...",
            collapsed=False,          # open while reasoning is live
            id=f"thinking_col_{self._id}",
        ):
            yield Static("", id=f"thinking_body_{self._id}", classes="thinking_body")

    def append_step(self, icon: str, text: str) -> None:
        """Add one step — called from the event loop via call_later."""
        self._steps.append(f"{icon}  {text}")
        self._flush()

    def finish(self) -> None:
        """Collapse and retitle once the agent returns its final answer."""
        try:
            c = self.query_one(f"#thinking_col_{self._id}", Collapsible)
            n = len(self._steps)
            c.title = f"Thoughts  ·  {n} step{'s' if n != 1 else ''}"
            c.collapsed = True
        except Exception:
            pass

    def _flush(self) -> None:
        try:
            body = self.query_one(f"#thinking_body_{self._id}", Static)
            body.update("\n".join(self._steps))
        except Exception:
            pass


class TerminusTUI(App):
    """Textual COSMOS-themed Terminal User Interface for Terminus."""

    CSS_PATH = "tui.tcss"

    # Tracking confirmation callback
    confirmation_future: Optional[asyncio.Future] = None
    is_agent_running = reactive(False)

    BANNER_TEXT = (
        "\n"
        " ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗\n"
        " ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝\n"
        "    ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗\n"
        "    ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║\n"
        "    ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║\n"
        "    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝\n"
        "\n"
        "                    Agentic Developer Terminal\n"
        "                 Type a command or ask a question.\n"
    )

    def __init__(self):
        super().__init__()
        self._thinking_block: Optional[ThinkingBlock] = None
        # Register this app in the UI module
        from terminus.ui import register_tui
        register_tui(self)

    def compose(self) -> ComposeResult:
        # Sidebar Container
        sidebar = Vertical(
            Label("● TERMINUS", id="sidebar_title"),
            Label("TAGS", classes="section_header"),
            Tree("Tags", id="tags_tree"),
            Horizontal(
                Label("CHATS", classes="section_header"),
                Button("+", id="btn_new_chat"),
                classes="chats_header_row"
            ),
            OptionList(id="chats_list"),
            Label("SYSTEM", classes="section_header"),
            Vertical(
                Label("CWD: ...", id="sys_cwd_lbl", classes="sys_info_lbl"),
                Label("Safety: ...", id="sys_yolo_lbl", classes="sys_info_lbl"),
                Label("CPU: --%", id="sys_cpu_lbl", classes="sys_info_lbl"),
                Label("RAM: --%", id="sys_ram_lbl", classes="sys_info_lbl"),
                Label("GPU: --%", id="sys_gpu_lbl", classes="sys_info_lbl"),
                id="sidebar_system_pane"
            ),
            Horizontal(
                Label(self.get_username(), id="username_lbl"),
                Button("logout", id="btn_logout"),
                id="sidebar_footer"
            ),
            id="sidebar_pane"
        )

        # Main Workspace Container
        main_workspace = Vertical(
            Horizontal(
                Button("≡", id="btn_toggle_sidebar"),
                Label(f"terminus - {os.path.basename(os.getcwd())}", id="header_title"),
                id="header_bar"
            ),
            Vertical(
                Static(self.BANNER_TEXT, id="retro_banner"),
                Vertical(id="chat_history"),
                id="chat_area"
            ),
            # Prompt input area
            Vertical(
                Input(placeholder="What is your request...", id="prompt_input"),
                Horizontal(
                    Label("+ 0 / 128k (0%)", id="token_counter"),
                    Label("", id="spinner_lbl"),
                    Button("Auto (Best Free)", id="model_selection_lbl"),
                    Button("▶", id="btn_send"),
                    id="input_status_bar"
                ),
                id="input_container"
            ),
            id="main_pane"
        )

        yield Horizontal(
            sidebar,
            main_workspace,
            id="app_layout"
        )

    def get_username(self) -> str:
        try:
            return os.getlogin()
        except:
            return os.environ.get("USERNAME", os.environ.get("USER", "sharannmanojkumar"))

    def on_mount(self) -> None:
        self.title = "Terminus"
        self.show_banner()
        self.refresh_sidebar_tags()
        self.refresh_sidebar_chats()
        self.update_model_label()
        self.update_system_info()
        self.set_interval(2.0, self.update_hardware_stats)

    def show_banner(self) -> None:
        """Clear message log and display the retro block TERMINUS banner."""
        chat_history = self.query_one("#chat_history")
        chat_history.remove_children()

        banner = self.query_one("#retro_banner")
        banner.remove_class("-hidden")

    def refresh_sidebar_tags(self) -> None:
        """Populate the tags tree with project tags."""
        tree = self.query_one("#tags_tree")
        tree.clear()
        
        # Add Root
        root = tree.root
        root.expand()

        # Add project tags
        tags = state_manager.get_all_tags()
        if tags:
            for tag in tags:
                root.add(f"#{tag}", allow_expand=False)
        else:
            root.add("(no tags)", allow_expand=False)

    def refresh_sidebar_chats(self) -> None:
        """Populate the chats OptionList with saved sessions."""
        list_view = self.query_one("#chats_list")
        list_view.clear_options()
        
        sessions = persistence.list_sessions()
        for session_data in sessions[:20]:
            name = session_data.get("session_name", "Unnamed")
            # Truncate long names
            display_name = name[:20] + "..." if len(name) > 23 else name
            list_view.add_option(display_name)

    def update_model_label(self) -> None:
        lbl = self.query_one("#model_selection_lbl")
        current = session.current_model
        
        # Map model name to a clean display badge
        if "gemini" in current:
            display = "Gemini Flash"
        elif "gpt-4" in current:
            display = "GPT-4o"
        elif "claude" in current:
            display = "Claude 3.5"
        elif "ollama" in current:
            display = f"Ollama ({current.split(':')[-1]})"
        else:
            display = current.split("/")[-1]
            
        lbl.label = f"Auto ({display})"

    def update_system_info(self) -> None:
        """Update system metrics in the sidebar pane."""
        try:
            cwd_lbl = self.query_one("#sys_cwd_lbl")
            cwd_lbl.update(f"CWD: {os.path.basename(os.getcwd())}")
        except:
            pass

        try:
            yolo_lbl = self.query_one("#sys_yolo_lbl")
            yolo_status = "ON (YOLO)" if not session.confirmation_enabled else "OFF (Safe)"
            yolo_lbl.update(f"Safety: {yolo_status}")
        except:
            pass

    async def update_hardware_stats(self) -> None:
        """Query CPU, RAM, and GPU stats and update the TUI labels."""
        try:
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.query_one("#sys_cpu_lbl").update(f"CPU: {cpu:.1f}%")
            self.query_one("#sys_ram_lbl").update(f"RAM: {ram:.1f}%")
        except Exception:
            pass

        try:
            gpu_val = await asyncio.to_thread(self._query_gpu)
            self.query_one("#sys_gpu_lbl").update(f"GPU: {gpu_val}")
        except Exception:
            try:
                self.query_one("#sys_gpu_lbl").update("GPU: N/A")
            except:
                pass

    def _query_gpu(self) -> str:
        try:
            import subprocess
            import shutil
            if shutil.which("nvidia-smi"):
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=1
                )
                if res.returncode == 0:
                    return f"{res.stdout.strip()}%"
        except:
            pass
        return "N/A"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "prompt_input":
            length = len(event.value)
            pct = int((length / 128000) * 100)
            counter = self.query_one("#token_counter")
            counter.update(f"+ {length} / 128k ({pct}%)")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt_input":
            self.submit_prompt()

    def on_key(self, event) -> None:
        """Escape cancels/unlocks a stuck agent request."""
        if event.key == "escape" and self.is_agent_running:
            self.is_agent_running = False
            self.stop_tui_spinner()
            self.update_system_info()
            self.add_message("warning", "Request cancelled. You can type a new prompt.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_send":
            self.submit_prompt()
        elif event.button.id == "btn_toggle_sidebar":
            sidebar = self.query_one("#sidebar_pane")
            sidebar.toggle_class("-hidden")
        elif event.button.id == "btn_new_chat":
            session.messages.clear()
            self.show_banner()
            self.add_message("success", "Started a new conversation session.")
        elif event.button.id == "btn_logout":
            self.exit()
        elif event.button.id == "model_selection_lbl":
            self.show_model_selection()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node
        label = str(node.label)
        if label.startswith("#"):
            # Switch to project tag
            tag_name = label[1:]
            project = state_manager.switch_to_tag(tag_name)
            if project:
                try:
                    os.chdir(project.working_directory)
                    session.change_directory(project.working_directory)
                    self.add_message("success", f"Switched to project: #{tag_name}")
                    self.query_one("#header_title").update(f"terminus - {os.path.basename(os.getcwd())}")
                    self.refresh_sidebar_tags()
                    self.update_system_info()
                except Exception as e:
                    self.add_message("warning", f"Switched to tag but couldn't change directory: {e}")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "chats_list":
            # Load selected session
            sessions = persistence.list_sessions()
            if event.option_index < len(sessions):
                sess_data = sessions[event.option_index]
                name = sess_data.get("session_name")
                if name:
                    try:
                        self.show_banner()
                        success = persistence.load_session(name)
                        if success:
                            self.add_message("success", f"Loaded conversation session: {name}")
                            # Populate loaded messages in chat log
                            for msg in session.messages:
                                if hasattr(msg, "parts"):
                                    for part in msg.parts:
                                        if hasattr(part, "content") and part.content.strip():
                                            role = "user" if "User" in part.__class__.__name__ else "agent"
                                            # Skip long system/guide prompts
                                            if len(part.content) < 800:
                                                self.add_message(role, part.content)
                            self.update_system_info()
                        else:
                            self.add_message("error", f"Failed to load session: {name}")
                    except Exception as e:
                        self.add_message("error", f"Failed to load session: {e}")

    def show_model_selection(self) -> None:
        """Display the modal model selection dialog."""
        async def do_switch():
            await model_manager.initialize()
            models = model_manager.list_models()
            current = session.current_model
            
            def handle_selection(new_model: Optional[str]):
                if new_model and new_model != current:
                    asyncio.create_task(self.switch_model(new_model))

            self.push_screen(ModelSelectionModal(models, current), handle_selection)
            
        asyncio.create_task(do_switch())

    async def switch_model(self, model_name: str) -> None:
        self.add_message("info", f"Switching model to: {model_name}...")
        success = await model_manager.switch_model(model_name)
        if success:
            self.update_model_label()
            self.add_message("success", f"Successfully switched to model: {session.current_model}")
        else:
            self.add_message("error", f"Failed to switch to model: {model_name}")

    def submit_prompt(self) -> None:
        input_widget = self.query_one("#prompt_input", Input)
        user_input = input_widget.value.strip()
        if not user_input:
            return

        # If agent is running, show feedback instead of silently ignoring
        if self.is_agent_running:
            self.add_message("warning", "… still processing previous request. Press Escape to cancel.")
            return

        input_widget.value = ""
        self.add_message("user", user_input)

        if user_input.lower() in ["exit", "quit"]:
            self.exit()
            return

        # Start background processing task
        self.is_agent_running = True
        self.start_tui_spinner("processing...")
        asyncio.create_task(self.execute_agent_request(user_input))

    async def execute_agent_request(self, user_input: str) -> None:
        # Open a fresh thinking block for this turn
        self.open_thinking_block()
        try:
            # Slash-commands don't need thinking block
            if await handle_command(user_input):
                return

            # Run agent with 90-second timeout
            try:
                resp = await asyncio.wait_for(
                    process_request(user_input),
                    timeout=90.0
                )
            except asyncio.TimeoutError:
                self.add_message("error", "Request timed out after 90 s. The model may be overloaded.")
                return

            if resp:
                await self.add_agent_message_stream(resp)

            # Auto-save
            try:
                persistence.auto_save()
                self.refresh_sidebar_chats()
            except Exception:
                pass

        except Exception as e:
            self.add_message("error", f"Execution error: {str(e)}")
        finally:
            self.close_thinking_block()   # collapse + retitle
            self.is_agent_running = False
            self.stop_tui_spinner()
            self.update_system_info()

    def add_message(self, msg_type: str, content: Any) -> None:
        """API called by routing hooks to append a message to the chat view."""
        # Hide the retro banner on first message
        banner = self.query_one("#retro_banner")
        if not banner.has_class("-hidden"):
            banner.add_class("-hidden")

        chat_history = self.query_one("#chat_history")
        chat_history.mount(MessageCard(msg_type, content))
        chat_history.scroll_end()

    async def add_agent_message_stream(self, content: str) -> None:
        """Stream an agent message into the TUI using a typewriter effect."""
        # Hide the retro banner on first message
        banner = self.query_one("#retro_banner")
        if not banner.has_class("-hidden"):
            banner.add_class("-hidden")

        chat_history = self.query_one("#chat_history")
        card = MessageCard("agent", "")
        chat_history.mount(card)
        chat_history.scroll_end()

        # Stream words smoothly
        words = content.split(" ")
        buffer = []
        for i, word in enumerate(words):
            buffer.append(word)
            if len(buffer) >= 2 or i == len(words) - 1:
                chunk = " ".join(buffer) + (" " if i < len(words) - 1 else "")
                card.message_text += chunk
                card.update(RichMarkdown(f"### ❯ Terminus\n\n{card.message_text}"))
                chat_history.scroll_end()
                buffer = []
                # Paced delay (30ms per word group)
                await asyncio.sleep(0.03)

    def open_thinking_block(self) -> None:
        """Mount a new ThinkingBlock into the chat for the upcoming agent turn."""
        try:
            chat_history = self.query_one("#chat_history")
            block = ThinkingBlock()
            chat_history.mount(block)
            chat_history.scroll_end()
            self._thinking_block = block
        except Exception:
            self._thinking_block = None

    def append_thinking_step(self, icon: str, text: str) -> None:
        """Append a step to the current thinking block (safe to call from any thread)."""
        if self._thinking_block:
            # call_from_thread-safe via Textual's call_later
            self.call_later(self._thinking_block.append_step, icon, text)

    def close_thinking_block(self) -> None:
        """Collapse and retitle the thinking block when the agent is done."""
        if self._thinking_block:
            self.call_later(self._thinking_block.finish)
            self._thinking_block = None

    def start_tui_spinner(self, message: str) -> None:
        lbl = self.query_one("#spinner_lbl")
        lbl.update(f"… {message}")

    def stop_tui_spinner(self) -> None:
        lbl = self.query_one("#spinner_lbl")
        lbl.update("")

    async def request_confirmation(self, title: str, preview: Any, footer: Optional[str] = None) -> str:
        """API called by core agent tool confirmation callback."""
        self.confirmation_future = asyncio.get_running_loop().create_future()
        
        def handle_modal_result(result: Optional[str]):
            if self.confirmation_future and not self.confirmation_future.done():
                self.confirmation_future.set_result(result or "no")

        self.push_screen(ConfirmationModal(title, preview, footer), handle_modal_result)
        
        # Await choice from future
        choice = await self.confirmation_future
        self.confirmation_future = None
        return choice


def run_tui():
    """TUI execution entry point."""
    app = TerminusTUI()
    app.run()
