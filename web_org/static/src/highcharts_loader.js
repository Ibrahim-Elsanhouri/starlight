import {loadJS} from '@web/core/assets';

let highchartsPromise;

/**
 * Ensure Highcharts + organization module are loaded exactly once.
 * - If Highcharts already exists on window (maybe loaded by another module),
 *   we DO NOT reload highcharts.js.
 * - We only load sankey/organization modules if missing.
 * Returns a Promise<Highcharts>.
 */
export function ensureHighchartsLoaded() {
    if (!highchartsPromise) {
        highchartsPromise = (async () => {
            if (!window.Highcharts) {
                await loadJS('/web_org/static/lib/highcharts/highcharts.js');
            }
            const H = window.Highcharts;
            if (!H) {
                throw new Error('Highcharts did not load correctly.');
            }

            if (!H.seriesTypes || !H.seriesTypes.sankey) {
                await loadJS('/web_org/static/lib/highcharts/sankey.js');
            }

            if (!H.seriesTypes || !H.seriesTypes.organization) {
                await loadJS('/web_org/static/lib/highcharts/organization.js');
            }

            return H;
        })();
    }
    return highchartsPromise;
}
