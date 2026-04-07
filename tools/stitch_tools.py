# tools/stitch_tools.py
import asyncio
import json
from pathlib import Path

import nest_asyncio
nest_asyncio.apply()

from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

from llm.provider import get_llm
from tools.stitch_client import StitchMCPClient


def _get_client() -> StitchMCPClient:
    return StitchMCPClient()


@tool
def create_stitch_project(title: str) -> str:
    """Create a new Stitch UI project. Returns the numeric project_id string."""

    async def _run():
        client = _get_client()
        res = await client.call_tool("create_project", {"title": title})
        content_text = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
        project_data = json.loads(content_text)
        full_name = project_data.get("name", "")
        project_id = full_name.replace("projects/", "")
        if not project_id:
            raise ValueError(f"Stitch create_project returned no project ID. Response: {project_data}")
        return project_id

    return asyncio.run(_run())


@tool
def generate_screen(project_id: str, prompt: str, device_type: str = "DESKTOP") -> str:
    """Generate a UI screen via Stitch from a text prompt. Returns the design content (HTML/Markdown)."""

    async def _run():
        client = _get_client()
        res = await client.call_tool(
            "generate_screen_from_text",
            {
                "projectId": project_id,
                "prompt": prompt,
                "deviceType": device_type,
                "modelId": "GEMINI_3_1_PRO",
            },
        )
        try:
            generated = json.loads(
                res.get("result", {}).get("content", [{}])[0].get("text", "{}")
            )
            design_md = (
                generated.get("outputComponents", [{}])[0]
                .get("designSystem", {})
                .get("designSystem", {})
                .get("designMd", "")
            )
            return design_md or json.dumps(generated)
        except Exception as e:
            return f"Error extracting design content: {e}"

    return asyncio.run(_run())


@tool
def save_and_convert_to_react(html_content: str, screen_name: str) -> str:
    """Save HTML from Stitch locally and convert it to a React functional component using JSX + Tailwind CSS."""
    safe_name = Path(screen_name).name  # strips directory separators

    # Save raw HTML
    stitch_dir = Path("output/stitch")
    stitch_dir.mkdir(parents=True, exist_ok=True)
    html_path = stitch_dir / f"{safe_name}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Convert to React via LLM
    llm = get_llm()
    prompt = PromptTemplate.from_template(
        """You are a senior frontend developer. Convert the following HTML/design spec into a React functional component.

Rules:
- Use React hooks (useState, useEffect) only where needed
- Use Tailwind CSS classes for all styling (no inline styles)
- Export the component as default
- Component name: {component_name}
- Return ONLY the JSX/TSX code, no explanations or markdown fences

HTML/Design:
{html_content}
"""
    )
    chain = prompt | llm
    result = chain.invoke({"component_name": safe_name, "html_content": html_content})
    jsx_content = result.content if hasattr(result, "content") else str(result)

    # Save React component
    react_dir = Path(f"output/react/src/components/{safe_name}")
    react_dir.mkdir(parents=True, exist_ok=True)
    jsx_path = react_dir / f"{safe_name}.jsx"
    jsx_path.write_text(jsx_content, encoding="utf-8")

    return f"HTML saved to {html_path}\nReact component saved to {jsx_path}"
