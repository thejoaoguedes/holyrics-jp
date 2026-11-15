// Romaji na tela de retorno só quando a Bíblia projetada é a japonesa.
//
// O script não mexe nas abas da Bíblia. Ele só lê a versão que está na
// aba 1 (a projetada) e escolhe a aba que as telas de retorno exibem:
//   - aba 1 = JA1955: retorno exibe a aba 2 (onde fica a JA1955ROM);
//   - aba 1 = qualquer outra versão: retorno exibe a aba 1.
//
// Use como ação de um gatilho "ao exibir > qualquer versículo" (veja o
// README). Roda um instante depois da exibição e só altera a tela de
// retorno quando precisa mudar.

h.setTimeout(function () {
    try {
        var version = String(h.hly('GetBibleSettings').data.tab_version_1 || '');
        var isJapanese = /^ja/i.test(version) && !/rom/i.test(version);
        var wanted = isJapanese ? 2 : 1;

        var displays = h.hly('GetDisplaySettings').data;
        for (var i = 0; i < displays.length; i++) {
            var d = displays[i];
            if (/^screen_/.test(d.id) && Number(d.bible_version_tab) != wanted) {
                h.hly('SetDisplaySettings', { id: d.id, bible_version_tab: wanted });
                h.log('romaji-no-retorno: ' + d.name + ' -> aba ' + wanted
                        + ' (aba 1 = ' + version + ')');
            }
        }
    } catch (e) {
        h.log('romaji-no-retorno: erro: ' + e);
    }
}, 300, 'romaji-no-retorno');
