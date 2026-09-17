// Globals injected by the Flask Jinja template (static/index.html) and by
// the GitHub Pages static templates (static/gh-pages/index.html, 404.html)
// before this bundle is loaded. See server/app.py for the Flask side.
export {};

declare module '*.css';

declare global {
  interface UrlFor {
    root: string;
    los: string;
    solve: string;
    views: string;
  }

  // eslint-disable-next-line no-var
  var URL_FOR: UrlFor;
  var PY_SOURCE_BASE: string;
  var DEVELOPMENT: boolean;
  var APP_NAME: string;
  var APP_VERSION: string;
  var DATA_VERSION: string;
  var DATA_VERSION_MAJOR: number;
  var DATA_VERSION_MINOR: number;
  var DATA_VERSION_BUILD: number;
  var START_IN_LOS_MODE: string;
}
