# Validation / Validação

## English

The initial release includes **33 automated tests**, three committed input scenarios and their complete expected reports. The suite checks domain decisions, invalid inputs, reproducibility, HTML embedding, bundle hashes, overwrite refusal, the command line and the real loopback HTTP interface. CI installs the package and runs the same suite on Windows/Linux with Python 3.11/3.13; it also builds a wheel. The example checker compares complete computed reports and the hosted demonstration with committed output.

```bash
python -m unittest discover -s tests -v
python scripts/check_examples.py
python -m pip wheel --no-deps . --wheel-dir dist
```

Browser review covers language switching, real local controls, scenario result changes, printable layout and invalid-input feedback. Source and output data remain visible for independent review. Tests establish software behavior for the included model; they do not establish accessibility conformance, learning gains, clinical outcomes, robot compatibility or field reliability. No user study or physical run has been performed in this repository.

## Português

A versão inicial inclui **33 testes automatizados**, três cenários de entrada publicados e seus relatórios completos esperados. A suíte verifica decisões do domínio, entradas inválidas, reprodução, incorporação HTML, hashes do pacote, recusa de sobrescrita, linha de comando e interface HTTP local real. A integração contínua instala o pacote e executa a mesma suíte em Windows/Linux com Python 3.11/3.13; também constrói uma distribuição wheel. O verificador de exemplos compara relatórios calculados completos e a demonstração publicada com as saídas versionadas.

Use os comandos acima. A revisão no navegador cobre troca de idioma, controles locais reais, alterações dos resultados, apresentação para impressão e retorno de entradas inválidas. Código e saídas permanecem disponíveis para revisão independente. Os testes comprovam comportamento de software para o modelo incluído; não comprovam conformidade de acessibilidade, ganhos de aprendizagem, resultados clínicos, compatibilidade com robô ou confiabilidade de campo. Nenhum estudo com usuários ou execução física foi realizado neste repositório.

[Test source / Código dos testes](../tests) · [Back / Voltar](../README.md)
