# Training Style Transfer Models

Acest director conține scripturile necesare pentru antrenarea modelelor de transfer de stil.

## Structura

* `dataset.py` — încarcă imaginile de conținut pentru training.
* `losses.py` — definește pierderile perceptuale și TV.
* `transformer_net.py` — rețeaua de transformare rapidă.
* `utils.py` — utilitare pentru încărcare imagine și salvare model.
* `train_style.py` — scriptul principal de training.

## Cum se antrenează un model de stil

1. Pregătește un set de imagini de conținut într-un director.
2. Alege o imagine de stil (`mosaic.jpg`, `sketch.jpg`, `van_gogh.jpg`).
3. Rulează scriptul cu parametrii necesari.

### Exemple

```powershell
cd training/style_transfer
python train_style.py --dataset "D:\\Datasets\\content" --style-image "training/style_transfer/styles/mosaic.jpg" --output "models/style_transfer/mosaic.pth" --epochs 2
```

```powershell
python train_style.py --dataset "D:\\Datasets\\content" --preset-name "Sketch" --epochs 2
```

## Output

Modelele antrenate se salvează ca fișiere `.pth` în folderul `models/style_transfer`.

## Integrare UI

Numele preset-urilor deja disponibile în aplicație sunt:

* `Van Gogh`
* `Mosaic`
* `Sketch`

Dacă fișierele `models/style_transfer/mosaic.pth` sau `models/style_transfer/sketch.pth` există, aplicația le va încărca automat pentru preseturile respective.
