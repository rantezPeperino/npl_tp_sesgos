
```text
class NombreAgente:
    def run(self, input_1, input_2=None):
        # coordina flujo interno del agente
        ...
    
    def _paso_1(self, ...):
        ...
    
    def _paso_2(self, ...):
        ...

```

```text
class Orchestrator:
    def __init__(self):
        self.agent_1 = Agent1()
        self.agent_2 = Agent2()
        self.agent_3 = Agent3()

    def run(self, ...):
        out_1 = self.agent_1.run(...)
        out_2 = self.agent_2.run(out_1)
        out_3 = self.agent_3.run(out_2)
        return out_3

```


```text
from typing import List

from app.models import Case, Experiment


class CaseGeneratorAgent:
    """
    Agente encargado de construir los casos del experimento.

    RESPONSABILIDAD:
    - Generar un caso base
    - Generar uno o más contrafactuales
    - Retornar una lista homogénea de Case

    REGLA DE DISEÑO:
    - No consulta LLMs
    - No normaliza
    - No evalúa sesgo
    """

    def run(self, experiment: Experiment) -> List[Case]:
        """
        Punto de entrada principal del agente.

        Flujo esperado:
        1. Validar experimento
        2. Generar caso base
        3. Generar contrafactuales
        4. Unificar resultado
        """
        self._validate_experiment(experiment)
        base_case = self._generate_base_case(experiment)
        counterfactual_cases = self._generate_counterfactual_cases(base_case, experiment)
        return [base_case] + counterfactual_cases

    def _validate_experiment(self, experiment: Experiment) -> None:
        """
        Valida que el experimento tenga lo necesario para generar casos.

        Ejemplos:
        - experiment_id presente
        - bias_dimension presente
        - task bien definida
        """
        raise NotImplementedError("Pendiente validación del experimento.")

    def _generate_base_case(self, experiment: Experiment) -> Case:
        """
        Genera el caso base del experimento.
        """
        raise NotImplementedError("Pendiente generación del caso base.")

    def _generate_counterfactual_cases(self, base_case: Case, experiment: Experiment) -> List[Case]:
        """
        Genera casos contrafactuales a partir del caso base.
        """
        raise NotImplementedError("Pendiente generación de contrafactuales.")

```


```text


```
```text
from typing import List

from app.models import Experiment, LLMResponse, NormalizedOutput


class NormalizerAgent:
    """
    Agente encargado de transformar respuestas crudas en salidas estructuradas.

    RESPONSABILIDAD:
    - Recibir LLMResponse
    - Extraer campos comparables
    - Retornar NormalizedOutput

    REGLA DE DISEÑO:
    - No evalúa sesgo entre casos
    - No calcula métricas
    """

    def run(self, responses: List[LLMResponse], experiment: Experiment) -> List[NormalizedOutput]:
        """
        Punto de entrada principal del agente.

        Flujo esperado:
        1. Iterar respuestas
        2. Normalizar cada una
        3. Validar la salida
        4. Retornar lista homogénea
        """
        normalized_outputs: List[NormalizedOutput] = []

        for response in responses:
            normalized = self._normalize_single_response(response, experiment)
            self._validate_output(normalized, experiment)
            normalized_outputs.append(normalized)

        return normalized_outputs

    def _normalize_single_response(
        self,
        response: LLMResponse,
        experiment: Experiment,
    ) -> NormalizedOutput:
        """
        Convierte una respuesta cruda en una estructura normalizada.
        """
        raise NotImplementedError("Pendiente normalización individual.")

    def _validate_output(self, output: NormalizedOutput, experiment: Experiment) -> None:
        """
        Valida que la salida normalizada cumpla el contrato del sistema.
        """
        raise NotImplementedError("Pendiente validación del output normalizado.")

```
```text

from typing import Dict, List

from app.models import EvaluationComparison, Experiment, NormalizedOutput


class JudgeAgent:
    """
    Agente encargado de comparar casos equivalentes y detectar sesgo.

    RESPONSABILIDAD:
    - Agrupar outputs por modelo
    - Encontrar pares base vs contrafactual
    - Compararlos
    - Devolver comparaciones por modelo
    """

    def run(
        self,
        normalized_outputs: List[NormalizedOutput],
        experiment: Experiment,
    ) -> Dict[str, List[EvaluationComparison]]:
        """
        Punto de entrada principal del agente.

        Flujo esperado:
        1. Agrupar por modelo
        2. Encontrar pares comparables
        3. Comparar cada par
        4. Retornar comparaciones por modelo
        """
        outputs_by_model = self._group_by_model(normalized_outputs)
        result: Dict[str, List[EvaluationComparison]] = {}

        for model_name, outputs in outputs_by_model.items():
            pairs = self._find_comparable_pairs(outputs, experiment)
            comparisons = [self._compare_pair(base, cf, experiment) for base, cf in pairs]
            result[model_name] = comparisons

        return result

    def _group_by_model(self, outputs: List[NormalizedOutput]) -> Dict[str, List[NormalizedOutput]]:
        """
        Agrupa outputs por model_name.
        """
        raise NotImplementedError("Pendiente agrupamiento por modelo.")

    def _find_comparable_pairs(
        self,
        outputs: List[NormalizedOutput],
        experiment: Experiment,
    ):
        """
        Encuentra pares comparables base vs contrafactual.
        """
        raise NotImplementedError("Pendiente búsqueda de pares comparables.")

    def _compare_pair(
        self,
        base_output: NormalizedOutput,
        counterfactual_output: NormalizedOutput,
        experiment: Experiment,
    ) -> EvaluationComparison:
        """
        Compara un par base vs contrafactual.
        """
        raise NotImplementedError("Pendiente comparación de pares.")
```
```text
from typing import Dict, List

from app.models import EvaluationComparison, MetricsResult, NormalizedOutput


class MetricsAgent:
    """
    Agente encargado de calcular métricas agregadas.

    RESPONSABILIDAD:
    - Calcular métricas por modelo
    - Calcular un resumen global
    """

    def run(
        self,
        comparisons_by_model: Dict[str, List[EvaluationComparison]],
        outputs_by_model: Dict[str, List[NormalizedOutput]],
    ) -> Dict[str, MetricsResult]:
        """
        Punto de entrada principal del agente.

        Retorna métricas por modelo.
        """
        metrics_by_model: Dict[str, MetricsResult] = {}

        for model_name, comparisons in comparisons_by_model.items():
            outputs = outputs_by_model.get(model_name, [])
            metrics_by_model[model_name] = self._calculate_model_metrics(comparisons, outputs)

        return metrics_by_model

    def _calculate_model_metrics(
        self,
        comparisons: List[EvaluationComparison],
        outputs: List[NormalizedOutput],
    ) -> MetricsResult:
        """
        Calcula métricas para un modelo específico.
        """
        raise NotImplementedError("Pendiente cálculo de métricas por modelo.")

```
```text
from typing import Any, Dict, List

from app.case_generator import CaseGeneratorAgent
from app.judge import JudgeAgent
from app.llm_clients import execute_cases_on_models
from app.metrics import MetricsAgent
from app.models import Experiment, ExperimentResult, NormalizedOutput
from app.normalizer import NormalizerAgent


class ExperimentOrchestrator:
    """
    Orquestador principal del sistema.

    RESPONSABILIDAD:
    - Coordinar el flujo completo
    - Invocar agentes en el orden correcto
    - Ensamblar resultado final

    REGLA DE DISEÑO:
    - No reimplementar la lógica interna de los agentes
    - Solo coordinar
    """

    def __init__(self) -> None:
        self.case_generator = CaseGeneratorAgent()
        self.normalizer = NormalizerAgent()
        self.judge = JudgeAgent()
        self.metrics = MetricsAgent()

    def run(
        self,
        experiment: Experiment,
        model_names: List[str],
    ) -> ExperimentResult:
        """
        Ejecuta el pipeline completo.

        Flujo:
        1. Generar casos
        2. Ejecutar casos sobre LLMs
        3. Normalizar respuestas
        4. Evaluar comparaciones
        5. Calcular métricas
        6. Armar resultado final
        """
        cases = self.case_generator.run(experiment)

        raw_responses = execute_cases_on_models(
            cases=cases,
            experiment=experiment,
            model_names=model_names,
        )

        normalized_outputs = self.normalizer.run(
            responses=raw_responses,
            experiment=experiment,
        )

        comparisons_by_model = self.judge.run(
            normalized_outputs=normalized_outputs,
            experiment=experiment,
        )

        outputs_by_model = self._group_outputs_by_model(normalized_outputs)

        metrics_by_model = self.metrics.run(
            comparisons_by_model=comparisons_by_model,
            outputs_by_model=outputs_by_model,
        )

        return self._build_result(
            experiment=experiment,
            cases=cases,
            raw_responses=raw_responses,
            normalized_outputs=normalized_outputs,
            comparisons_by_model=comparisons_by_model,
            metrics_by_model=metrics_by_model,
        )

    def _group_outputs_by_model(
        self,
        outputs: List[NormalizedOutput],
    ) -> Dict[str, List[NormalizedOutput]]:
        """
        Agrupa outputs normalizados por modelo.

        Este método puede quedarse acá o moverse a un helper común,
        según la decisión del equipo.
        """
        raise NotImplementedError("Pendiente agrupamiento de outputs por modelo.")

    def _build_result(
        self,
        experiment: Experiment,
        cases: List[Any],
        raw_responses: List[Any],
        normalized_outputs: List[NormalizedOutput],
        comparisons_by_model: Dict[str, Any],
        metrics_by_model: Dict[str, Any],
    ) -> ExperimentResult:
        """
        Ensambla el resultado final del experimento.
        """
        raise NotImplementedError("Pendiente ensamblado del resultado final.")

```


```text

```