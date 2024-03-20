from copy import copy
from typing import Any
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


def val_scalar_dict(attribute: str):
    def val(
        dict_str_any: dict[str, Any],
    ) -> dict[str, Union[int, float, str, bool]]:
        for key, value in dict_str_any.items():
            if not isinstance(value, (int, float, str, bool)):
                raise ValueError(
                    f"{attribute}[{key}] must be a scalar (int, float, str, "
                    f"bool, or None). Given {value} ({type(value)})"
                )
        return dict_str_any

    return val


class SingleImage(BaseModel):

    path: str
    origin: Optional[str] = None

    attributes: dict[str, Any] = Field(default_factory=dict)
    flags: dict[str, bool] = Field(default_factory=dict)

    _attributes = validator("attributes", allow_reuse=True)(
        val_scalar_dict("attributes")
    )

    def match_filter(
        self,
        attribute_filters: Optional[dict[str, Any]] = None,
        flag_filters: Optional[dict[str, bool]] = None,
    ):
        if attribute_filters is None and flag_filters is None:
            return True

        if flag_filters is not None:
            for key, value in flag_filters.items():
                if self.flags.get(key, False) != value:
                    return False

        if attribute_filters is not None:
            for key, value in attribute_filters.items():
                if value is None:
                    continue
                if self.attributes.get(key) != value:
                    return False

        return True


def find_image_by_path(
    *,
    images: list[SingleImage],
    path: str,
) -> Optional[SingleImage]:
    """
    Return a copy of the image with a given path, from a list.

    Args:
        images: List of images.
        path: Path that the returned image must have.

    Returns:
        The first image from `images` which has path equal to `path`.
    """
    try:
        image = next(image for image in images if image.path == path)
        return copy(image)
    except StopIteration:
        return None


def _filter_image_list(
    images: list[SingleImage],
    attribute_filters: Optional[dict[str, Any]] = None,
    flag_filters: Optional[dict[str, Any]] = None,
) -> list[SingleImage]:
    if attribute_filters is None and flag_filters is None:
        # When no filter is provided, return all images
        return images

    filtered_images = []
    for this_image in images:
        if this_image.match_filter(
            attribute_filters=attribute_filters, flag_filters=flag_filters
        ):
            filtered_images.append(copy(this_image))
    return filtered_images
