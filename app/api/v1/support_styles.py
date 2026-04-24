"""
Support Style / Tone Mode catalogue endpoint.

The catalogue is a read-only list served from code, not a DB table — see
app/core/support_style.py for the why. Clients hit this once on app load
to populate the sidebar toggle; changes to the list require a redeploy.
"""
from fastapi import APIRouter

from app.core.support_style import DEFAULT_STYLE, list_styles
from app.schemas.chat import SupportStyleCatalogueResponse, SupportStyleOption

router = APIRouter()


@router.get("", response_model=SupportStyleCatalogueResponse)
async def get_support_style_catalogue():
    """Return the tone-mode catalogue + the global default slug."""
    return SupportStyleCatalogueResponse(
        default=DEFAULT_STYLE,
        styles=[
            SupportStyleOption(
                slug=style.slug,
                name=style.name,
                description=style.description,
            )
            for style in list_styles()
        ],
    )
