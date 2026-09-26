from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class SuperuserAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(self.error_messages['invalid_login'], code='invalid_login',
                                  params={'username': self.username_field.verbose_name})


class SuperuserAdminSite(AdminSite):
    """O painel global inclui contas e tokens de todos os responsáveis."""

    login_form = SuperuserAuthenticationForm

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser
