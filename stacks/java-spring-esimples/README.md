# Stack overlay: Java Spring (e-Simples)

Extensão opcional para projetos com **tenant**, **financeiro**, **Padrão C** (listagem enxuta + filho).

Instalação:

```bash
./install/install.sh /path/esimples-api java-spring-esimples
```

| Artefato | Destino no projeto |
|----------|-------------------|
| `docs/padrao/colecao-filha-vinculada-pai.md` | `docs/padrao/` |
| `docs/padrao/mestre-detalhe-conta-receber.md` | `docs/padrao/` |
| `docs/padrao/carga-faixa-manifest.json` | `docs/padrao/` |
| `docs/validador/revisao.overlay.md` | `docs/validador/revisao.overlay.md` |

No validador, usar `revisao.md` (genérico) + linhas em `revisao.overlay.md` para vizinhos (`ContaPagarService`, etc.).
