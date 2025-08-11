from rest_access_policy import AccessPolicy

# Principal: *, admin, staff, authenticated, anonymous, group:name, id:id


class CoreAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["<safe_methods>"],
            "principal": ["anonymous"],
            "effect": "allow",
        },
        {
            "action": ["*"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]
