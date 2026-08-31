import markdown
import nh3
from django.conf import settings


def markdownify(content):
    html = markdown.markdown(content or "", extensions=settings.FAIRDM_MARKDOWN_EXTENSIONS)
    return nh3.clean(html)
