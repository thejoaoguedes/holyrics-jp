// Romaji na tela de retorno só quando a Bíblia projetada é a japonesa.
//
// Pré-requisito (uma vez, à mão): a tela de retorno configurada para exibir
// a aba 2 da Bíblia; o projetor fica na aba 1.
//
// O script só escolhe o que vai na aba 2, conforme a versão da aba 1:
//   - japonesa (ex.: JA1955): aba 2 = JA1955-ROMAJI;
//   - qualquer outra: aba 2 = a mesma versão da aba 1.
//
// Use como ação de um gatilho "ao exibir > qualquer versículo" (veja o
// README). Ele não mexe nas configurações das telas e roda fora do momento
// da exibição, para não travar a projeção.

h.setTimeout(function () {
    try {
        var settings = h.hly('GetBibleSettings').data;
        var main = settings.tab_version_1;

        // nada mudou desde a última vez: não faz nada
        if (h.getGlobal('romaji_retorno_aba1') == main
                && h.getGlobal('romaji_retorno_aba2') == settings.tab_version_2) {
            return;
        }

        var versions = h.hly('GetBibleVersionsV2').data;
        var romaji = null;
        var mainIsJapanese = false;
        for (var i = 0; i < versions.length; i++) {
            var v = versions[i];
            var isRomaji = /romaji/i.test(v.title + ' ' + v.version);
            if (isRomaji && romaji == null) {
                romaji = v.version;
            }
            if (v.version == main && !isRomaji) {
                mainIsJapanese = (v.language && v.language.iso == 'ja')
                        || /^ja/i.test(v.version);
            }
        }

        var second = (mainIsJapanese && romaji != null) ? romaji : main;
        if (settings.tab_version_2 != second) {
            h.hly('SetBibleSettings', { tab_version_2: second });
        }
        h.setGlobal('romaji_retorno_aba1', main);
        h.setGlobal('romaji_retorno_aba2', second);
    } catch (e) {
        h.log('romaji-no-retorno: ' + e);
    }
}, 300, 'romaji-no-retorno');
