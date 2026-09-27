// Reads the shell makes on every page (interaction pulse, report templates for the command
// palette, the Inbox decision count). Strict fixtures that refuse unknown requests answer
// these without making them part of the page under test.
const SUFFIXES = ["/interactions/pulse", "/analytics/graph/templates", "/change-proposals"];
export const isShellBackgroundRead = (method, path) =>
  method === "GET" && SUFFIXES.some((suffix) => path.endsWith(suffix));
// Company search (query and resolve) is a POST read the server admits as one, not a write.
export const isSearchRead = (path) => /\/search\/(query|resolve)$/.test(path);
