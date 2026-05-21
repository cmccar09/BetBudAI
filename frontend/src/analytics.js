const GA_MEASUREMENT_ID = process.env.REACT_APP_GA_MEASUREMENT_ID || '';

let analyticsInitialized = false;

function hasAnalytics() {
  return typeof window !== 'undefined' && !!GA_MEASUREMENT_ID;
}

function ensureDataLayer() {
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments);
  };
}

export function initAnalytics() {
  if (!hasAnalytics() || analyticsInitialized) return;

  ensureDataLayer();

  if (!document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}"]`)) {
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
    document.head.appendChild(script);
  }

  window.gtag('js', new Date());
  window.gtag('config', GA_MEASUREMENT_ID, {
    send_page_view: false,
    anonymize_ip: true,
  });

  analyticsInitialized = true;
}

export function trackEvent(eventName, params = {}) {
  if (!hasAnalytics()) return;
  ensureDataLayer();
  window.gtag('event', eventName, params);
}

export function trackPageView(pageKey, params = {}) {
  if (!hasAnalytics()) return;
  ensureDataLayer();

  const pagePath = params.page_path || window.location.pathname;
  const pageLocation = `${window.location.origin}${pagePath}`;

  window.gtag('event', 'page_view', {
    page_title: params.page_title || pageKey,
    page_path: pagePath,
    page_location: pageLocation,
    app_page: pageKey,
    user_status: params.user_status || 'guest',
  });
}

export function analyticsEnabled() {
  return !!GA_MEASUREMENT_ID;
}
