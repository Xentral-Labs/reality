"""Storyline mode (spec 182): declarative story packages played through the ordinary
proposal path, with a call trace and a delta read that explain each chapter.

Nothing in this package writes business data by itself. Chapters run the same
commands the app, the CLI and MCP run; the package only says which ones and why.
"""
