import { createContentLoader } from "vitepress";

export type PostLocale = "en" | "de";

export interface BlogPost {
  url: string;
  locale: PostLocale;
  title: string;
  description: string;
  date: string;
  displayDate: string;
  author: string;
  tags: string[];
  order: number;
  draft: boolean;
}

declare const data: BlogPost[];
export { data };

const displayFormat: Record<PostLocale, Intl.DateTimeFormat> = {
  en: new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }),
  de: new Intl.DateTimeFormat("de-DE", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }),
};

// Two posts can share a publication date, because a date is a day and not an instant. `order`
// decides which of them a reader sees first; the url keeps the result stable when neither is set.
const DEFAULT_ORDER = 100;

const comparePosts = (left: BlogPost, right: BlogPost) =>
  Date.parse(right.date) - Date.parse(left.date) ||
  left.order - right.order ||
  left.url.localeCompare(right.url);

const localeOf = (url: string): PostLocale => (url.startsWith("/de/") ? "de" : "en");

const isPost = (url: string) => !/\/blog\/?$/u.test(url);

export default createContentLoader(["blog/*.md", "de/blog/*.md"], {
  transform(entries): BlogPost[] {
    return entries
      .filter((entry) => isPost(entry.url) && entry.frontmatter.date)
      .map((entry) => {
        const locale = localeOf(entry.url);
        const date = new Date(entry.frontmatter.date);
        return {
          url: entry.url,
          locale,
          title: String(entry.frontmatter.title || ""),
          description: String(entry.frontmatter.description || ""),
          date: date.toISOString(),
          displayDate: displayFormat[locale].format(date),
          author: String(entry.frontmatter.author || ""),
          tags: (entry.frontmatter.tags as string[] | undefined) || [],
          order: Number(entry.frontmatter.order ?? DEFAULT_ORDER),
          draft: entry.frontmatter.draft === true,
        };
      })
      .filter((post) => !post.draft)
      .sort(comparePosts);
  },
});
