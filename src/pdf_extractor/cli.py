#!/usr/bin/env python3
"""Command-line interface for PDF Extractor."""

import sys

from .converter import main

if __name__ == "__main__":
    sys.exit(main())