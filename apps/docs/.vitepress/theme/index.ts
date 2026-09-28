import { h } from "vue";
import LanguageBridge from "./components/LanguageBridge.vue";
import GlobalAskReality from "./components/GlobalAskReality.vue";
import DefaultTheme from "vitepress/theme";
import PostList from "./components/PostList.vue";
import PostMeta from "./components/PostMeta.vue";
import Subscribe from "./components/Subscribe.vue";
import ProductLink from "./components/ProductLink.vue";
import ToolUsage from "./components/ToolUsage.vue";
import BusinessJourneyGuide from "./components/BusinessJourneyGuide.vue";
import "./custom.css";
import "./tool-usage.css";

export default {
  extends: DefaultTheme,
  Layout: () =>
    h(DefaultTheme.Layout, null, {
      "layout-top": () => h(LanguageBridge),
      "layout-bottom": () => h(GlobalAskReality),
    }),
  enhanceApp({ app }: { app: import("vue").App }) {
    app.component("PostList", PostList);
    app.component("PostMeta", PostMeta);
    app.component("Subscribe", Subscribe);
    app.component("ProductLink", ProductLink);
    app.component("ToolUsage", ToolUsage);
    app.component("BusinessJourneyGuide", BusinessJourneyGuide);
  },
};
