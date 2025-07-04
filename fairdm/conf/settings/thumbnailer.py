# EASY_THUMBNAILS SETTINGS
THUMBNAIL_CACHE_DIMENSIONS = True
""""""

# THUMBNAIL_CHECK_CACHE_MISS = True
THUMBNAIL_SUBDIR = "thumbs"
""""""

THUMBNAIL_ALIASES = {
    "contributors.Contributor": {
        "thumb": {"size": (48, 48), "crop": False},
        "small": {"size": (150, 150), "crop": False},
        "medium": {"size": (600, 600), "crop": False},
    },
}
""""""

THUMBNAIL_PROCESSORS = [
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "easy_thumbnails.processors.scale_and_crop",
    "easy_thumbnails.processors.filters",
]
""""""

THUMBNAIL_DEBUG = True
""""""
