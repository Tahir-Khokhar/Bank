from __future__ import annotations  # Enables postponed evaluation of type annotations.

from django.views.generic import TemplateView  # Imports the generic template-based view.


class LandingPageView(TemplateView):  # Displays the landing page template.
    
    template_name = 'index.html'
