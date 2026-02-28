"""
DataScout — File Upload Component.

Renders a modern drag-and-drop file upload widget with format and size validation.
"""

from typing import Optional

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config import Config


def render_upload_widget() -> Optional[UploadedFile]:
    """Render the file upload widget with validation and feedback.

    Features:
        - Drag-and-drop support
        - File format validation (.csv, .xlsx, .xls, .json)
        - File size validation (max 100 MB)
        - Upload progress indicator
        - Success/error feedback

    Returns:
        UploadedFile object if a valid file was uploaded, None otherwise.
    """
    # Format the accepted types for display
    format_display = ", ".join(sorted(Config.SUPPORTED_FORMATS))

    uploaded_file = st.file_uploader(
        "Drag and drop a file here, or click to browse",
        type=[fmt.lstrip('.') for fmt in Config.SUPPORTED_FORMATS],
        help=f"Supported formats: {format_display} | Max size: {Config.MAX_FILE_SIZE_MB} MB",
        key="dataset_uploader"
    )

    if uploaded_file is not None:
        # Validate file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > Config.MAX_FILE_SIZE_MB:
            st.error(
                f"**⚠️ File Too Large**\n\n"
                f"Your file is {file_size_mb:.1f} MB, which exceeds the "
                f"{Config.MAX_FILE_SIZE_MB} MB limit."
            )
            st.info("💡 Try reducing your dataset size or splitting it into smaller files.")
            return None

        return uploaded_file

    return None
