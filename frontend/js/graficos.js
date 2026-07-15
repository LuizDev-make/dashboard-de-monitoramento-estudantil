/**
 * graficos.js — Configurações e criação de gráficos com Chart.js.
 * 
 * Todos os gráficos usam o tema dark com cores HSL consistentes.
 */

// Configuração global do Chart.js para tema dark
Chart.defaults.color = 'hsl(220, 15%, 65%)';
Chart.defaults.borderColor = 'hsla(220, 15%, 30%, 0.3)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.animation.duration = 800;
Chart.defaults.animation.easing = 'easeOutQuart';

// Paleta de cores
const CORES = {
    ok: 'hsl(152, 68%, 45%)',
    okAlpha: 'hsla(152, 68%, 45%, 0.2)',
    atencao: 'hsl(42, 95%, 55%)',
    atencaoAlpha: 'hsla(42, 95%, 55%, 0.2)',
    perigo: 'hsl(0, 78%, 55%)',
    perigoAlpha: 'hsla(0, 78%, 55%, 0.2)',
    primary: 'hsl(215, 90%, 60%)',
    primaryAlpha: 'hsla(215, 90%, 60%, 0.2)',
    secondary: 'hsl(270, 70%, 65%)',
    secondaryAlpha: 'hsla(270, 70%, 65%, 0.2)',
    grid: 'hsla(220, 15%, 30%, 0.15)',
};

// Armazena instâncias de gráficos para destruição
const chartInstances = {};

/**
 * Destrói um gráfico existente antes de recriar.
 */
function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }
}

/**
 * Cria um gráfico de rosca (distribuição de classificações).
 */
function criarGraficoRosca(canvasId, dados) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['OK', 'Atenção', 'Perigo'],
            datasets: [{
                data: [dados.ok || 0, dados.atencao || 0, dados.perigo || 0],
                backgroundColor: [CORES.ok, CORES.atencao, CORES.perigo],
                borderColor: 'transparent',
                borderWidth: 0,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                            return ` ${ctx.label}: ${ctx.raw} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}

/**
 * Cria um histograma interativo.
 */
function criarHistograma(canvasId, dados) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = [];
    for (let i = 0; i < dados.bins.length - 1; i++) {
        labels.push(`${dados.bins[i].toFixed(1)}-${dados.bins[i+1].toFixed(1)}`);
    }

    // Linhas de referência (média, mediana, desvios)
    const annotations = {};
    if (dados.media !== undefined) {
        annotations.mediaLine = {
            type: 'line',
            xMin: dados.media,
            xMax: dados.media,
            borderColor: CORES.primary,
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
                display: true,
                content: `Média: ${dados.media.toFixed(2)}`,
                position: 'start',
            },
        };
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: dados.indicador || 'Distribuição',
                data: dados.contagens,
                backgroundColor: CORES.primaryAlpha,
                borderColor: CORES.primary,
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: CORES.primary,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (ctx) => ` ${ctx.raw} estudantes`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: CORES.grid },
                    ticks: { maxRotation: 45 },
                },
                y: {
                    grid: { color: CORES.grid },
                    beginAtZero: true,
                    ticks: { precision: 0 },
                },
            },
        },
    });
}

/**
 * Cria um gráfico de evolução (linha temporal).
 */
function criarGraficoEvolucao(canvasId, dados) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.periodos,
            datasets: [{
                label: dados.indicador || 'Evolução',
                data: dados.valores,
                borderColor: CORES.primary,
                backgroundColor: CORES.primaryAlpha,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: CORES.primary,
                pointBorderColor: 'hsl(225, 25%, 8%)',
                pointBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: { grid: { color: CORES.grid } },
                y: {
                    grid: { color: CORES.grid },
                    beginAtZero: false,
                },
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        },
    });
}

/**
 * Cria gráfico de barras (classificação por curso).
 */
function criarGraficoBarras(canvasId, labels, datasets) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
            },
            scales: {
                x: {
                    grid: { color: CORES.grid },
                    stacked: true,
                },
                y: {
                    grid: { color: CORES.grid },
                    stacked: true,
                    beginAtZero: true,
                    ticks: { precision: 0 },
                },
            },
        },
    });
}

/**
 * Cria gráfico de evolução do estudante (múltiplas linhas).
 */
function criarGraficoEvolucaoEstudante(canvasId, evolucao) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: evolucao.periodos,
            datasets: [
                {
                    label: 'Média Global',
                    data: evolucao.medias_globais,
                    borderColor: CORES.primary,
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    pointRadius: 3,
                    yAxisID: 'y',
                },
                {
                    label: 'Frequência (%)',
                    data: evolucao.frequencias,
                    borderColor: CORES.secondary,
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    pointRadius: 3,
                    yAxisID: 'y1',
                },
                {
                    label: 'Probabilidade Risco',
                    data: evolucao.probabilidades ? evolucao.probabilidades.map(p => p !== null ? p * 100 : null) : [],
                    borderColor: CORES.perigo,
                    backgroundColor: CORES.perigoAlpha,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: { legend: { position: 'bottom' } },
            scales: {
                x: { grid: { color: CORES.grid } },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: CORES.grid },
                    min: 0,
                    max: 10,
                    title: { display: true, text: 'Média' },
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    min: 0,
                    max: 100,
                    title: { display: true, text: '% / Frequência' },
                },
            },
        },
    });
}
