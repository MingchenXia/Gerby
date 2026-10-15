const destination = new URL(document.documentElement.dataset.redirect, location.href);
const fragments = JSON.parse(document.documentElement.dataset.fragments || '{}');
const fragment = decodeURIComponent(location.hash.slice(1));
if (fragment && fragments[fragment]) destination.hash = fragments[fragment];
location.replace(destination.href);
