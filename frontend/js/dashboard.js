/**
 * dashboard.js — Lógica do dashboard principal.
 * 
 * Carrega resumo, gráficos e lista de prioritários.
 */

// Estado dos filtros
let filtros = {
    curso_id: null,
    ano: null,
    semestre: null,
};

/**
 * Inicializa o dashboard.
 */
async function initDashboard() {
    await carregarFiltros();
    await carregarDados();
}

/**
 * Carrega opções dos filtros.
 */
async function carregarFiltros() {
    try {
        const cursos = await apiGet('/cursos');
        const selectCurso = document.getElementById('filtro-curso');
        if (selectCurso) {
            cursos.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.nome;
                selectCurso.appendChild(opt);
            });
        }

        const periodos = await apiGet('/periodos-letivos');
        const selectAno = document.getElementById('filtro-ano');
        if (selectAno) {
            const anos = [...new Set(periodos.map(p => p.ano))].sort((a, b) => b - a);
            anos.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a;
                opt.textContent = a;
                selectAno.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Erro ao carregar filtros:', err);
    }
}

/**
 * Carrega todos os dados do dashboard.
 */
async function carregarDados() {
    showLoading(true);
    try {
        await Promise.all([
            carregarResumo(),
            carregarGraficoClassificacao(),
            carregarHistograma(),
            carregarEvolucao(),
            carregarPrioritarios(),
        ]);
    } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
        showToast('Erro ao carregar dados do dashboard.', 'error');
    }
    showLoading(false);
}

/**
 * Carrega os cards de resumo.
 */
async function carregarResumo() {
    const resumo = await apiGet('/dashboard/resumo', filtros);

    setCardValue('total-estudantes', resumo.total_estudantes);
    setCardValue('total-ok', resumo.total_ok);
    setCardValue('pct-ok', resumo.percentual_ok + '%');
    setCardValue('total-atencao', resumo.total_atencao);
    setCardValue('pct-atencao', resumo.percentual_atencao + '%');
    setCardValue('total-perigo', resumo.total_perigo);
    setCardValue('pct-perigo', resumo.percentual_perigo + '%');
    setCardValue('media-global', formatarNumero(resumo.media_global_geral, 2));
    setCardValue('mediana-global', formatarNumero(resumo.mediana_global, 2));
    setCardValue('freq-media', formatarNumero(resumo.frequencia_media_geral, 1) + '%');
    setCardValue('taxa-reprovacao', formatarNumero(resumo.taxa_reprovacao_media, 1) + '%');
    setCardValue('sem-contato', resumo.sem_contato);
    setCardValue('acomp-atrasados', resumo.acompanhamentos_atrasados);
    setCardValue('curso-perigo', resumo.curso_maior_perigo || '—');
    setCardValue('periodo-risco', resumo.periodo_maior_risco || '—');
}

/**
 * Carrega o gráfico de distribuição de classificações (rosca).
 */
async function carregarGraficoClassificacao() {
    const resumo = await apiGet('/dashboard/resumo', filtros);
    criarGraficoRosca('chart-classificacao', {
        ok: resumo.total_ok,
        atencao: resumo.total_atencao,
        perigo: resumo.total_perigo,
    });
}

/**
 * Carrega o histograma.
 */
async function carregarHistograma() {
    const indicador = document.getElementById('histograma-indicador')?.value || 'media_global';
    const dados = await apiGet('/dashboard/histograma', {
        indicador,
        ...filtros,
    });
    criarHistograma('chart-histograma', dados);

    // Atualiza info do histograma
    const info = document.getElementById('histograma-info');
    if (info) {
        info.innerHTML = `
            <span>Média: <strong>${formatarNumero(dados.media, 2)}</strong></span>
            <span>Mediana: <strong>${formatarNumero(dados.mediana, 2)}</strong></span>
            <span>σ: <strong>${formatarNumero(dados.desvio_padrao, 2)}</strong></span>
        `;
    }
}

/**
 * Carrega o gráfico de evolução.
 */
async function carregarEvolucao() {
    const indicador = document.getElementById('evolucao-indicador')?.value || 'media_global';
    const dados = await apiGet('/dashboard/evolucao', {
        indicador,
        curso_id: filtros.curso_id,
    });
    criarGraficoEvolucao('chart-evolucao', dados);
}

/**
 * Carrega a lista de estudantes prioritários.
 */
async function carregarPrioritarios() {
    try {
        const resultado = await apiGet('/estudantes', {
            risco: 'Perigo',
            ordenar_por: 'probabilidade_risco',
            ordem: 'DESC',
            por_pagina: 6,
        });

        const container = document.getElementById('prioritarios-lista');
        if (!container) return;

        if (!resultado.estudantes || resultado.estudantes.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Nenhum estudante em situação de perigo.</p>';
            return;
        }

        container.innerHTML = resultado.estudantes.map(est => `
            <div class="priority-card animate-fade-in">
                <div class="flex justify-between items-center">
                    <div>
                        <div class="student-name">${est.nome}</div>
                        <div class="student-info">${est.matricula} · ${est.curso_nome || ''} · P${est.periodo_curricular || '?'}</div>
                    </div>
                    <span class="badge badge-${classeRisco(est.classificacao_risco)}">
                        <span class="risk-dot ${classeRisco(est.classificacao_risco)}"></span>
                        ${formatarProbabilidade(est.probabilidade_risco)} ${est.classificacao_risco}
                    </span>
                </div>
                <div class="prob-bar mt-sm">
                    <div class="bar-track">
                        <div class="bar-fill ${classeRisco(est.classificacao_risco)}" 
                             style="width: ${(est.probabilidade_risco || 0) * 100}%"></div>
                    </div>
                </div>
                <div class="student-info mt-sm">
                    Média: ${formatarNumero(est.media_global, 1)} · Freq: ${formatarNumero(est.frequencia_media, 0)}% · 
                    Reprov: ${est.reprovacoes || 0}
                    ${est.ultimo_contato ? ' · Último contato: ' + est.ultimo_contato : ' · <strong style="color: var(--color-atencao)">Sem contato</strong>'}
                </div>
                <div class="priority-actions">
                    <a href="estudante.html?id=${est.id}" class="btn btn-sm btn-primary">📋 Perfil</a>
                    <button class="btn btn-sm btn-secondary" onclick="registrarContato(${est.id})">📞 Contato</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar prioritários:', err);
    }
}

/**
 * Define o valor de um card.
 */
function setCardValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value ?? '—';
}

/**
 * Mostra/esconde indicador de loading.
 */
function showLoading(show) {
    const el = document.getElementById('loading-overlay');
    if (el) el.classList.toggle('hidden', !show);
}

/**
 * Aplica filtros e recarrega.
 */
function aplicarFiltros() {
    filtros.curso_id = document.getElementById('filtro-curso')?.value || null;
    filtros.ano = document.getElementById('filtro-ano')?.value || null;
    filtros.semestre = document.getElementById('filtro-semestre')?.value || null;
    carregarDados();
}

/**
 * Limpa filtros.
 */
function limparFiltros() {
    document.getElementById('filtro-curso').value = '';
    document.getElementById('filtro-ano').value = '';
    document.getElementById('filtro-semestre').value = '';
    filtros = { curso_id: null, ano: null, semestre: null };
    carregarDados();
}

/**
 * Registra contato rápido com estudante.
 */
async function registrarContato(estudanteId) {
    try {
        // Tenta buscar acompanhamento existente
        const acomp = await apiGet(`/acompanhamentos/${estudanteId}`);
        if (acomp.acompanhamento) {
            await apiPut(`/acompanhamentos/${estudanteId}`, {
                ultimo_contato: new Date().toISOString().split('T')[0],
                estudante_contatado: 1,
                situacao_atendimento: 'em_andamento',
            });
        } else {
            await apiPost('/acompanhamentos', {
                ultimo_contato: new Date().toISOString().split('T')[0],
                estudante_contatado: 1,
                situacao_atendimento: 'em_andamento',
            }, { estudante_id: estudanteId });
        }
        showToast('Contato registrado com sucesso!', 'success');
        carregarPrioritarios();
    } catch (err) {
        showToast('Erro ao registrar contato.', 'error');
    }
}

// Inicializa quando a página carregar
document.addEventListener('DOMContentLoaded', initDashboard);
