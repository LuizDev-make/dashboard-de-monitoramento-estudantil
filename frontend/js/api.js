/**
 * api.js — Wrapper centralizado para chamadas à API REST.
 * 
 * Todas as requisições ao backend passam por este módulo,
 * garantindo tratamento de erros e URL base consistentes.
 */

const API_BASE = '/api';

/**
 * Realiza uma requisição GET à API.
 * @param {string} endpoint - Caminho do endpoint (ex: '/estudantes')
 * @param {Object} params - Parâmetros de query string
 * @returns {Promise<Object>} Dados da resposta
 */
async function apiGet(endpoint, params = {}) {
    const url = new URL(API_BASE + endpoint, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
            url.searchParams.append(key, value);
        }
    });

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Erro ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API GET ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Realiza uma requisição POST à API.
 * @param {string} endpoint - Caminho do endpoint
 * @param {Object} body - Corpo da requisição (JSON)
 * @param {Object} params - Parâmetros de query string
 * @returns {Promise<Object>} Dados da resposta
 */
async function apiPost(endpoint, body = {}, params = {}) {
    const url = new URL(API_BASE + endpoint, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
            url.searchParams.append(key, value);
        }
    });

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Erro ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API POST ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Realiza uma requisição PUT à API.
 * @param {string} endpoint - Caminho do endpoint
 * @param {Object} body - Corpo da requisição (JSON)
 * @returns {Promise<Object>} Dados da resposta
 */
async function apiPut(endpoint, body = {}) {
    try {
        const response = await fetch(API_BASE + endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Erro ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API PUT ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Upload de arquivo via POST multipart.
 * @param {string} endpoint - Caminho do endpoint
 * @param {File} file - Arquivo para upload
 * @returns {Promise<Object>} Resultado da importação
 */
async function apiUpload(endpoint, file) {
    const formData = new FormData();
    formData.append('arquivo', file);

    try {
        const response = await fetch(API_BASE + endpoint, {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Erro ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API UPLOAD ${endpoint}:`, error);
        throw error;
    }
}

/* ============================================================
   Utilitários
   ============================================================ */

/**
 * Formata probabilidade para exibição.
 * @param {number} prob - Probabilidade (0-1)
 * @returns {string} Ex: "87,42%"
 */
function formatarProbabilidade(prob) {
    if (prob === null || prob === undefined) return '—';
    return (prob * 100).toFixed(2).replace('.', ',') + '%';
}

/**
 * Retorna a classe CSS da classificação de risco.
 * @param {string} classificacao - 'OK', 'Atenção' ou 'Perigo'
 * @returns {string} Classe CSS
 */
function classeRisco(classificacao) {
    switch (classificacao) {
        case 'OK': return 'ok';
        case 'Atenção': return 'atencao';
        case 'Perigo': return 'perigo';
        default: return 'neutro';
    }
}

/**
 * Formata número para exibição brasileira.
 * @param {number} valor - Valor numérico
 * @param {number} decimais - Casas decimais
 * @returns {string} Número formatado
 */
function formatarNumero(valor, decimais = 1) {
    if (valor === null || valor === undefined) return '—';
    return Number(valor).toFixed(decimais).replace('.', ',');
}

/**
 * Mostra uma notificação toast.
 * @param {string} mensagem - Texto da mensagem
 * @param {string} tipo - 'success', 'error' ou 'info'
 */
function showToast(mensagem, tipo = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[tipo] || 'ℹ️'}</span><span>${mensagem}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Exporta dados para CSV.
 * @param {Array<Object>} dados - Array de objetos
 * @param {string} nomeArquivo - Nome do arquivo
 */
function exportarCSV(dados, nomeArquivo = 'exportacao.csv') {
    if (!dados || dados.length === 0) {
        showToast('Nenhum dado para exportar.', 'error');
        return;
    }

    const colunas = Object.keys(dados[0]);
    const linhas = [
        colunas.join(';'),
        ...dados.map(row =>
            colunas.map(col => {
                let val = row[col];
                if (val === null || val === undefined) val = '';
                val = String(val).replace(/"/g, '""');
                return `"${val}"`;
            }).join(';')
        ),
    ];

    const blob = new Blob(['\uFEFF' + linhas.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nomeArquivo;
    link.click();
    URL.revokeObjectURL(url);
    showToast('Arquivo CSV exportado com sucesso!', 'success');
}

/**
 * Debounce para busca.
 */
function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}
