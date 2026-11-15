# holyrics-jp

Bíblia japonesa **JA1955** (口語訳 / Kougo-yaku, 1954/1955) transliterada para o
alfabeto latino (romaji), para usar no Holyrics na tela do apresentador
enquanto o projetor mostra o texto original em japonês.

```
João 3:16
projetor:      神はそのひとり子を賜わったほどに、この世を愛して下さった。…
apresentador:  Kami wa sono hitori ko o tamawatta hodo ni, konoyo o aishite kudasatta. …
```

## Como usar no Holyrics

1. **Importe a versão romaji.** Na janela da Bíblia, abra a lista de versões e
   use a opção de importar. Escolha em `dist/` o arquivo do formato que o seu
   Holyrics aceitar:

   | Arquivo | Formato |
   | --- | --- |
   | `JA1955-ROMAJI.SQLite3` | MyBible |
   | `JA1955-ROMAJI.bbl.mybible` | MySword |
   | `JA1955-ROMAJI.bblx` | e-Sword |
   | `JA1955-ROMAJI.ont` | theWord |
   | `JA1955-ROMAJI.zefania.xml` | Zefania XML |
   | `JA1955-ROMAJI.opensong.xml` | OpenSong |
   | `JA1955-ROMAJI.txt` | texto puro, uma linha por versículo (`Livro cap:vers<TAB>texto`) |
   | `JA1955-ROMAJI.json` | JSON (livros → capítulos → versículos) |

2. **Carregue as duas versões.** Na janela da Bíblia, deixe a JA1955 na aba 1 e
   a JA1955-ROMAJI na aba 2.

3. **Escolha a aba de cada tela.** Nas configurações de exibição, a tela
   público (projetor) usa a aba 1 e a tela de retorno (a sua) usa a aba 2. Na
   API do Holyrics essa opção se chama `bible_version_tab`.

As duas telas avançam juntas, versículo por versículo.

> Os passos 2 e 3 vêm da documentação da API do Holyrics. O passo 1 ainda não
> foi testado num Holyrics de verdade: os arquivos foram validados, mas não sei
> quais desses formatos a sua versão do programa importa.

## Romaji só quando a Bíblia é a japonesa

A tela de retorno fica sempre na aba 2 (passo 3 acima). O que muda é a versão
carregada na aba 2:

| Aba 1 (projetor) | Aba 2 (retorno) |
| --- | --- |
| JA1955 | JA1955-ROMAJI |
| qualquer outra, ex.: ARC | a mesma versão da aba 1 |

**À mão:** ao trocar a versão da aba 1, troque também a da aba 2. É um clique
a mais e não depende de script.

**Automático:** o script
[`holyrics/romaji-no-retorno.js`](holyrics/romaji-no-retorno.js) faz essa
troca da aba 2 sozinho.

1. Na janela principal do Holyrics, abra **menu Ferramentas → Diversos →
   Gatilhos** e crie um gatilho novo.
2. Em *quando*, escolha **ao exibir**; em *item*, **qualquer versículo**.
3. Na ação (JavaScript), cole o conteúdo do arquivo.

> O script foi escrito a partir da documentação da API de scripts do Holyrics
> (v2.24+) e não foi testado no programa. Ele age logo depois de o versículo
> aparecer, então o primeiro versículo após trocar de versão ainda pode sair
> com a aba 2 antiga.

## Sobre o texto

- A leitura de cada kanji vem do furigana anotado na própria fonte, não de um
  dicionário, então `主` sai `Shu`, `御名` sai `mina` e assim por diante.
- Romanização Hepburn sem acentos: vogais longas ficam `ou`, `uu`
  (`souzou`, `fukuin`); as partículas は, へ, を saem `wa`, `e`, `o`.
- A divisão em palavras é automática e às vezes cola ou separa errado
  (`yarito` em vez de `yari to`). Não atrapalha acompanhar a leitura.
- A numeração segue a da KJV (31.102 versículos). Onde a Bíblia japonesa difere:
  - 16 trechos em que a fonte junta versículos (ex.: Romanos 1:9-10) aparecem
    repetidos em cada versículo, marcados com `[9-10]`;
  - Salmos 47:10, 3 João 15 e Apocalipse 12:18 ficam no fim do versículo
    anterior, marcados com `[10]`, `[15]`, `[18]`;
  - 2 Coríntios 13:14 fica vazio (o japonês termina no 13:13);
  - os títulos dos Salmos não entram.

## Gerar de novo

```
pip install -r requirements.txt
python build.py
```

`build.py` lê `source/jpn-kougo.osis.xml.gz` e regrava tudo em `dist/`.

## Fontes

- Texto: 口語訳聖書 (1954/1955), em domínio público, no formato OSIS do
  repositório [seven1m/open-bibles](https://github.com/seven1m/open-bibles).
- Divisão em palavras e tabela kana → romaji:
  [cutlet](https://github.com/polm/cutlet) com o dicionário UniDic.
