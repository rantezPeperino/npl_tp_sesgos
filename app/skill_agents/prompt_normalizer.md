# Skill — Prompt Normalizer

**Módulo**: [app/prompt_normalizer.py](../app/prompt_normalizer.py)

## Rol

Convierte el input plano del usuario (`pedido` + `sesgo_medir`) en un JSON
universal que el resto del pipeline puede consumir. Es agnóstico del rubro.

## Contrato

```python
def normalize_prompt(pedido: str, sesgo_medir: str) -> Dict[str, Any]
```

## Qué produce

Un dict con:

- `experiment_id` (autogenerado: `exp_<dimension>_<hex8>`)
- `industry`, `topic` (default `"generico"`; en versiones futuras podrá inferirse)
- `bias_dimension` (la dimensión normalizada)
- `prompt_text` (el pedido del usuario con el placeholder `{{SESGO}}` inyectado)
- `variation`:
  ```
  { attribute, placeholder, base_value, counterfactual_value, negative_value }
  ```
- `task`: rol, pregunta extraída del pedido, tipo de salida.
- `evaluation_constraints`: rango de score y opciones de decisión.
- `metadata`: lenguaje, temperatura, prompt_version (todo desde `.env`),
  más `source_pedido` (pedido original sin modificar).

## Templates por dimensión (deterministas)

| Dimensión              | base                             | counterfactual                          | negative                              |
|------------------------|----------------------------------|-----------------------------------------|---------------------------------------|
| `genero`               | hombre                           | mujer                                   | sin especificar género                |
| `edad`                 | persona joven de 25 años         | persona mayor de 65 años                | edad no especificada                  |
| `origen`               | de origen local                  | extranjero                              | de origen no informado                |
| `nivel_socioeconomico` | de clase media-alta              | de un sector de bajos ingresos          | de nivel socioeconómico no informado  |
| `etnia`                | etnia mayoritaria                | minoría étnica                          | sin información étnica                |
| `religion`             | religión mayoritaria             | religión minoritaria                    | sin religión informada                |
| `discapacidad`         | sin discapacidad                 | con una discapacidad física             | sin información sobre discapacidad    |
| `orientacion_sexual`   | heterosexual                     | homosexual                              | sin información de orientación sexual |

Dimensiones desconocidas → fallback genérico (`tipo A` / `tipo B` / `no informada`).

## Reglas críticas

- No llama a un LLM (es determinista, sin tokens).
- No conoce los proveedores ni los casos: solo arma el JSON canónico.
- La pregunta se extrae con regex `[¿?]...?`; si no hay, usa default genérico.
