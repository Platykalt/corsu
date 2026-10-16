/*
 * GitHub adapter: where GitHub's interface is, and where its users' content is.
 *
 * Selectors rely on what GitHub keeps stable across its React rewrites: ARIA landmarks and labels, roles,
 * data-testid and data-component attributes. Its CSS-module class names carry a hash suffix
 * ("sidebarSection__oqw6Y8"), so they are only matched by prefix ([class*="sidebarSection"]).
 * Selectors stay within the subset the Node tests' fake DOM understands: tag, #id, .class, [attr], [attr="v"],
 * [attr^="v"], [attr*="v"], [attr$="v"], compound selectors, the descendant combinator and comma lists.
 * Checked against public pages fetched without login on 2026-10-16 (repository, file view, issues, pull requests,
 * explore); see docs/webext.md.
 */
(function (root) {
    "use strict";
    const adapter = {
        id: "github",
        name: "GitHub",
        hosts: ["github.com"],
        matches: ["https://github.com/*"],
        glossary: "glossary/github.json",

        // Interface zones. Text is translated only inside these, and only when it is an exact glossary label.
        ui: [
            "header[role=\"banner\"]",                       // logged-out marketing header
            "header[aria-label=\"Global navigation menu\"]", // logged-in header
            "[data-testid=\"top-nav-center\"]",
            "[data-testid=\"top-nav-right\"]",
            "nav[aria-label]",                               // Global, Repository, Footer, Pagination, Breadcrumbs...
            "footer[role=\"contentinfo\"]",
            "[data-testid=\"repo-header-actions\"]",         // Star, Fork, Watch
            "[class*=\"sidebarSection\"]",                   // About / Releases / Languages headings and links
            "h2[data-component=\"Heading\"]",
            "h3[data-component=\"Heading\"]",
            "thead",                                         // Name / Last commit message / Last commit date
            "button", "summary",
            "[role=\"button\"]", "[role=\"tab\"]", "[role=\"menu\"]", "[role=\"menuitem\"]", "[role=\"tooltip\"]",
            "[role=\"img\"]", "svg[aria-label]",
            "[data-testid$=\"-anchor-button\"]",             // Labels, Milestones, Projects... on issue lists
            "[data-testid=\"issues-list-surface\"] li[aria-label]",
        ],

        // Search fields: the only elements whose placeholder is translated.
        searchFields: [
            "input[type=\"search\"]",
            "input[role=\"combobox\"]",
            "#query-builder-test",
            "input[name=\"q\"]",
        ],

        // Attributes translated on interface elements (placeholder only on search fields, see above).
        attributes: ["aria-label", "title"],

        // User content: never changed, even when it sits inside an interface zone or equals a glossary label
        // (a README heading "Documentation", a label named "docs", a branch named "Code", a user named "Open").
        never: [
            ".markdown-body",                                // READMEs, issue and comment bodies, wikis
            "article",                                       // README container, explore cards, blog posts
            ".comment-body", ".js-comment-body",
            "[data-testid=\"issue-body\"]", "[data-testid=\"comment-body\"]",
            "[data-testid=\"issue-listitem-title-link\"]", "[data-testid=\"listitem-title-link\"]",
            "[data-testid=\"directory-content\"] tbody",     // file and folder names, commit messages
            "[data-testid=\"latest-commit-details\"]",
            "[data-testid=\"repo-name-wrapper\"]",
            "[data-testid=\"breadcrumbs\"]", "[data-testid=\"breadcrumbs-filename\"]",
            "[data-testid=\"path-name-segment\"]",
            "[data-hovercard-type]",                         // user, organisation, repository and team names
            "[class*=\"IssueLabel\"]",                       // label names chosen by maintainers
            "[class*=\"TopicTag\"]", ".topic-tag",
            "[class*=\"sidebarSection\"] p",                 // repository description
            "[itemprop=\"about\"]",
            ".react-code-lines", ".react-code-text", ".blob-wrapper", ".highlight",
            "[role=\"grid\"]",                               // code view and file tree grids
        ],

        // Interface widgets that GitHub nests inside user content. They must not contain user text themselves.
        uiInsideNever: [
            "clipboard-copy",                                // copy button of code blocks in READMEs
            "[data-testid=\"view-all-files-row\"]",
        ],
    };

    if (typeof module === "object" && module.exports) module.exports = adapter;
    else {
        root.CorsuWeb = root.CorsuWeb || {};
        root.CorsuWeb.adapters = Object.assign(root.CorsuWeb.adapters || {}, { [adapter.id]: adapter });
    }
})(typeof globalThis !== "undefined" ? globalThis : this);
