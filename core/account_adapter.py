"""
Custom adapters for django-allauth + Keycloak integration.

Integrates Keycloak OIDC authentication with our custom user management approach
(storing Keycloak user_id and username in tramite models).
"""

from typing import Optional
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for django-allauth account operations.

    We don't create Django users, just return the SocialAccount user info.
    """

    def save_user(self, request, user, form):
        """
        Override to prevent user creation in Django.

        In our microservice architecture, users are managed in Keycloak only.
        We don't store users in Django database.
        """
        # Return the user without saving (we're not managing users)
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for django-allauth social account (Keycloak OIDC).

    Stores Keycloak user information that we need for our tramite models.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called before social login completes.

        Here we can extract Keycloak user info and store it in the session
        for use in our views.
        """
        # Get extra data from Keycloak (OIDC)
        extra_data = sociallogin.account.extra_data or {}

        # Keycloak claims that we need
        user_id = extra_data.get("sub")
        username = extra_data.get("preferred_username")
        email = extra_data.get("email")

        # Get roles from Keycloak (realm_access)
        realm_access = extra_data.get("realm_access", {})
        roles = realm_access.get("roles", [])

        # Store in session for use in views
        request.session["keycloak_user_id"] = user_id
        request.session["keycloak_username"] = username
        request.session["keycloak_email"] = email
        request.session["keycloak_roles"] = roles

        # Also attach to sociallogin for easy access
        sociallogin.state["keycloak_user_id"] = user_id
        sociallogin.state["keycloak_username"] = username
        sociallogin.state["keycloak_email"] = email
        sociallogin.state["keycloak_roles"] = roles

        return super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        """
        Called to populate the user from social account data.

        We skip user creation/updates as users are managed in Keycloak.
        """
        # We don't populate/update Django User
        return super().populate_user(request, sociallogin, data)

    def authentication_failed(self, request, provider_id, error=None, exception=None):
        """
        Called when authentication fails.
        """
        from django.contrib import messages

        messages.error(
            request, f"Authentication failed with {provider_id}. Please try again."
        )
        return super().authentication_failed(request, provider_id, error, exception)


def get_keycloak_user_info(request) -> dict:
    """
    Get Keycloak user information from session.

    This is a helper function to be used in views instead of
    accessing request.user directly (since we're not managing users in Django).

    Args:
        request: Django request object

    Returns:
        Dictionary with Keycloak user info or empty dict if not authenticated
    """
    return {
        "user_id": request.session.get("keycloak_user_id"),
        "username": request.session.get("keycloak_username"),
        "email": request.session.get("keycloak_email"),
        "roles": request.session.get("keycloak_roles", []),
    }


def user_has_role(request, role: str) -> bool:
    """
    Check if authenticated user has a specific role from Keycloak.

    Args:
        request: Django request object
        role: Role name to check

    Returns:
        True if user has role, False otherwise
    """
    roles = request.session.get("keycloak_roles", [])
    return role in roles


def is_authenticated(request) -> bool:
    """
    Check if user is authenticated via Keycloak.

    Args:
        request: Django request object

    Returns:
        True if authenticated, False otherwise
    """
    return "keycloak_user_id" in request.session
