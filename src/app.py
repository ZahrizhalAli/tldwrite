import logging
import os
import subprocess
import tempfile
from typing import Final, Dict, List, Tuple, Any

import streamlit as st
from pydantic import ValidationError

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
    "OPENAI": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    "ANTHROPIC": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
    "GEMINI": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "OLLAMA": ["llama3", "mistral", "gemma"],
    "OFFLINE": ["offline-mode"],
}
PROVIDER_ENV_VARS: Final[Dict[str, str]] = {
    "OPENAI": "OPENAI_API_KEY",
    "ANTHROPIC": "ANTHROPIC_API_KEY",
    "GEMINI": "GOOGLE_API_KEY",
}

# UI Styling Options
BADGE_STYLES: Final[List[str]] = [
    "default", "flat", "flat-square", "plastic", "for-the-badge",
    "skills", "skills-light", "social",
]
LOGO_OPTIONS: Final[List[str]] = [
    "blue", "gradient", "black", "cloud", "purple", "grey",
    "custom", "llm",
]
HEADER_STYLES: Final[List[str]] = [
    "classic", "modern", "compact", "ascii", "ascii_box", "svg"
]
TOC_STYLES: Final[List[str]] = ["bullet", "fold", "links", "number", "roman"]
ALIGNMENT_OPTIONS: Final[List[str]] = ["center", "left", "right"]

# Session State Keys
README_GENERATED_KEY: Final[str] = "readme_generated"
README_CONTENT_KEY: Final[str] = "readme_content"
SELECTED_PROVIDER_KEY: Final[str] = "selected_provider"
# SELECTED_MODEL_KEY: Final[str] = "selected_model" # Not strictly needed if using st.selectbox key

# --- Streamlit Application Class ---

class ReadmeAIApp:
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

    raw_image_url = "https://raw.githubusercontent.com/ZahrizhalAli/tldwrite/36eb328a0542b25f3801dafc38ef17bb7920415e/assets/logo.png"
    def _render_header(self) -> None:
        """Render application header."""
        # Use columns for potentially better control, though one column works too
        col1, _ = st.columns([0.99, 0.01])
        with col1:
            # Consider hosting the image within the app or using a more permanent URL
            st.markdown(
                """
                <p align="left">
            <img src="{raw_image_url}" alt="TL;DWrite Banner Logo" width="45%">
        </p>
                <p align="left"><img src="https://github.com/ZahrizhalAli/tldwrite/blob/36eb328a0542b25f3801dafc38ef17bb7920415e/assets/logo.png" alt="readme-ai-banner-logo" width="45%"></p>
                """,
                unsafe_allow_html=True,
            )
            # if DESCRIPTION:
            #     st.markdown(f"*{DESCRIPTION}*")

    def _render_sidebar(self) -> Tuple[str | None, str | None, Dict[str, str]]:
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
                "model": model if selected_provider != "OFFLINE" else "", # Handle offline case
            }

            return repo_path, api_key, model_config

    def _render_main_options(self) -> Dict[str, Any]:
        """Render main configuration options."""
        st.subheader("Customization Options")
        st.markdown("Customize the README output with the following options:")

        col1, col2, col3 = st.columns(3)
        with col1:
            header_style = st.selectbox("Header Style", HEADER_STYLES, index=HEADER_STYLES.index("classic"))
            badge_style = st.selectbox("Badge Style", BADGE_STYLES, index=BADGE_STYLES.index("flat-square"))
            image = st.selectbox("Project Logo", LOGO_OPTIONS, index=LOGO_OPTIONS.index("gradient"))
        with col2:
            toc_style = st.selectbox("Table of Contents Style", TOC_STYLES, index=TOC_STYLES.index("bullet"))
            align = st.selectbox("Content Alignment", ALIGNMENT_OPTIONS, index=ALIGNMENT_OPTIONS.index("center"))
            # Providing default badge color, consider making it optional?
            badge_color_hex = st.color_picker("Badge Color", "#0080ff")
            # Remove '#' for the CLI argument
            badge_color = badge_color_hex.lstrip("#")
        with col3:
            # Reasonable defaults and ranges
            context_window = st.number_input("Context Window", min_value=1, max_value=99999, value=3900)
            temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.1, step=0.05)
            tree_depth = st.slider("Directory Tree Depth", min_value=1, max_value=5, value=2)

        emojis = st.checkbox("Enable Emojis", value=True) # Default to True

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
    def _build_command(
        repo_path: str, output_path: str, config: Dict[str, str], options: Dict[str, Any]
    ) -> List[str]:
        """Build the command list for the readme-ai CLI."""
        cmd = [
            "readmeai",
            "--repository", repo_path,
            "--output", output_path,
        ]

        # Add provider and model only if not offline
        if config["provider"] != "offline":
             cmd.extend(["--api", config["provider"]])
             # Only add model if provider requires it (not offline)
             if config["model"]:
                 cmd.extend(["--model", config["model"]])
        else:
             # Explicitly handle offline mode if the CLI needs a flag for it
             # cmd.append("--offline") # Uncomment if readmeai needs an explicit --offline flag
             pass # Assuming offline is default or handled by omitting --api/--model

        for key, value in options.items():
            cli_arg = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value: # Add flag only if True
                    cmd.append(cli_arg)
            elif value is not None: # Add argument and value if not None
                 cmd.extend([cli_arg, str(value)])

        logger.info(f"Constructed command: {' '.join(cmd)}")
        return cmd

    def _execute_command(
        self, command: List[str], api_key: str | None, selected_provider: str
    ) -> None:
        """Execute the readmeai command synchronously and capture output."""
        env = os.environ.copy()
        api_key_env_var = PROVIDER_ENV_VARS.get(selected_provider)

        # Set API key in environment if provided and needed
        if api_key and api_key_env_var:
            env[api_key_env_var] = api_key
            logger.info(f"Using provided API key for {selected_provider}.")
        elif api_key_env_var and api_key_env_var not in env:
             # Warn if API key is needed but not provided via input or environment
             logger.warning(f"API key for {selected_provider} not found in input or environment variable {api_key_env_var}.")
             st.warning(f"API key for {selected_provider} not provided. Check environment variable `{api_key_env_var}` or input field.")
             # Depending on readmeai behavior, might want to raise an error here

        try:
            # Use st.spinner for user feedback during the blocking call
            with st.spinner("Generating README... Please wait."):
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=False # Check manually to display stderr
                )

            # Display logs/errors after execution
            if process.stderr:
                 st.text_area("Generation Logs", value=process.stderr, height=200)

            # Raise error if the command failed
            process.check_returncode()

        except FileNotFoundError:
             st.error("Error: 'readmeai' command not found. Is it installed and in your PATH?")
             logger.error("'readmeai' command not found.")
             raise
        except subprocess.CalledProcessError as e:
             st.error(f"README generation failed (return code {e.returncode}). See logs above for details.")
             logger.error(f"readmeai command failed: {e.stderr}")
             # Re-raise to stop execution if desired, or handle more gracefully
             raise
        except Exception as e:
             st.error(f"An unexpected error occurred: {e}")
             logger.exception("Unexpected error during command execution.")
             raise

    def _generate_readme(
        self, repo_path: str, api_key: str | None, config: Dict[str, str], options: Dict[str, Any]
    ) -> None:
        """Generate README using provided configuration."""
        # Reset state before generation
        st.session_state[README_GENERATED_KEY] = False
        st.session_state[README_CONTENT_KEY] = "Generating..."

        try:
            # Use a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_file:
                output_path = tmp_file.name

            logger.info(f"Generating README for repository: {repo_path}")
            logger.info(f"Using model config: {config}")
            logger.info(f"Using options: {options}")
            logger.info(f"Outputting to temporary file: {output_path}")

            command = self._build_command(repo_path, output_path, config, options)

            # Execute the command synchronously
            self._execute_command(command, api_key, config["provider"].upper())

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

        except (subprocess.CalledProcessError, FileNotFoundError):
             # Errors already logged and displayed by _execute_command
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
    app = ReadmeAIApp()
    app.run()