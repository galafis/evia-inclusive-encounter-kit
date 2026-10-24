# Guided evidence tour · Visita guiada às evidências

[README](../README.md) · [Validation / Validação](../docs/VALIDATION.md)

## The question · A pergunta

**EN:** What does the record show when a person pauses or declines?

**PT:** O que o registro mostra quando alguém pausa ou recusa?

## First result · Primeiro resultado

The unstarted example remains unstarted regardless of elapsed time. In the paused example, a fictional 90-second encounter contains 30 seconds paused and 60 seconds active, with two cards completed and one skipped. The declined example ends before starting, with no active time. None of these choices is converted into a performance score.

**EN:** These are committed examples of software behavior. Follow the installation and execution commands in the [README](../README.md#english); the source inputs and expected outputs below allow inspection before installation.

**PT:** São exemplos versionados do comportamento do software. Siga a instalação e os comandos do [README](../README.md#portugues); as entradas e saídas abaixo permitem inspecionar o resultado antes de instalar.

## Compare one assumption · Compare uma premissa

**EN:** Compare unstarted, paused and declined examples; inspect active time without assigning a participation score. Keep the original input, change a copy, rerun the implementation and compare the complete output, including warnings and excluded records.

**PT:** Compare os exemplos não iniciado, pausado e recusado; inspecione tempo ativo sem pontuar participação. Preserve a entrada original, altere uma cópia, execute novamente e compare a saída completa, incluindo avisos e registros excluídos.

## Inputs and expected outputs · Entradas e saídas esperadas

| Input · Entrada | Expected output · Saída esperada | Inspect · Inspecione |
| --- | --- | --- |
| [baseline.json](../examples/baseline.json) | [expected/baseline.json](../examples/expected/baseline.json) | Compare the complete record / Compare o registro completo |
| [declined.json](../examples/declined.json) | [expected/declined.json](../examples/expected/declined.json) | Compare the complete record / Compare o registro completo |
| [paused.json](../examples/paused.json) | [expected/paused.json](../examples/expected/paused.json) | Compare the complete record / Compare o registro completo |

## Review the evidence · Revise as evidências

1. **Input / Entrada:** identify units, identifiers and assumptions before interpreting a result. / Identifique unidades, identificadores e premissas antes de interpretar o resultado.
2. **Implementation / Implementação:** follow the domain code linked in the README. / Acompanhe o código de domínio indicado no README.
3. **Output / Saída:** compare both the headline and the complete record. / Compare o destaque e o registro completo.
4. **Checks / Verificações:** read [validation notes](../docs/VALIDATION.md) and the current workflow result. / Leia as [notas de validação](../docs/VALIDATION.md) e o resultado atual da automação.

**EN:** The banner illustrates the workflow; it is not a screenshot. Example values describe the supplied scenarios. They do not establish physical performance, institutional endorsement or an outcome beyond the documented software scope. Domain-specific assumptions and limitations remain in the README and method documents.

**PT:** O banner ilustra o fluxo; não é uma captura de tela. Os valores descrevem os cenários fornecidos. Não estabelecem desempenho físico, endosso institucional ou resultado além do escopo documentado do software. Premissas e limites do domínio permanecem no README e nos documentos de método.
