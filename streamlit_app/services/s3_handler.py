"""
DataScout — Amazon S3 Handler.

Manages dataset upload, download, metadata extraction, and artifact retrieval
from Amazon S3 with encryption and validation.
"""

import io
from pathlib import Path
from typing import Dict, Tuple

import boto3
import pandas as pd

from config import Config


class S3Handler:
    """Amazon S3 operations for dataset and artifact management.

    Handles secure upload with encryption, metadata extraction,
    artifact download, and session data cleanup.
    """

    def __init__(self):
        """Initialize the S3 client."""
        self.s3 = boto3.client('s3', region_name=Config.AWS_REGION)
        # Force the bucket to the one the Bedrock agent role has permissions for
        self.bucket: str = "datascout-storage-use2"

    def upload_dataset(self, file_obj, session_id: str) -> str:
        """Upload a dataset to S3 with validation and encryption.

        Args:
            file_obj: File-like object (from Streamlit file uploader).
            session_id: Unique session identifier for path isolation.

        Returns:
            S3 URI of the uploaded file (s3://bucket/key).

        Raises:
            ValueError: If file format or size is invalid.
        """
        self._validate_file(file_obj)

        key = f"datasets/{session_id}/original/{file_obj.name}"
        file_obj.seek(0)
        self.s3.upload_fileobj(
            file_obj, self.bucket, key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        return f"s3://{self.bucket}/{key}"

    def get_dataset_metadata(self, s3_uri: str) -> Dict:
        """Extract metadata from an uploaded dataset.

        Downloads the file, parses it with pandas, and extracts schema
        information including column names, types, row count, and a preview.

        Args:
            s3_uri: S3 URI of the dataset.

        Returns:
            Metadata dict with keys: filename, rows, columns, dtypes,
            size_mb, preview, null_counts.
        """
        bucket, key = self._parse_uri(s3_uri)
        response = self.s3.get_object(Bucket=bucket, Key=key)
        body = response['Body'].read()
        filename = key.split('/')[-1]
        ext = Path(filename).suffix.lower()

        if ext == '.csv':
            df = pd.read_csv(io.BytesIO(body), nrows=1000)
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(io.BytesIO(body), nrows=1000)
        elif ext == '.json':
            df = pd.read_json(io.BytesIO(body))
        else:
            raise ValueError(f"Unsupported format: {ext}")

        return {
            'filename': filename,
            'rows': len(df),
            'columns': list(df.columns),
            'dtypes': {c: str(d) for c, d in df.dtypes.items()},
            'size_mb': round(len(body) / (1024 * 1024), 2),
            'preview': df.head(5).to_dict(orient='records'),
            'null_counts': {c: int(v) for c, v in df.isnull().sum().items()}
        }

    def download_artifact(self, s3_uri: str) -> bytes:
        """Download artifact bytes (e.g., chart image) from S3.

        Args:
            s3_uri: S3 URI of the artifact.

        Returns:
            Raw bytes of the artifact file.
        """
        bucket, key = self._parse_uri(s3_uri)
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def delete_session_data(self, session_id: str) -> None:
        """Delete all data associated with a session.

        Removes datasets, artifacts, and logs for the given session.

        Args:
            session_id: Session identifier whose data should be purged.
        """
        prefixes = [
            f"datasets/{session_id}/",
            f"artifacts/{session_id}/",
            f"logs/{session_id}/"
        ]
        for prefix in prefixes:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            objects = response.get('Contents', [])
            if objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects]
                self.s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': delete_keys}
                )

    def _validate_file(self, file_obj) -> None:
        """Validate file format and size before upload.

        Args:
            file_obj: File-like object to validate.

        Raises:
            ValueError: If the file format is unsupported or size exceeds limit.
        """
        ext = Path(file_obj.name).suffix.lower()
        if ext not in Config.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported: {', '.join(sorted(Config.SUPPORTED_FORMATS))}"
            )
        file_obj.seek(0, 2)
        size_mb = file_obj.tell() / (1024 * 1024)
        file_obj.seek(0)
        if size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {size_mb:.1f}MB > {Config.MAX_FILE_SIZE_MB}MB"
            )

    @staticmethod
    def _parse_uri(uri: str) -> Tuple[str, str]:
        """Parse an S3 URI into bucket and key.

        Args:
            uri: S3 URI in format s3://bucket/key.

        Returns:
            Tuple of (bucket, key).
        """
        parts = uri.replace('s3://', '').split('/', 1)
        return parts[0], parts[1]
