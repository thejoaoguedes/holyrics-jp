// Romaji na tela de retorno só quando a Bíblia projetada é a japonesa.
//
// O script não mexe nas abas da Bíblia. Ele só lê a versão que está na
// aba 1 (a projetada) e escolhe a aba que a tela de retorno exibe:
//   - aba 1 = JA1955: retorno exibe a aba 2 (onde fica a JA1955ROM);
//   - aba 1 = qualquer outra versão: retorno exibe a aba 1.
//
// A tela de retorno é a escolhida com definir-telas.js; sem escolha, vale
// para todas as telas "screen_*".
//
// Use como ação de um gatilho "ao exibir > qualquer versículo" (veja o
// README). Roda um instante depois da exibição e só altera a tela quando
// precisa mudar.

h.setTimeout(function () {
    try {
        var version = String(h.hly('GetBibleSettings').data.tab_version_1 || '');
        var isJapanese = /^ja/i.test(version) && !/rom/i.test(version);
        var wanted = isJapanese ? 2 : 1;
        var chosen = h.restore('romaji_retorno_tela', null);

        var displays = h.hly('GetDisplaySettings').data;
        for (var i = 0; i < displays.length; i++) {
            var d = displays[i];
            var isTarget = chosen ? d.id == chosen : /^screen_/.test(d.id);
            if (isTarget && Number(d.bible_version_tab) != wanted) {
                h.hly('SetDisplaySettings', { id: d.id, bible_version_tab: wanted });
                h.log('romaji-no-retorno: ' + d.name + ' -> aba ' + wanted
                        + ' (aba 1 = ' + version + ')');
            }
        }
    } catch (e) {
        h.log('romaji-no-retorno: erro: ' + e);
    }
}, 300, 'romaji-no-retorno');
