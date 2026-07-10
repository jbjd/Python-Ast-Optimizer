from unittest.mock import patch

from personal_python_ast_optimizer.config import OptimizeConfig, TokensToSkipConfig
from personal_python_ast_optimizer.run import optimize_source_and_minify


# TODO: Flush out with all tokens that can be skipped when I implement them all
def test_warn_unused_skips() -> None:
    no_warn_source: str = "class DEF(ABC):pass\na=1"

    warn_source: str = "a=1"

    with patch(
        "personal_python_ast_optimizer._optimize.utils._logger.warning"
    ) as mock_logger_warning:
        config = OptimizeConfig(
            tokens_to_skip=TokensToSkipConfig(classes_to_skip={"ABC"})
        )

        optimize_source_and_minify(no_warn_source, config)
        mock_logger_warning.assert_not_called()

        optimize_source_and_minify(warn_source, config)
        mock_logger_warning.assert_called_once()
