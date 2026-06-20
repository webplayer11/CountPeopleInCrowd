# CrowdLens — Crowd Counting Web App

A Flask web application for crowd density estimation and head counting.
Runs with a **mock predictor** until a real model is plugged in.

## Project structure

```
crowd-counting/
├── app.py                   Flask app — routing and I/O only
├── requirements.txt
├── README.md
├── model/
│   ├── __init__.py
│   └── predictor.py         All prediction logic lives here
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/app.js
    ├── uploads/             Saved input images (runtime)
    └── results/             Generated density maps (runtime)
```

## Quick start

```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

## API contract

`POST /analyze`  — multipart form with `image` field

Response JSON:
```json
{
  "count":           312,
  "original_url":    "/static/uploads/<id>.jpg",
  "density_map_url": "/static/results/density_<id>.png",
  "processing_time": 0.043
}
```

## Plugging in a real model

Open `model/predictor.py` and replace **only** `_run_model()`:

```python
def _run_model(image: Image.Image) -> tuple[int, np.ndarray]:
    # image — PIL.Image in RGB mode
    # return: (int count, np.ndarray heatmap_rgb H×W×3 uint8)
    count, heatmap = your_model.infer(image)
    return count, heatmap
```

`app.py`, `index.html`, `style.css`, and `app.js` need **zero changes**.