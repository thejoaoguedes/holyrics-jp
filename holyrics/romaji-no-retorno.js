// Romaji na tela de retorno só quando a Bíblia projetada é a japonesa.
//
// Olha a versão da aba 1 da janela da Bíblia:
//   - japonesa (ex.: JA1955): põe a JA1955-ROMAJI na aba 2 e manda as telas
//     de retorno exibirem a aba 2;
//   - qualquer outra: as telas de retorno voltam a exibir a aba 1, igual ao
//     projetor.
//
// Use como ação de um gatilho "ao exibir > qualquer versículo"
// (veja o README). A tela público nunca é alterada.

function romajiNoRetorno() {
    var versions = h.hly('GetBibleVersionsV2').data;
    var main = h.hly('GetBibleSettings').data.tab_version_1;

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

    var tab = 1;
    if (mainIsJapanese && romaji != null) {
        h.hly('SetBibleSettings', { tab_version_2: romaji });
        tab = 2;
    }

    var displays = h.hly('GetDisplaySettings').data;
    for (var j = 0; j < displays.length; j++) {
        var d = displays[j];
        if (/^screen_/.test(d.id) && d.bible_version_tab != tab) {
            h.hly('SetDisplaySettings', { id: d.id, bible_version_tab: tab });
        }
    }
}

romajiNoRetorno();
