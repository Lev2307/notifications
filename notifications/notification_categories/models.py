from django.db import models

from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class NotificationCategory(models.Model):
    # A model of the notification category, for example, study
    user = models.ForeignKey(
        'authentication.MyUser', 
        null=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("User"),
    ) 
    name_type = models.CharField( # the category name
        _("Category name"),
        max_length=15
    )
    color = models.CharField( # category color
        _("Color"), 
        max_length=15
    )
    slug = models.SlugField(_("Slug"), allow_unicode=True)

    class Meta:
        verbose_name = 'Notification category'
        verbose_name_plural = 'Notification categories'

    def __str__(self):
        return self.name_type
    
    def save(self, *args, **kwargs):
        if not self.slug and self.name_type not in ['study', 'work', 'sport']:
            self.slug = slugify(self.name_type, allow_unicode=True)
        return super().save(*args, **kwargs)