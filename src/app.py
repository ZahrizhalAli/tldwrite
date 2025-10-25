import asyncio
import logging
import os
import subprocess
import tempfile

import streamlit as st

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


TITLE = "README-AI"
DESCRIPTION = ""

SUPPORTED_MODELS = {
    "OPENAI": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    "ANTHROPIC": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
    "GEMINI": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "OLLAMA": ["llama3", "mistral", "gemma"],
    "OFFLINE": ["offline-mode"],
}

BADGE_STYLES = [
    "default",
    "flat",
    "flat-square",
    "plastic",
    "for-the-badge",
    "skills",
    "skills-light",
    "social",
]

LOGO_OPTIONS = [
    "blue",
    "gradient",
    "black",
    "cloud",
    "purple",
    "grey",
    "custom",
    "llm",
]

HEADER_STYLES = ["classic", "modern", "compact", "ascii", "ascii_box", "svg"]

TOC_STYLES = ["bullet", "fold", "links", "number", "roman"]


class ReadmeAIApp:
    """
    Streamlit web app serving the readme-ai CLI.
    """

    def __init__(self):
        self.init_session_state()
        self.setup_page_config()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def init_session_state(self) -> None:
        if "readme_generated" not in st.session_state:
            st.session_state.readme_generated = False
        if "readme_content" not in st.session_state:
            st.session_state.readme_content = ""
        if "selected_provider" not in st.session_state:
            st.session_state.selected_provider = "OPENAI"
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "gpt-3.5-turbo"

    def setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="README-AI",
            # page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                "Get Help": "https://github.com/eli64s/readme-ai/discussions",
                "Report a bug": "https://github.com/eli64s/readme-ai/issues",
                "About": "https://eli64s.github.io/readme-ai/",
            },
        )

    def render_header(self) -> None:
        """Render application header."""
        col1, _ = st.columns([0.99, 0.01])
        with col1:
            (
                st.markdown(
                    """
                    <p align="left"><img src="https://raw.githubusercontent.com/eli64s/readme-ai/98f887af0de5fb2e40944a94e3d761b8be472312/docs/docs/assets/svg/readme-ai-logo-gradient.svg" alt="readme-ai-banner-logo" width="45%"></p>
                    <!--<p align="left"><em>Designed for simplicity, customization, and developer productivity.</em></p>-->
                    """,
                    unsafe_allow_html=True,
                )
            )
        # st.image(
        #     "assets/logo.svg",
        #     width=600,
        # )
        # st.markdown(DESCRIPTION)

    def render_sidebar(self) -> tuple[str, str, dict]:
        """Render sidebar with configuration options."""
        with st.sidebar:
            st.title("Configuration")
            st.subheader("Repository Settings")
            repo_path = st.text_input(
                "Repository URL/Path",
                value="https://github.com/eli64s/readme-ai",
                help="Enter a GitHub repository URL or local path",
            )

            st.subheader("LLM Provider")
            selected_provider = st.radio(
                "Select Provider",
                options=list(SUPPORTED_MODELS.keys()),
                horizontal=True,
            )
            st.session_state.selected_provider = selected_provider

            api_key = st.text_input("API Key", type="password")

            model = st.selectbox(
                "Model",
                options=SUPPORTED_MODELS[selected_provider],
                index=0,
                key="model_selection",
            )

            return (
                repo_path,
                api_key,
                self.get_model_config(selected_provider, model),
            )

    def render_main_options(self) -> dict:
        """Render main configuration options."""
        st.subheader("Customization Options")
        st.markdown("Customize the README output with the following options:")

        col1, col2, col3 = st.columns(3)
        with col1:
            header_style = st.selectbox("Header Style", HEADER_STYLES)
            badge_style = st.selectbox("Badge Style", BADGE_STYLES)
            image = st.selectbox("Project Logo", LOGO_OPTIONS)
        with col2:
            toc_style = st.selectbox("Table of Contents Style", TOC_STYLES)
            align = st.selectbox(
                "Content Alignment", ["center", "left", "right"]
            )
            badge_color = st.color_picker("Badge Color", "#0080ff")

        col1, col2, col3 = st.columns(3)
        with col1:
            context_window = st.number_input("Context Window", 1, 99999, 3900)
        with col2:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.1)
        with col3:
            tree_depth = st.slider("Directory Tree Depth", 1, 5, 2)

        emojis = st.checkbox("Enable Emojis")

        return {
            "badge_style": badge_style,
            "header_style": header_style,
            "image": image,
            "toc_style": toc_style,
            "align": align,
            "badge_color": badge_color,
            "tree_depth": tree_depth,
            "context_window": context_window,
            "temperature": temperature,
            "emojis": emojis,
        }

    def render_output_section(self) -> None:
        """Render README output section."""
        if st.session_state.readme_generated:
            tabs = st.tabs(["Preview", "Markdown", "Download"])

            with tabs[0]:
                st.markdown(
                    st.session_state.readme_content, unsafe_allow_html=True
                )

            with tabs[1]:
                st.code(st.session_state.readme_content, language="markdown")

            with tabs[2]:
                st.download_button(
                    "Download README.md",
                    st.session_state.readme_content,
                    file_name="README.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

    def get_model_config(self, provider: str, model: str) -> dict:
        """Get model configuration based on provider."""
        return {
            "provider": provider.lower(),
            "model": model,
        }

    def build_command(
        self, repo_path: str, output_path: str, config: dict, options: dict
    ) -> list[str]:
        """Build command for readme-ai CLI."""
        cmd = [
            "readmeai",
            "--repository",
            repo_path,
            "--output",
            output_path,
            "--api",
            config["provider"],
            "--model",
            config["model"],
        ]

        for key, value in options.items():
            if isinstance(value, bool):
                if value:
                    cmd.extend([f"--{key.replace('_', '-')}"])
            else:
                if key == "badge_color" and isinstance(value, str):
                    value = value.lstrip("#")  # Remove # from hex color
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        return cmd

    async def generate_readme(
        self, repo_path: str, api_key: str, config: dict, options: dict
    ) -> None:
        """Generate README using provided configuration."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".md", mode="w+", delete=False
            ) as tmp:
                command = self.build_command(
                    repo_path, tmp.name, config, options
                )
                await self.execute_command(command, api_key, tmp.name)

                with open(tmp.name) as f:
                    st.session_state.readme_content = f.read()
                    st.session_state.readme_generated = True

        except Exception as e:
            st.error(f"Error generating README: {e!s}")
            logger.error(f"README generation failed: {e!s}", exc_info=True)

    async def execute_command(
        self, command: list[str], api_key: str, output_path: str
    ) -> None:
        """Execute the command and handle its output."""
        with st.spinner("Generating README..."):
            env = os.environ.copy()
            if api_key:
                if st.session_state.selected_provider == "OPENAI":
                    env["OPENAI_API_KEY"] = api_key
                elif st.session_state.selected_provider == "ANTHROPIC":
                    env["ANTHROPIC_API_KEY"] = api_key
                elif st.session_state.selected_provider == "GEMINI":
                    env["GOOGLE_API_KEY"] = api_key

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            output_container = st.empty()
            stderr_accumulated = ""

            while True:
                try:
                    stderr_line = await process.stderr.readline()
                    if not stderr_line:
                        break

                    if line := stderr_line.decode().strip():
                        stderr_accumulated += line + "\n"
                        output_container.text_area(
                            "Generation Logs",
                            value=stderr_accumulated,
                            height=150,
                        )
                except Exception as e:
                    logger.error(f"Error reading process output: {e}")
                    break

            returncode = await process.wait()
            if returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode, command, stderr_accumulated
                )

    def run(self) -> None:
        """Run the Streamlit application."""
        self.render_header()

        repo_path, api_key, model_config = self.render_sidebar()
        options = self.render_main_options()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate README", use_container_width=True):
                self.loop.run_until_complete(
                    self.generate_readme(
                        repo_path, api_key, model_config, options
                    )
                )
        with col2:
            if st.button("Reset", use_container_width=True):
                st.session_state.readme_generated = False
                st.session_state.readme_content = ""
                st.rerun()

        self.render_output_section()

    def __del__(self):
        """Cleanup the event loop on deletion."""
        if hasattr(self, "loop") and self.loop is not None:
            try:
                self.loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")


if __name__ == "__main__":
    app = ReadmeAIApp()
    app.run()
