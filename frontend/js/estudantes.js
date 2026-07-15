/**
 * estudantes.js — Lógica da tabela de estudantes.
 * 
 * Busca, filtros, ordenação, paginação e exportação CSV.
 */

let estadoTabela = {
    pagina: 1,
    por_pagina: 25,
    ordenar_por: 'probabilidade_risco',
    ordem: 'DESC',
    busca: '',
    curso_id: null,
    risco: null,
    ano: null,
    semestre: null,
};

let todosEstudantes = [];

async function initEstudantes() {
    await carregarFiltrosEstudantes();
    await carregarEstudantes();
}

async function carregarFiltrosEstudantes() {
    try {
        const cursos = await apiGet('/cursos');
        const sel = document.getElementById('filtro-curso-est');
        if (sel) {
            cursos.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.nome;
                sel.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Erro ao carregar filtros:', err);
    }
}

async function carregarEstudantes() {
    const tbody = document.getElementById('tabela-estudantes-body');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="18" class="loading-overlay"><div class="spinner"></div> Carregando...</td></tr>';

    try {
        const resultado = await apiGet('/estudantes', {
            pagina: estadoTabela.pagina,
            por_pagina: estadoTabela.por_pagina,
            ordenar_por: estadoTabela.ordenar_por,
            ordem: estadoTabela.ordem,
            busca: estadoTabela.busca,
            curso_id: estadoTabela.curso_id,
            risco: estadoTabela.risco,
            ano: estadoTabela.ano,
            semestre: estadoTabela.semestre,
        });

        todosEstudantes = resultado.estudantes;
        renderizarTabela(resultado.estudantes);
        renderizarPaginacao(resultado.total);
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="18" class="text-center text-muted">Erro ao carregar estudantes.</td></tr>';
        console.error(err);
    }
}

function renderizarTabela(estudantes) {
    const tbody = document.getElementById('tabela-estudantes-body');
    if (!tbody) return;

    if (!estudantes || estudantes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="18" class="text-center text-muted" style="padding:32px">Nenhum estudante encontrado.</td></tr>';
        return;
    }

    tbody.innerHTML = estudantes.map(est => {
        const riskClass = classeRisco(est.classificacao_risco);
        return `
        <tr class="animate-fade-in" onclick="window.location.href='estudante.html?id=${est.id}'" style="cursor:pointer">
            <td><span class="risk-dot ${riskClass}"></span></td>
            <td><span class="badge badge-${riskClass}">${est.classificacao_risco || '—'}</span></td>
            <td class="font-mono"><strong>${formatarProbabilidade(est.probabilidade_risco)}</strong></td>
            <td class="font-mono">${est.matricula}</td>
            <td><strong>${est.nome}</strong></td>
            <td class="text-muted">${est.telefone || '—'}</td>
            <td>${est.curso_nome || '—'}</td>
            <td class="text-center">P${est.periodo_curricular || '?'}</td>
            <td class="text-center">${formatarNumero(est.media_global, 1)}</td>
            <td class="text-center">${formatarNumero(est.media_semestre, 1)}</td>
            <td class="text-center">${formatarNumero(est.frequencia_media, 0)}%</td>
            <td class="text-center">${est.reprovacoes ?? 0}</td>
            <td class="text-center">${est.reprovacoes_sucessivas ?? 0}</td>
            <td class="text-center">${formatarNumero(est.percentual_integralizacao, 0)}%</td>
            <td class="text-center">${formatarNumero(est.distancia_km, 1)} km</td>
            <td><span class="badge badge-neutro">${est.situacao_atendimento || 'pendente'}</span></td>
            <td class="text-muted">${est.funcionario_responsavel || '—'}</td>
            <td class="text-muted">${est.ultimo_contato || '—'}</td>
        </tr>`;
    }).join('');
}

function renderizarPaginacao(total) {
    const container = document.getElementById('paginacao');
    if (!container) return;

    const totalPaginas = Math.ceil(total / estadoTabela.por_pagina);
    const pagina = estadoTabela.pagina;

    let html = `<span class="page-info">Mostrando ${((pagina-1)*estadoTabela.por_pagina)+1}–${Math.min(pagina*estadoTabela.por_pagina, total)} de ${total}</span>`;
    html += '<div class="page-buttons">';
    html += `<button class="page-btn" onclick="irParaPagina(1)" ${pagina === 1 ? 'disabled' : ''}>«</button>`;
    html += `<button class="page-btn" onclick="irParaPagina(${pagina-1})" ${pagina === 1 ? 'disabled' : ''}>‹</button>`;

    const inicio = Math.max(1, pagina - 2);
    const fim = Math.min(totalPaginas, pagina + 2);
    for (let i = inicio; i <= fim; i++) {
        html += `<button class="page-btn ${i === pagina ? 'active' : ''}" onclick="irParaPagina(${i})">${i}</button>`;
    }

    html += `<button class="page-btn" onclick="irParaPagina(${pagina+1})" ${pagina >= totalPaginas ? 'disabled' : ''}>›</button>`;
    html += `<button class="page-btn" onclick="irParaPagina(${totalPaginas})" ${pagina >= totalPaginas ? 'disabled' : ''}>»</button>`;
    html += '</div>';

    container.innerHTML = html;
}

function irParaPagina(p) {
    if (p < 1) return;
    estadoTabela.pagina = p;
    carregarEstudantes();
}

function ordenarPor(campo) {
    if (estadoTabela.ordenar_por === campo) {
        estadoTabela.ordem = estadoTabela.ordem === 'ASC' ? 'DESC' : 'ASC';
    } else {
        estadoTabela.ordenar_por = campo;
        estadoTabela.ordem = 'DESC';
    }
    estadoTabela.pagina = 1;
    carregarEstudantes();
    atualizarIconesOrdenacao();
}

function atualizarIconesOrdenacao() {
    document.querySelectorAll('thead th[data-sort]').forEach(th => {
        th.classList.remove('sorted');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = '';
        if (th.dataset.sort === estadoTabela.ordenar_por) {
            th.classList.add('sorted');
            if (icon) icon.textContent = estadoTabela.ordem === 'ASC' ? '▲' : '▼';
        }
    });
}

function aplicarFiltrosEstudantes() {
    estadoTabela.curso_id = document.getElementById('filtro-curso-est')?.value || null;
    estadoTabela.risco = document.getElementById('filtro-risco')?.value || null;
    estadoTabela.pagina = 1;
    carregarEstudantes();
}

function buscarEstudantes() {
    estadoTabela.busca = document.getElementById('busca-estudante')?.value || '';
    estadoTabela.pagina = 1;
    carregarEstudantes();
}

const buscarDebounced = debounce(buscarEstudantes, 400);

function exportarDados() {
    if (todosEstudantes.length === 0) {
        showToast('Nenhum dado para exportar. Carregue os estudantes primeiro.', 'error');
        return;
    }
    exportarCSV(todosEstudantes, 'estudantes_ufrpe.csv');
}

function limparFiltrosEstudantes() {
    document.getElementById('filtro-curso-est').value = '';
    document.getElementById('filtro-risco').value = '';
    document.getElementById('busca-estudante').value = '';
    estadoTabela = { ...estadoTabela, busca: '', curso_id: null, risco: null, pagina: 1 };
    carregarEstudantes();
}

document.addEventListener('DOMContentLoaded', initEstudantes);
