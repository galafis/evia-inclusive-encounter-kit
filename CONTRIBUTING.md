# Contributing / Contribuir

## English

Use synthetic examples and public interfaces. Keep English and Portuguese equivalent. Explain the domain change before adding interface elements. Include a boundary example when changing a decision rule. Do not add hardware claims or private product details.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/build_demo.py
python scripts/check_examples.py
```

`build_demo.py` intentionally rewrites expected reports and `docs/index.html` from the three scenarios. Review those diffs; never use regeneration to hide a failing test. Changing a pinned public dependency requires reviewing its source change and rerunning exchange tests. Open a pull request with the motivation, observed result and limitations.

## Português

Use exemplos sintéticos e interfaces públicas. Mantenha inglês e português equivalentes. Explique a alteração de domínio antes de adicionar elementos de interface. Inclua um exemplo limite ao alterar uma regra de decisão. Não acrescente alegações sobre hardware ou detalhes privados do produto.

Use os comandos acima. `build_demo.py` regrava intencionalmente os relatórios esperados e `docs/index.html` a partir dos três cenários. Revise as diferenças; nunca use a regeneração para ocultar um teste com falha. Alterar dependência pública fixada exige revisar seu código e executar novamente os testes de intercâmbio. Abra uma proposta de alteração com motivação, resultado observado e limitações.
