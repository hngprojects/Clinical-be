# Fix app/api/v1/endpoints/auth.py
with open("app/api/v1/endpoints/auth.py", "r") as f:
	content = f.read()

# Move the urllib and settings imports to the top
content = content.replace(
	"from urllib.parse import urlencode\n\nfrom fastapi import HTTPException\nfrom fastapi.responses import RedirectResponse\n\nfrom app.core.config import get_settings\nfrom app.schemas.auth import GoogleAuthData\nfrom app.services.oauth import (\n\texchange_google_code,\n\tfetch_google_user_info,\n\tget_or_create_google_user,\n)",
	"",
)

imports = """from urllib.parse import urlencode
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import get_settings
from app.schemas.auth import GoogleAuthData
from app.schemas.user import UserResponse
from app.api.deps import DBSession
from app.services.oauth import (
\texchange_google_code,
\tfetch_google_user_info,
\tget_or_create_google_user,
)
"""

content = imports + content
with open("app/api/v1/endpoints/auth.py", "w") as f:
	f.write(content)

# Fix app/schemas/auth.py
with open("app/schemas/auth.py", "r") as f:
	content = f.read()

if "from app.schemas.user import UserResponse" not in content:
	content = "from app.schemas.user import UserResponse\n" + content

with open("app/schemas/auth.py", "w") as f:
	f.write(content)
