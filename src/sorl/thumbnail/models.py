from django.core.cache import cache
from django.db import models
from django.db.models import signals
from sorl.thumbnail.conf import settings
from sorl.thumbnail.helpers import get_or_set_cache


def get_cache_key(key):
    return '%s%s' % (settings.THUMBNAIL_CACHE_PREFIX, key)


class ThumbnailCacheManager(models.Manager):
    def get(self, key):
        def get_thumbnail_from_db():
            sup = super(ThumbnailCacheManager, self)
            return sup.get_query_set().get(pk=key)
        cache_key = get_cache_key(key)
        return get_or_set_cache(cache_key, get_thumbnail_from_db)


class Thumbnail(models.Model):
    # This pk approach should sport a faster lookup when ever we need to reach
    # the db.
    key = models.CharField(max_length=32, primary_key=True)
    source_name = models.CharField(max_length=1000)
    source_storage = models.CharField(max_length=200)
    geometry = models.CharField(max_length=11)
    options = models.CharField(max_length=1000)

    name = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000)
    path = models.CharField(max_length=1000)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    filesize = models.PositiveIntegerField()

    objects = models.Manager()
    cache = ThumbnailCacheManager()

    @property
    def cache_key(self):
        return get_cache_key(self.key)

    # x, y aliases
    x = property(lambda self: self.width)
    y = property(lambda self: self.height)


def invalidate_cache(sender, instance, **kwargs):
    cache.delete(instance.cache_key)

def update_cache(sender, instance, **kwargs):
    cache.set(instance.cache_key, instance, settings.THUMBNAIL_CACHE_TIMEOUT)

signals.pre_save.connect(invalidate_cache, sender=Thumbnail)
signals.post_save.connect(update_cache, sender=Thumbnail)
signals.pre_delete.connect(invalidate_cache, sender=Thumbnail)

