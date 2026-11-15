// Romaji na tela de retorno só quando a Bíblia projetada é a japonesa.
//
// As versões das abas não são alteradas. Exemplo de uso:
//   aba 1 = ARC, aba 2 = JA1955ROM, aba 3 = JA1955
//
// O script olha qual versão o projetor está exibindo:
//   - JA1955: as telas de retorno passam a exibir a aba da JA1955ROM;
//   - qualquer outra: as telas de retorno exibem a mesma aba do projetor.
//
// Use como ação de um gatilho "ao exibir > qualquer versículo" (veja o
// README). Roda um instante depois da exibição e só altera a tela de
// retorno quando precisa mudar.

h.setTimeout(function () {
    try {
        var bible = h.hly('GetBibleSettings').data;
        var tabs = [null, bible.tab_version_1, bible.tab_version_2, bible.tab_version_3];

        var isRomaji = function (id) { return /rom/i.test(String(id || '')); };
        var isJapanese = function (id) {
            return /^ja/i.test(String(id || '')) && !isRomaji(id);
        };

        var romajiTab = 0;
        for (var t = 1; t <= 3; t++) {
            if (isRomaji(tabs[t])) {
                romajiTab = t;
                break;
            }
        }

        var displays = h.hly('GetDisplaySettings').data;
        var publicTab = 1;
        for (var i = 0; i < displays.length; i++) {
            if (displays[i].id == 'public') {
                publicTab = Number(displays[i].bible_version_tab) || 1;
            }
        }

        var wanted = publicTab;
        if (romajiTab > 0 && isJapanese(tabs[publicTab])) {
            wanted = romajiTab;
        }

        for (var j = 0; j < displays.length; j++) {
            var d = displays[j];
            if (/^screen_/.test(d.id) && Number(d.bible_version_tab) != wanted) {
                h.hly('SetDisplaySettings', { id: d.id, bible_version_tab: wanted });
                h.log('romaji-no-retorno: ' + d.name + ' -> aba ' + wanted
                        + ' (projetor: aba ' + publicTab + ' = ' + tabs[publicTab] + ')');
            }
        }
    } catch (e) {
        h.log('romaji-no-retorno: erro: ' + e);
    }
}, 300, 'romaji-no-retorno');
