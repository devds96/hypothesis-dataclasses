"""Executing this script will run `doctest` on the
`hypothesis_dataclasses` package and its modules.
"""

import doctest

from typing import List


FLAGS = (
    doctest.DONT_ACCEPT_TRUE_FOR_1,
)
"""Flags used for doctest."""


def main() -> int:
    """The main function running the doctests."""

    import hypothesis_dataclasses

    from inspect import getmembers, ismodule
    from functools import reduce
    from warnings import catch_warnings, simplefilter
    from hypothesis.errors import NonInteractiveExampleWarning

    with catch_warnings():
        # We are using the .example() method of the hypothesis
        # strategies in the doctests which causes this warning.
        simplefilter("ignore", NonInteractiveExampleWarning)

        options = reduce(lambda a, b: a | b, FLAGS)

        print("Collecting modules.")

        modules = tuple(getmembers(hypothesis_dataclasses, ismodule))
        print("Found modules:", ", ".join(map(lambda nm: nm[0], modules)))

        overall_fails = 0
        overall_attempts = 0
        failed_modules: List[str] = list()
        for name, m in modules:
            results = doctest.testmod(m, verbose=True, optionflags=options)
            failed = results.failed
            if failed > 0:
                failed_modules.append(name)
            overall_fails += failed
            overall_attempts += results.attempted
        if overall_fails > 0:
            print(
                f"Overall {overall_fails} failures in "
                f"{len(failed_modules)} modules (out of {len(modules)} "
                f"modules with {overall_attempts} examples):"
            )
            print(*failed_modules)
            return -1
        print(
            f"Tested {overall_attempts} examples in {len(modules)} "
            "modules; all tests passed."
        )
        return 0


if __name__ == "__main__":
    exit(main())
