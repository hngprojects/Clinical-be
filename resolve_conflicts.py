import os
import re


def replace_in_file(filepath, callback):
    with open(filepath, "r") as f:
        content = f.read()
    new_content = callback(content)
    with open(filepath, "w") as f:
        f.write(new_content)


# 1. pyproject.toml
def fix_pyproject(content):
    return re.sub(
        r'<<<<<<< HEAD\n\s*"httpx(.*?)\n\s*"python-jose(.*?)\n=======\n\s*"bcrypt(.*?)\n>>>>>>> origin/dev',
        r'    "httpx\1\n    "python-jose\2\n    "bcrypt\3',
        content,
    )


replace_in_file("pyproject.toml", fix_pyproject)


# 2. app/schemas/__init__.py
def fix_schemas_init(content):
    return re.sub(
        r"<<<<<<< HEAD\nfrom app.schemas.auth import GoogleAuthData\n=======\nfrom app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest\n>>>>>>> origin/dev",
        "from app.schemas.auth import GoogleAuthData, ForgotPasswordRequest, ResetPasswordRequest",
        content,
    )


replace_in_file("app/schemas/__init__.py", fix_schemas_init)

# 3, 4, 7. Keep dev versions of router, alembic, security
os.system("git checkout origin/dev -- app/api/v1/router.py")
os.system(
    "git checkout origin/dev -- alembic/versions/a88e01cfb395_add_ai_interpretation_chat_waitlist_and_.py"
)
os.system("git checkout origin/dev -- app/core/security.py")


# 5. app/core/config.py
def fix_config(content):
    return re.sub(
        r"<<<<<<< HEAD\n\s*# Google OAuth\n(.*?)\n\s*# JWT\n.*?\n=======\n(.*?)\n>>>>>>> origin/dev",
        r"\t# Google OAuth\n\1\n\n\2",
        content,
        flags=re.DOTALL,
    )


replace_in_file("app/core/config.py", fix_config)
