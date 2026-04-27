document.addEventListener("DOMContentLoaded", function () {
    // ==============================
    // CAMPOS DE NOMENCLATURA / ABREVIAÇÃO
    // ==============================
    const padraoNomenclatura = document.getElementById("padrao_nomenclatura");
    const grupoArquivoNomenclatura = document.getElementById("grupo_arquivo_nomenclatura");

    const padraoAbreviacao = document.getElementById("padrao_abreviacao");
    const grupoArquivoAbreviacao = document.getElementById("grupo_arquivo_abreviacao");

    function controlarCampos() {
        if (padraoNomenclatura && grupoArquivoNomenclatura) {
            if (padraoNomenclatura.value === "sim") {
                grupoArquivoNomenclatura.classList.remove("hidden");
            } else {
                grupoArquivoNomenclatura.classList.add("hidden");
            }
        }

        if (padraoAbreviacao && grupoArquivoAbreviacao) {
            if (padraoAbreviacao.value === "sim") {
                grupoArquivoAbreviacao.classList.remove("hidden");
            } else {
                grupoArquivoAbreviacao.classList.add("hidden");
            }
        }
    }

    if (padraoNomenclatura) {
        padraoNomenclatura.addEventListener("change", controlarCampos);
    }

    if (padraoAbreviacao) {
        padraoAbreviacao.addEventListener("change", controlarCampos);
    }

    controlarCampos();

    // ==============================
    // BOTÃO GERAR MODELO (LOADING)
    // ==============================
    const formGerar = document.getElementById("form-gerar-modelo");
    const btnGerar = document.getElementById("btn-gerar-modelo");

    if (formGerar && btnGerar) {
        formGerar.addEventListener("submit", function () {
            btnGerar.disabled = true;
            btnGerar.innerText = "Gerando...";
            btnGerar.style.opacity = "0.7";
            btnGerar.style.cursor = "not-allowed";
        });
    }

    // ==============================
    // MODAL DO PLANO
    // ==============================
    const modalPlano = document.getElementById("modal-plano");
    const btnFecharModalPlano = document.getElementById("btn-fechar-modal-plano");

    if (modalPlano && btnFecharModalPlano) {
        btnFecharModalPlano.addEventListener("click", function () {
            modalPlano.style.display = "none";
        });
    }

    // ==============================
    // MOSTRAR / OCULTAR HISTÓRICO
    // ==============================
    const btnHistorico = document.getElementById("btn-toggle-historico");
    const historicoContainer = document.getElementById("historico-container");

    if (btnHistorico && historicoContainer) {
        btnHistorico.addEventListener("click", function () {
            const estaOculto =
                historicoContainer.style.display === "none" ||
                historicoContainer.style.display === "";

            if (estaOculto) {
                historicoContainer.style.display = "block";
                btnHistorico.innerText = "Ocultar histórico";
            } else {
                historicoContainer.style.display = "none";
                btnHistorico.innerText = "Ver histórico";
            }
        });
    }

    // ==============================
    // VER / OCULTAR RESPOSTA
    // ==============================
    const botoesResposta = document.querySelectorAll(".btn-toggle-resposta");

    botoesResposta.forEach((botao) => {
        botao.addEventListener("click", function () {
            const resposta = botao.nextElementSibling;
            if (!resposta) return;

            const estaOculta =
                resposta.style.display === "none" || resposta.style.display === "";

            if (estaOculta) {
                resposta.style.display = "block";
                botao.innerText = "Ocultar resposta";
            } else {
                resposta.style.display = "none";
                botao.innerText = "Ver resposta";
            }
        });
    });

        // ==============================
    // FILTRO DO HISTÓRICO
    // ==============================
    const filtroHistorico = document.getElementById("filtro-historico");

    if (filtroHistorico) {
        filtroHistorico.addEventListener("change", function () {
            const valorSelecionado = filtroHistorico.value;
            window.location.href = `/dashboard?page=1&mostrar_historico=1&filtro_historico=${valorSelecionado}`;
        });
    }

        // ==============================
    // PAGINAÇÃO DO HISTÓRICO COM FILTRO ATUAL
    // ==============================
    const btnPaginaAnterior = document.getElementById("btn-pagina-anterior");
    const btnPaginaProxima = document.getElementById("btn-pagina-proxima");
    const filtroHistoricoAtual = document.getElementById("filtro-historico");

    function navegarHistoricoComFiltro(event, botao) {
        if (!botao) return;

        event.preventDefault();

        const page = botao.getAttribute("data-page");
        const filtro = filtroHistoricoAtual ? filtroHistoricoAtual.value : "todos";

        window.location.href = `/dashboard?page=${page}&mostrar_historico=1&filtro_historico=${filtro}`;
    }

    if (btnPaginaAnterior) {
        btnPaginaAnterior.addEventListener("click", function (event) {
            navegarHistoricoComFiltro(event, btnPaginaAnterior);
        });
    }

    if (btnPaginaProxima) {
        btnPaginaProxima.addEventListener("click", function (event) {
            navegarHistoricoComFiltro(event, btnPaginaProxima);
        });
    }
});

