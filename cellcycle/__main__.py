"""允许通过 python -m cellcycle 运行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
