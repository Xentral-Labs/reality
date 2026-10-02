"""Shared bounded pagination metadata."""

from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Page:
    number: int
    size: int
    total: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.size - 1) // self.size)

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.pages

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size


def page_for(total: int, number: int = 1, size: int = DEFAULT_PAGE_SIZE) -> Page:
    safe_size = max(1, min(size, MAX_PAGE_SIZE))
    safe_number = max(1, number)
    page = Page(safe_number, safe_size, total)
    if page.number > page.pages:
        return Page(page.pages, safe_size, total)
    return page
