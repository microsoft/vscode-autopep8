# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Utility functions for calculating edits."""


import bisect
import difflib
from typing import List

from lsprotocol import types as lsp


def get_text_edits(old_text: str, new_text: str) -> List[lsp.TextEdit]:
    """Return a list of text edits to transform old_text into new_text."""
    offsets = [0]
    old_text_lines = old_text.splitlines(keepends=True)
    new_text_lines = new_text.splitlines(keepends=True)

    line_dist = abs(len(new_text_lines) - len(old_text_lines))
    char_dist = abs(len(new_text) - len(old_text))

    if line_dist > 200 or char_dist > 500:
        # Too many edits, just return a single edit.
        return [
            lsp.TextEdit(
                range=lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(len(old_text_lines), 0)),
                new_text=new_text,
            )
        ]

    for line in old_text_lines:
        offsets.append(offsets[-1] + len(line))

    def from_offset(offset: int) -> lsp.Position:
        line = bisect.bisect_right(offsets, offset) - 1
        character = offset - offsets[line]
        return lsp.Position(line=line, character=character)

    sequences = difflib.SequenceMatcher(a=old_text, b=new_text).get_opcodes()
    edits = [
        lsp.TextEdit(
            range=lsp.Range(start=from_offset(old_start), end=from_offset(old_end)),
            new_text=new_text[new_start:new_end],
        )
        for opcode, old_start, old_end, new_start, new_end in sequences
        if opcode != "equal"
    ]
    return edits
