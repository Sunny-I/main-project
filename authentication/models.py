from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _  
from django.contrib.auth.forms import User


class Register(models.Model):
    username = models.CharField(max_length=20)
    email = models.EmailField(_("Email address"), max_length=254)
    password = models.CharField( _("Password"),max_length=50,)
    confirm_password = models.CharField( _("confirm password"),)






