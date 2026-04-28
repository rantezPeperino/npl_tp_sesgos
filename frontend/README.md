# tiltDetector — Frontend (React MVP)

Frontend React + Vite + Tailwind para consumir la API de tiltDetector.

## Cómo correr

Pre-requisitos: Node 18+ y el backend FastAPI corriendo en `http://localhost:8000`.

```bash
cd frontend
npm install
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173).

> Vite proxea todo `/api/*` → `http://localhost:8000/*`. Si tu backend corre en otro puerto, edita `vite.config.js`.

## Estructura

```
frontend/
├── src/
│   ├── api/tiltApi.js              # wrapper de fetch
│   ├── hooks/useExperiment.js      # estado + persistencia en localStorage
│   ├── components/
│   │   ├── ExperimentForm.jsx      # formulario principal
│   │   ├── ResultsTabs.jsx         # tabs por modelo
│   │   ├── ModelCard.jsx           # tabla + barra de score_gap + conclusión
│   │   ├── CaseDetailDrawer.jsx    # drawer con prompt/raw/normalización
│   │   ├── LLMStatusBadge.jsx      # estado live de los providers
│   │   └── GlobalSummary.jsx       # 3 cards de resumen global
│   ├── pages/
│   │   ├── Home.jsx                # pantalla con formulario
│   │   └── Results.jsx             # pantalla de resultados
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Funcionalidad

- Al cargar la app llama `GET /llm/status` y preselecciona los modelos sanos.
- `POST /experiments/run` con `{pedido, sesgo_medir, model_names}`.
- Los modelos `unhealthy` aparecen deshabilitados con tooltip de error.
- Spinner durante la espera (los LLMs pueden tardar 10-30s).
- Resultado persistido en `localStorage` para sobrevivir a un refresh.
- Tabs por modelo, badge de `bias_intensity` con colores
  (none=gris, low=amarillo, medium=naranja, high=rojo).
- Drawer con prompt enviado, respuesta cruda y normalización por caso
  (BASE / CONTRAFACTUAL / TESTIGO).
