import logging
import os
import tempfile
from typing import Any, Dict, Final, List, Tuple

import streamlit as st
from pydantic import ValidationError
from agents.config.settings import ConfigLoader, GitSettings
from agents.core.errors import ReadmeGeneratorError
from agents.core.pipeline import readme_agent
from agents.generators.enums import (
    BadgeStyles,
    CustomLogos,
    DefaultLogos,
    EmojiThemes,
    HeaderStyles,
    NavigationStyles,
)
from agents.models.enums import (
    AnthropicModels,
    GeminiModels,
    OllamaModels,
    OpenAIModels,
)

# --- Configuration & Constants ---

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application Metadata
APP_TITLE: Final[str] = "README-AI"
# DESCRIPTION = "" # Consider adding a description if needed

# Model Configuration
SUPPORTED_MODELS: Final[Dict[str, List[str]]] = {
    "OPENAI": [model.value for model in OpenAIModels],
    "ANTHROPIC": [model.value for model in AnthropicModels],
    "GEMINI": [model.value for model in GeminiModels],
    "OLLAMA": [model.value for model in OllamaModels],
    "OFFLINE": ["offline-mode"],
}
PROVIDER_ENV_VARS: Final[Dict[str, str]] = {
    "OPENAI": "OPENAI_API_KEY",
    "ANTHROPIC": "ANTHROPIC_API_KEY",
    "GEMINI": "GOOGLE_API_KEY",
}

# UI Styling Options
BADGE_STYLES: Final[List[str]] = [style.value for style in BadgeStyles]
LOGO_OPTIONS: Final[List[str]] = (
    [logo.name for logo in DefaultLogos] + [logo.value for logo in CustomLogos]
)
HEADER_STYLES: Final[List[str]] = [style.value for style in HeaderStyles]
TOC_STYLES: Final[List[str]] = [style.value for style in NavigationStyles]
ALIGNMENT_OPTIONS: Final[List[str]] = ["center", "left", "right"]

# Session State Keys
README_GENERATED_KEY: Final[str] = "readme_generated"
README_CONTENT_KEY: Final[str] = "readme_content"
SELECTED_PROVIDER_KEY: Final[str] = "selected_provider"
# SELECTED_MODEL_KEY: Final[str] = "selected_model" # Not strictly needed if using st.selectbox key

# --- Streamlit Application Class ---

class CogitoAIApp:
    """
    Streamlit web app serving the readme-ai CLI.
    """

    def __init__(self):
        self._setup_page_config()
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if README_GENERATED_KEY not in st.session_state:
            st.session_state[README_GENERATED_KEY] = False
        if README_CONTENT_KEY not in st.session_state:
            st.session_state[README_CONTENT_KEY] = ""
        if SELECTED_PROVIDER_KEY not in st.session_state:
            st.session_state[SELECTED_PROVIDER_KEY] = "OPENAI"
        # The selected model is implicitly stored by the key in st.selectbox

    def _setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=APP_TITLE,
            # page_icon="📚", # Consider adding an icon
            layout="wide",
            initial_sidebar_state="expanded",

        )

    def _render_header(self) -> None:
        """Render application header."""
        # Use columns for potentially better control, though one column works too
        col1, _ = st.columns([0.99, 0.01])
        with col1:
            raw_image_url = "https://raw.githubusercontent.com/ZahrizhalAli/tldwrite/main/assets/stretch_logo.png"

            st.html(f"<img src={raw_image_url} style='width:100%'>")


    def _render_sidebar(self) -> Tuple[str | None, str | None, Dict[str, str | None]]:
        """Render sidebar with configuration options. Returns repo_path, api_key, model_config."""
        with st.sidebar:
            st.title("Configuration")

            st.subheader("Repository Settings")
            repo_path = st.text_input(
                "Repository URL/Path",
                placeholder="https://github.com/user/repo or /path/to/local/repo",
                help="Enter a GitHub repository URL or local path. Leave blank to use default.",
            ) or "https://github.com/ZahrizhalAli/tldwrite" # Default if blank

            st.subheader("LLM Provider")
            # Use on_change to potentially reset model if provider changes? (Optional complexity)
            selected_provider = st.radio(
                "Select Provider",
                options=list(SUPPORTED_MODELS.keys()),
                horizontal=True,
                key=SELECTED_PROVIDER_KEY, # Use defined key
            )

            api_key_env_var = PROVIDER_ENV_VARS.get(selected_provider)
            api_key_needed = api_key_env_var and selected_provider not in ["OLLAMA", "OFFLINE"]
            api_key_placeholder = f"Your {selected_provider} API Key ({api_key_env_var})" if api_key_needed else "API Key (Not Required)"

            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder=api_key_placeholder,
                help=f"Needed for {selected_provider} models. Reads {api_key_env_var} env var if set.",
                disabled=not api_key_needed,
            )

            # Ensure model selection updates if provider changes
            available_models = SUPPORTED_MODELS[selected_provider]
            # Try to keep the previous model if it exists in the new list, else default to first
            current_model_index = 0
            if 'model_selection' in st.session_state and st.session_state.model_selection in available_models:
                 current_model_index = available_models.index(st.session_state.model_selection)

            model = st.selectbox(
                "Model",
                options=available_models,
                index=current_model_index,
                key="model_selection", # Unique key for the widget state
                disabled=selected_provider == "OFFLINE",
            )

            model_config = {
                "provider": selected_provider.lower(),
                "model": model if selected_provider != "OFFLINE" else None, # Handle offline case
            }

            return repo_path, api_key, model_config

    def _render_main_options(self) -> Dict[str, Any]:
        """Render main configuration options."""
        st.subheader("Customization Options")
        st.markdown("Customize the README output with the following options:")

        col1, col2, col3 = st.columns(3)
        with col1:
            header_style = st.selectbox(
                "Header Style", HEADER_STYLES, index=HEADER_STYLES.index("classic")
            )
            badge_style = st.selectbox(
                "Badge Style", BADGE_STYLES, index=BADGE_STYLES.index("flat-square")
            )
            logo_choice = st.selectbox(
                "Project Logo",
                LOGO_OPTIONS,
                index=LOGO_OPTIONS.index("PURPLE")
                if "PURPLE" in LOGO_OPTIONS
                else 0,
            )
        with col2:
            toc_style = st.selectbox(
                "Table of Contents Style",
                TOC_STYLES,
                index=TOC_STYLES.index("bullet"),
            )
            align = st.selectbox("Content Alignment", ALIGNMENT_OPTIONS, index=ALIGNMENT_OPTIONS.index("center"))
            # Providing default badge color, consider making it optional?
            badge_color_hex = st.color_picker("Badge Color", "#0080ff")
            # Remove '#' for the CLI argument
            badge_color = badge_color_hex.lstrip("#")
        with col3:
            # Reasonable defaults and ranges
            context_window = st.number_input(
                "Context Window", min_value=1, max_value=4096, value=3900
            )
            temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.1, step=0.05)
            tree_max_depth = st.slider(
                "Directory Tree Depth", min_value=1, max_value=5, value=2
            )

        custom_logo_path = ""
        if logo_choice == CustomLogos.CUSTOM.value:
            custom_logo_path = st.text_input(
                "Custom Logo URL/Path",
                placeholder="https://example.com/logo.svg or /path/to/logo.svg",
                help="Used only when Project Logo is set to CUSTOM.",
            )

        emojis_enabled = st.checkbox("Enable Emojis", value=True)
        emoji_theme = (
            EmojiThemes.MINIMAL.value if emojis_enabled else EmojiThemes.DEFAULT.value
        )

        return {
            "badge_style": badge_style,
            "header_style": header_style,
            "logo_choice": logo_choice,
            "custom_logo_path": custom_logo_path,
            "navigation_style": toc_style,
            "align": align,
            "badge_color": badge_color,
            "tree_max_depth": tree_max_depth,
            "context_window": context_window,
            "temperature": temperature,
            "emojis": emoji_theme,
        }

    def _render_output_section(self) -> None:
        """Render README output section if content exists."""
        if st.session_state.get(README_GENERATED_KEY, False):
            st.subheader("Generated README")
            preview_tab, markdown_tab, download_tab = st.tabs(["Preview", "Markdown", "Download"])

            readme_content = st.session_state.get(README_CONTENT_KEY, "")

            with preview_tab:
                st.markdown(readme_content, unsafe_allow_html=True)

            with markdown_tab:
                st.code(readme_content, language="markdown")

            with download_tab:
                st.download_button(
                    label="Download README.md",
                    data=readme_content,
                    file_name="README_ai.md", # Slightly different name to avoid overwrite
                    mime="text/markdown",
                    use_container_width=True,
                )

    @staticmethod
    def _resolve_logo(logo_choice: str, custom_logo_path: str) -> str:
        """Resolve a logo selection to an actual file path or URL."""
        if logo_choice == CustomLogos.CUSTOM.value:
            return custom_logo_path.strip()
        if logo_choice == CustomLogos.LLM.value:
            return CustomLogos.LLM.value
        if logo_choice in DefaultLogos.__members__:
            return DefaultLogos[logo_choice].value
        return DefaultLogos.PURPLE.value

    @staticmethod
    def _build_config(
        repo_path: str, config: Dict[str, str | None], options: Dict[str, Any]
    ) -> ConfigLoader:
        """Build a readme-ai ConfigLoader based on UI settings."""
        config_loader = ConfigLoader()

        config_loader.config.git = GitSettings(repository=repo_path)

        llm_updates: Dict[str, Any] = {
            "api": config["provider"],
            "context_window": options["context_window"],
            "temperature": options["temperature"],
        }
        if config.get("model"):
            llm_updates["model"] = config["model"]

        config_loader.config.llm = config_loader.config.llm.model_copy(
            update=llm_updates
        )

        resolved_logo = CogitoAIApp._resolve_logo(
            options["logo_choice"], options["custom_logo_path"]
        )
        config_loader.config.md = config_loader.config.md.model_copy(
            update={
                "align": options["align"],
                "badge_color": options["badge_color"],
                "badge_style": options["badge_style"],
                "emojis": options["emojis"],
                "header_style": options["header_style"],
                "logo": resolved_logo,
                "navigation_style": options["navigation_style"],
                "tree_max_depth": options["tree_max_depth"],
            }
        )

        return config_loader

    def _generate_readme(
        self,
        repo_path: str,
        api_key: str | None,
        config: Dict[str, str | None],
        options: Dict[str, Any],
    ) -> None:
        """Generate README using provided configuration."""
        # Reset state before generation
        st.session_state[README_GENERATED_KEY] = False
        st.session_state[README_CONTENT_KEY] = "Generating..."

        try:
            if (
                options["logo_choice"] == CustomLogos.CUSTOM.value
                and not options["custom_logo_path"].strip()
            ):
                st.warning("Please provide a custom logo URL or path.")
                st.session_state[README_CONTENT_KEY] = "Custom logo required."
                return

            # Use a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_file:
                output_path = tmp_file.name

            logger.info(f"Generating README for repository: {repo_path}")
            logger.info(f"Using model config: {config}")
            logger.info(f"Using options: {options}")
            logger.info(f"Outputting to temporary file: {output_path}")

            api_key_env_var = PROVIDER_ENV_VARS.get(config["provider"].upper())
            if api_key and api_key_env_var:
                os.environ[api_key_env_var] = api_key
                logger.info(f"Using provided API key for {config['provider'].upper()}.")
            elif api_key_env_var and api_key_env_var not in os.environ:
                logger.warning(
                    "API key for %s not found in input or environment variable %s.",
                    config["provider"].upper(),
                    api_key_env_var,
                )
                st.warning(
                    f"API key for {config['provider'].upper()} not provided. "
                    f"Check environment variable `{api_key_env_var}` or input field."
                )

            config_loader = self._build_config(repo_path, config, options)

            # Execute the agent synchronously
            with st.spinner("Generating README... Please wait."):
                readme_agent(config=config_loader, output_file=output_path)

            # Read the generated content if successful
            if os.path.exists(output_path):
                 with open(output_path, "r") as f:
                     st.session_state[README_CONTENT_KEY] = f.read()
                 st.session_state[README_GENERATED_KEY] = True
                 logger.info(f"README generated successfully: {output_path}")
                 st.success("README generated successfully!")
            else:
                 # Should be caught by CalledProcessError, but as a safeguard:
                 st.error("README generation finished, but output file was not found.")
                 logger.error(f"Output file {output_path} not found after command execution.")
                 st.session_state[README_CONTENT_KEY] = "Error: Output file not found."

        except ReadmeGeneratorError as e:
             st.error(f"README generation failed. {e}")
             logger.error(f"readme_agent failed: {e}")
             st.session_state[README_CONTENT_KEY] = "Error during generation. Check logs."
        except ValidationError as e:
             st.error(f"Configuration Error: {e}")
             logger.error(f"Pydantic validation error: {e}")
             st.session_state[README_CONTENT_KEY] = f"Error: Invalid configuration - {e}"
        except Exception as e:
             st.error(f"An unexpected error occurred during README generation: {e!s}")
             logger.exception("Unexpected error in _generate_readme.")
             st.session_state[README_CONTENT_KEY] = f"Error: {e!s}"
        finally:
             # Clean up the temporary file if it still exists
             if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"Removed temporary file: {output_path}")
                except OSError as e:
                    logger.warning(f"Could not remove temporary file {output_path}: {e}")
             # Ensure rerun happens to update the UI correctly based on state
             st.rerun()


    def run(self) -> None:
        """Run the main Streamlit application flow."""
        self._render_header()


        repo_path, api_key, model_config = self._render_sidebar()
        options = self._render_main_options()

        # Place buttons side-by-side
        col1, col2, _ = st.columns([1, 1, 3]) # Adjust ratio as needed
        with col1:
            generate_clicked = st.button("✨ Generate README", type="primary", use_container_width=True)
        with col2:
            reset_clicked = st.button("Reset Options", use_container_width=True)

        if generate_clicked:
            if not repo_path:
                st.warning("Please enter a repository URL or path.")
            else:
                 # Call the synchronous generation function directly
                 self._generate_readme(repo_path, api_key, model_config, options)

        if reset_clicked:
            # Clear specific relevant keys, keep others like provider/model potentially
            st.session_state[README_GENERATED_KEY] = False
            st.session_state[README_CONTENT_KEY] = ""
            # Optionally reset other options by clearing their specific keys if needed
            # e.g., del st.session_state.model_selection
            logger.info("Reset button clicked. Clearing output state.")
            st.rerun()

        # Always render the output section based on the current state
        self._render_output_section()


# --- Main Execution ---

if __name__ == "__main__":
    app = CogitoAIApp()
    app.run()
