"""Enable running pdf_extractor as a module."""

import sys

from .converter import main

if __name__ == "__main__":
    sys.exit(main())