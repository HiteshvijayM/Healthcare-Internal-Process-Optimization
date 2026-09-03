"""DETERMINISTIC decision functions.

This package must not import ``extraction`` or ``drafting``. The boundary is the
single mechanism protecting P7 determinism and FR-017 inspectability at once, and
it is enforced by a contract test that scans the AST rather than by convention.
"""
