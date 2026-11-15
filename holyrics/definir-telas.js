// Define qual tela vai mostrar o romaji (a aba 2 da Bíblia).
//
// Rode uma vez em Ferramentas > Script. Ele lista as telas do Holyrics,
// você escolhe a sua, e ela passa a exibir a aba 2 na hora (para testar).
// A escolha fica salva e é usada pelo gatilho romaji-no-retorno.js.

var telas = h.hly('GetDisplaySettings').data;
var itens = [];
for (var i = 0; i < telas.length; i++) {
    var t = telas[i];
    if (t.id == 'public') {
        continue; // o projetor nunca é alterado
    }
    itens.push({
        id: t.id,
        label: t.name + '  [' + t.id + ']  aba atual: ' + t.bible_version_tab
                + (t.hide ? '  (oculta)' : '')
    });
}

if (itens.length == 0) {
    h.ok('O Holyrics só tem a tela público configurada. Configure antes uma '
            + 'tela de retorno para o seu monitor.', 'Romaji no retorno');
} else {
    var escolha = h.itemChooser('Qual tela deve mostrar o romaji?', itens);
    if (escolha != null) {
        h.store('romaji_retorno_tela', escolha.id);
        var r = h.hly('SetDisplaySettings', { id: escolha.id, bible_version_tab: 2 });
        h.ok('Tela escolhida: ' + escolha.label + '\n\nResposta do Holyrics: '
                + h.toJson(r) + '\n\nProjete um versículo: essa tela deve '
                + 'mostrar a versão da aba 2.', 'Romaji no retorno');
    }
}
