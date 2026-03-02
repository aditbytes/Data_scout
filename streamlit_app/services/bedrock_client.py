"""
DataScout — Amazon Bedrock Agent Client.

Wraps the Bedrock Agent Runtime API for query processing with
streaming response parsing and structured output extraction.
Compatible with any Bedrock-supported model (Nova Pro, Claude, etc.).
"""

import logging
import re
from html import unescape
from typing import Dict, List

import boto3
import botocore.config

from config import Config

logger = logging.getLogger('datascout.bedrock')


class BedrockAgentClient:
    """Amazon Bedrock Agent Runtime client wrapper.

    Handles invocation of the Bedrock Agent, streaming response parsing,
    and extraction of structured components (explanation, code, results,
    visualizations) from the agent's response.
    """

    def __init__(self):
        """Initialize the Bedrock Agent Runtime client."""
        config = botocore.config.Config(
            region_name=Config.AWS_REGION,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60
        )
        self.client = boto3.client('bedrock-agent-runtime', config=config)
        self.agent_id: str = Config.BEDROCK_AGENT_ID
        self.agent_alias_id: str = Config.BEDROCK_AGENT_ALIAS_ID

    def invoke_agent(self, query: str, session_id: str,
                     dataset_uri: str) -> Dict:
        """Invoke the Bedrock Agent with a user query.

        Args:
            query: The natural language question from the user.
            session_id: Unique session identifier for conversation context.
            dataset_uri: S3 URI of the uploaded dataset.

        Returns:
            Structured dict with keys: explanation, code, results,
            visualizations, next_steps.

        Raises:
            botocore.exceptions.ClientError: On AWS API errors.
        """
        session_state = {
            'sessionAttributes': {
                'dataset_format': 'csv'
            }
        }

        # Nova Pro requires the exact S3 Bucket name that the Bedrock agent has permissions for
        if dataset_uri:
            # Enforce that the bucket name is the one the Bedrock agent role is configured for
            # The DataScoutAgentS3Access role specifically grants access to 'datascout-storage-use2'
            if 'datascout-storage-use2' not in dataset_uri:
                logger.warning(f"Original URI {dataset_uri} doesn't match agent role bucket. Replacing...")
                file_name = dataset_uri.split('/')[-1]
                dataset_uri = f"s3://datascout-storage-use2/datasets/{session_id}/original/{file_name}"
                
            session_state['sessionAttributes']['dataset_uri'] = dataset_uri
            session_state['files'] = [
                {
                    'name': dataset_uri.split('/')[-1],
                    'source': {
                        'sourceType': 'S3',
                        's3Location': {
                            'uri': dataset_uri
                        }
                    },
                    'useCase': 'CODE_INTERPRETER'
                }
            ]

        # ── Append output format hint ──────────────────────────────────────
        # Request structured, detailed output with clear section markers.
        enhanced_query = (
            f"{query}\n\n"
            "Please provide a comprehensive analysis with these sections:\n"
            "## Executive Summary\n"
            "A 2-3 sentence overview of the most important findings.\n\n"
            "## Methodology\n"
            "Brief description of the analytical approach and techniques used.\n\n"
            "## Key Findings\n"
            "List the top 3-5 most important discoveries as bullet points "
            "with specific numbers and percentages.\n\n"
            "## Detailed Analysis\n"
            "In-depth explanation with statistics, comparisons, and context. "
            "Include results as a markdown table.\n\n"
            "## Recommendations\n"
            "2-3 actionable next steps based on the analysis.\n\n"
            "CRITICAL REQUIREMENT: You MUST include the Python code you used and you MUST generate at least one chart image for EVERY question to visualize the results. "
            "If using Matplotlib, ensure you call `plt.tight_layout()` so that long labels are not cut off."
        )

        response = self.client.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.agent_alias_id,
            sessionId=session_id,
            inputText=enhanced_query,
            enableTrace=True,
            sessionState=session_state
        )
        return self._parse_response(response)

    def _parse_response(self, response: dict) -> Dict:
        """Parse streaming response into structured components.

        Captures both text chunks and file outputs (e.g., chart images)
        from the Bedrock Agent completion stream.

        Args:
            response: Raw response from invoke_agent API.

        Returns:
            Structured dict with extracted components.
        """
        chunks: List[str] = []
        chart_images: list = []  # Raw image bytes from Code Interpreter

        for event in response.get('completion', []):
            # ── Text chunks
            if 'chunk' in event:
                chunk_bytes = event['chunk'].get('bytes', b'')
                chunks.append(chunk_bytes.decode('utf-8'))

            # ── File outputs from Code Interpreter (chart images)
            if 'files' in event:
                files_data = event['files'].get('files', [])
                for f in files_data:
                    file_bytes = f.get('bytes', b'')
                    file_name = f.get('name', 'chart.png')
                    file_type = f.get('type', 'image/png')
                    if file_bytes and ('image' in file_type or
                                       file_name.endswith(('.png', '.jpg', '.jpeg', '.svg'))):
                        chart_images.append({
                            'bytes': file_bytes,
                            'name': file_name,
                            'type': file_type
                        })
                        logger.info("Captured chart image: %s (%d bytes)",
                                    file_name, len(file_bytes))

        full_text = ''.join(chunks)

        # Log raw response for debugging — critical when switching models
        logger.debug("Raw agent response length: %d chars", len(full_text))
        logger.debug("Raw agent response:\n%s", full_text)

        if not full_text.strip() and not chart_images:
            logger.warning("Agent returned an empty response")
            return {
                'explanation': 'The agent returned an empty response. '
                               'Please try rephrasing your question.',
                'code': '',
                'results': '',
                'visualizations': [],
                'chart_images': [],
                'next_steps': []
            }

        result = self._extract_components(full_text)
        result['chart_images'] = chart_images
        return result

    def _extract_components(self, text: str) -> Dict:
        """Extract structured components from the agent's text response.

        Model-agnostic parser that handles section-based output
        (Executive Summary, Methodology, Key Findings, etc.) as well
        as code blocks and S3 URIs.

        Args:
            text: Full text response from the agent.

        Returns:
            Dict with keys: explanation, executive_summary, methodology,
            key_findings, detailed_analysis, recommendations, code,
            results, visualizations, next_steps.
        """
        components = {
            'explanation': '',
            'executive_summary': '',
            'methodology': '',
            'key_findings': [],
            'detailed_analysis': '',
            'recommendations': [],
            'code': '',
            'results': '',
            'visualizations': [],
            'next_steps': []
        }

        # ── Extract code blocks (supports ```python, ```py, and bare ```)
        code_blocks = re.findall(
            r'```(?:python|py)\s*\n(.*?)```', text, re.DOTALL
        )
        if not code_blocks:
            code_blocks = re.findall(
                r'```\s*\n(.*?)```', text, re.DOTALL
            )
        if code_blocks:
            components['code'] = code_blocks[-1].strip()

        # ── Extract S3 visualization URIs
        s3_uris = re.findall(r's3://[^\s\>\"\'\'\]\)]+', text)
        components['visualizations'] = s3_uris

        # ── Strip S3 references from text
        cleaned_text = text
        if s3_uris:
            cleaned_text = re.sub(
                r'!\[[^\]]*\]\(s3://[^\)]+\)', '', cleaned_text
            )
            for uri in s3_uris:
                cleaned_text = cleaned_text.replace(uri, '')
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # ── Remove code blocks from cleaned text for section extraction
        text_no_code = re.sub(
            r'```(?:\w*)\s*\n.*?```', '', cleaned_text, flags=re.DOTALL
        ).strip()

        # ── Extract structured sections using ## headers
        self._extract_section(
            text_no_code, components, 'executive_summary',
            r'(?:##\s*(?:Executive\s+)?Summary)\s*\n(.*?)(?=\n##\s|$)'
        )
        self._extract_section(
            text_no_code, components, 'methodology',
            r'(?:##\s*(?:Methodology|Approach|Method))\s*\n(.*?)(?=\n##\s|$)'
        )
        self._extract_section(
            text_no_code, components, 'detailed_analysis',
            r'(?:##\s*(?:Detailed\s+)?Analysis)\s*\n(.*?)(?=\n##\s|$)'
        )

        # ── Key Findings: extract as list items
        findings_match = re.search(
            r'(?:##\s*(?:Key\s+)?Findings?)\s*\n(.*?)(?=\n##\s|$)',
            text_no_code, re.DOTALL | re.IGNORECASE
        )
        if findings_match:
            findings_text = findings_match.group(1)
            components['key_findings'] = self._extract_list_items(findings_text)

        # ── Recommendations
        rec_match = re.search(
            r'(?:##\s*(?:Recommendations?|Next\s+Steps?|Suggestions?))\s*\n(.*?)(?=\n##\s|$)',
            text_no_code, re.DOTALL | re.IGNORECASE
        )
        if rec_match:
            rec_text = rec_match.group(1)
            components['recommendations'] = self._extract_list_items(rec_text)
            components['next_steps'] = components['recommendations'][:5]

        # ── Results: look for tables in the detailed analysis or results section
        results_match = re.search(
            r'(?:##\s*(?:Results?|Data|Output))\s*\n(.*?)(?=\n##\s|$)',
            text_no_code, re.DOTALL | re.IGNORECASE
        )
        if results_match:
            components['results'] = results_match.group(1).strip()

        # If no dedicated results section, extract tables from detailed analysis
        if not components['results']:
            table_match = re.search(
                r'(\|.+\|\n\|[-: |]+\|\n(?:\|.+\|\n?)+)',
                text_no_code, re.MULTILINE
            )
            if table_match:
                components['results'] = table_match.group(1).strip()

        # ── Explanation: use text before the first ## section as general explanation
        pre_section = re.split(r'\n##\s', text_no_code, maxsplit=1)
        if pre_section and pre_section[0].strip():
            components['explanation'] = pre_section[0].strip()

        # ── If no structured sections found, use legacy fallback
        has_structured = any([
            components['executive_summary'],
            components['key_findings'],
            components['detailed_analysis']
        ])

        if not has_structured:
            logger.info("No structured sections found; using fallback parsing")
            # Legacy fallback: split around code blocks
            parts = re.split(
                r'```(?:\w*)\s*\n.*?```', cleaned_text, flags=re.DOTALL
            )
            if len(parts) >= 1 and parts[0].strip():
                components['explanation'] = parts[0].strip()
            if len(parts) >= 2:
                results_text = '\n'.join(
                    p.strip() for p in parts[1:] if p.strip()
                )
                components['results'] = results_text

            # Extract next steps from unstructured text
            next_steps_match = re.search(
                r'(?:next\s*steps?|suggestions?|you\s*(?:can|could|might)\s*(?:also|try))[:\s]*\n'
                r'((?:\s*[-•*\d.]+\s*.+\n?)+)',
                text, re.IGNORECASE
            )
            if next_steps_match:
                steps_text = next_steps_match.group(1)
                steps = re.findall(r'[-•*\d.]+\s*(.+)', steps_text)
                components['next_steps'] = [
                    s.strip() for s in steps if s.strip()
                ]

        # ── Final fallback: always show something
        if (not components['explanation'] and
                not components['executive_summary'] and
                not components['code'] and
                not components['results']):
            logger.info("No components found; using raw text as explanation")
            components['explanation'] = cleaned_text.strip()

        # ── Normalize text fields and de-duplicate list fields
        for key in ['explanation', 'executive_summary', 'methodology',
                    'detailed_analysis', 'results']:
            components[key] = self._clean_text(components[key])
        components['key_findings'] = self._dedupe_preserve_order(
            [self._clean_text(x) for x in components['key_findings'] if x]
        )
        components['recommendations'] = self._dedupe_preserve_order(
            [self._clean_text(x) for x in components['recommendations'] if x]
        )
        if components['recommendations'] and not components['next_steps']:
            components['next_steps'] = components['recommendations'][:5]

        return components

    @staticmethod
    def _extract_section(text: str, components: dict,
                         key: str, pattern: str) -> None:
        """Extract a named section from text using a regex pattern."""
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            components[key] = match.group(1).strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize model text output and strip accidental HTML wrappers."""
        if not text:
            return ''

        cleaned = unescape(text).replace('\r\n', '\n').replace('\r', '\n')
        cleaned = re.sub(r'<\s*br\s*/?\s*>', '\n', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r'</\s*(?:div|p|li|ul|ol|section|article|h\d)\s*>',
            '\n',
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        cleaned = cleaned.replace('```', '')
        cleaned = re.sub(r'[ \t]+\n', '\n', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _extract_list_items(self, section_text: str) -> List[str]:
        """Extract bullets from markdown or lightweight HTML list content."""
        if not section_text:
            return []

        items: List[str] = []

        # HTML list items
        html_li_items = re.findall(
            r'<li[^>]*>(.*?)</li>', section_text, re.DOTALL | re.IGNORECASE
        )
        items.extend(self._clean_text(item) for item in html_li_items if item.strip())

        # Custom finding-text blocks occasionally returned by the model
        custom_finding_items = re.findall(
            r'class=["\']finding-text["\'][^>]*>(.*?)</[^>]+>',
            section_text,
            re.DOTALL | re.IGNORECASE
        )
        items.extend(
            self._clean_text(item) for item in custom_finding_items if item.strip()
        )

        # Markdown bullets / numbered lists
        cleaned_block = self._clean_text(section_text)
        markdown_items = re.findall(
            r'^\s*(?:[-*•]+|\d+[.)])\s+(.+)$',
            cleaned_block,
            re.MULTILINE
        )
        items.extend(self._clean_text(item) for item in markdown_items if item.strip())

        # Last-resort split by non-empty lines (ignoring standalone numbers)
        if not items and cleaned_block:
            for line in cleaned_block.splitlines():
                line = line.strip().strip('-*•')
                if not line or re.fullmatch(r'\d+[.)]?', line):
                    continue
                if len(line.split()) >= 3:
                    items.append(line)

        return self._dedupe_preserve_order(items)

    @staticmethod
    def _dedupe_preserve_order(items: List[str]) -> List[str]:
        """De-duplicate while preserving original order."""
        seen = set()
        deduped = []
        for item in items:
            if item and item not in seen:
                deduped.append(item)
                seen.add(item)
        return deduped
