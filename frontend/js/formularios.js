/**
 * formularios.js — Lógica de formulários e edição de acompanhamentos.
 * 
 * Modais, edição de acompanhamento, registro de contato.
 */

/**
 * Abre o modal de edição de acompanhamento.
 */
function abrirModalAcompanhamento(estudanteId) {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
        overlay.classList.add('active');
        overlay.dataset.estudanteId = estudanteId;
        carregarDadosAcompanhamento(estudanteId);
    }
}

/**
 * Fecha o modal.
 */
function fecharModal() {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.remove('active');
}

/**
 * Carrega dados do acompanhamento no formulário.
 */
async function carregarDadosAcompanhamento(estudanteId) {
    try {
        const resultado = await apiGet(`/acompanhamentos/${estudanteId}`);
        const acomp = resultado.acompanhamento;

        if (acomp) {
            setFormValue('form-responsavel', acomp.funcionario_responsavel);
            setFormValue('form-situacao', acomp.situacao_atendimento);
            setFormValue('form-prioridade', acomp.prioridade_manual);
            setFormValue('form-observacao', acomp.observacao);
            setFormValue('form-encaminhamento', acomp.encaminhamento);
            setFormValue('form-data-contato', acomp.data_prevista_contato);
            setFormValue('form-acao', acomp.acao_realizada);
        }
    } catch (err) {
        console.error('Erro ao carregar acompanhamento:', err);
    }
}

/**
 * Salva dados do acompanhamento.
 */
async function salvarAcompanhamento() {
    const overlay = document.getElementById('modal-overlay');
    const estudanteId = overlay?.dataset.estudanteId;
    if (!estudanteId) return;

    const dados = {
        funcionario_responsavel: document.getElementById('form-responsavel')?.value || null,
        situacao_atendimento: document.getElementById('form-situacao')?.value || 'pendente',
        prioridade_manual: parseInt(document.getElementById('form-prioridade')?.value || '0'),
        observacao: document.getElementById('form-observacao')?.value || null,
        encaminhamento: document.getElementById('form-encaminhamento')?.value || null,
        data_prevista_contato: document.getElementById('form-data-contato')?.value || null,
        acao_realizada: document.getElementById('form-acao')?.value || null,
    };

    try {
        // Tenta atualizar primeiro
        const acomp = await apiGet(`/acompanhamentos/${estudanteId}`);
        if (acomp.acompanhamento) {
            await apiPut(`/acompanhamentos/${estudanteId}`, dados);
        } else {
            await apiPost('/acompanhamentos', dados, { estudante_id: estudanteId });
        }
        showToast('Acompanhamento salvo com sucesso!', 'success');
        fecharModal();
        // Recarrega dados se estiver na página de perfil
        if (typeof carregarPerfil === 'function') {
            carregarPerfil();
        }
    } catch (err) {
        showToast('Erro ao salvar acompanhamento: ' + err.message, 'error');
    }
}

/**
 * Define valor de um campo de formulário.
 */
function setFormValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
}

/**
 * Fecha modal ao clicar fora.
 */
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal();
    }
});

/**
 * Fecha modal com ESC.
 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') fecharModal();
});
