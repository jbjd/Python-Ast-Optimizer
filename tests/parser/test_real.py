"""Real cases of minified code that broken at some point.
They are added here to ensure regression does not occur."""

from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


def test_image_viewer_constants():
    before_and_after = BeforeAndAfter(
        """
\"\"\"
File with constants needed in multiple spots of the codebase
\"\"\"

from enum import StrEnum


class ImageFormats(StrEnum):
    \"\"\"Image format strings that this app supports\"\"\"

    DDS = "DDS"
    GIF = "GIF"
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WebP\"""",
        """from enum import StrEnum
class ImageFormats(StrEnum):DDS='DDS';GIF='GIF';JPEG='JPEG';PNG='PNG';WEBP='WebP'""",
    )
    optimize_and_assert_correctness(before_and_after)
