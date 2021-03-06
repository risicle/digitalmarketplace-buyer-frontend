// files are loaded from the /spec/javascripts/support folder so paths are relative to that
var manifest = {
  support : [
    '../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/analytics/google-analytics-universal-tracker.js',
    '../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/analytics/analytics.js',
    '../../../app/assets/javascripts/analytics/_dm-analytics.js'
  ],
  test : [
    '../unit/AnalyticsSpec.js'
  ]
};

if (typeof exports !== 'undefined') {
  exports.manifest = manifest;
}
