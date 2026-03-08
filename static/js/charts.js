/* ═══════════════════════════════════════════════════════════════════
   Portfolio Manager — Chart.js Utilities
   ═══════════════════════════════════════════════════════════════════ */

// Shared color palette for charts
const CHART_COLORS = [
    '#6366f1', // indigo
    '#22c55e', // green
    '#f59e0b', // amber
    '#06b6d4', // cyan
    '#ef4444', // red
    '#a855f7', // purple
    '#ec4899', // pink
    '#14b8a6', // teal
    '#f97316', // orange
    '#84cc16', // lime
];

const CHART_DEFAULTS = {
    color: '#94a3b8',
    borderColor: 'rgba(255,255,255,0.06)',
    font: {
        family: "'Inter', sans-serif",
    },
};

// Apply global defaults
Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.font.family = CHART_DEFAULTS.font.family;

/**
 * Create a portfolio growth line chart.
 * @param {string} canvasId - Canvas element ID
 * @param {string[]} labels - Date labels
 * @param {number[]} values - Portfolio values
 */
function createGrowthChart(canvasId, labels, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Create gradient
    const chartCtx = ctx.getContext('2d');
    const gradient = chartCtx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.25)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: '#6366f1',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#6366f1',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a1d29',
                    titleColor: '#e2e8f0',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(ctx) {
                            return '$' + ctx.parsed.y.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                            });
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: CHART_DEFAULTS.borderColor },
                    ticks: {
                        maxTicksLimit: 8,
                        font: { size: 11 },
                    },
                },
                y: {
                    grid: { color: CHART_DEFAULTS.borderColor },
                    ticks: {
                        font: { size: 11 },
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        },
                    },
                },
            },
        },
    });
}

/**
 * Create an asset allocation doughnut chart.
 * @param {string} canvasId - Canvas element ID
 * @param {string[]} labels - Asset symbols
 * @param {number[]} values - Market values
 */
function createAllocationChart(canvasId, labels, values) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: CHART_COLORS.slice(0, labels.length),
                borderColor: '#1a1d29',
                borderWidth: 3,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12, weight: '500' },
                    },
                },
                tooltip: {
                    backgroundColor: '#1a1d29',
                    titleColor: '#e2e8f0',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: function(ctx) {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return ctx.label + ': $' + ctx.parsed.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                            }) + ' (' + pct + '%)';
                        },
                    },
                },
            },
        },
    });
}
