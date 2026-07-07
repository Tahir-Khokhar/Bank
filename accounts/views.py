"""Accounts web views.

This module contains class-based views only.
"""

from __future__ import annotations

from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    """Render the landing page at the root URL (/)."""

    template_name = 'index.html'

