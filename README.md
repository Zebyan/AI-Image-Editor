# Image Editor AI

## 1. Prezentare generală

Image Editor AI este un editor de imagini desktop construit în Python cu interfață grafică Qt (PySide6). Aplicația oferă funcții de editare clasică, generare de GIF-uri animate și transfer de stil artistic folosind modele PyTorch.

Arhitectura proiectului este modulară, separând clar:

* interfața grafică (`app/ui`)
* logica de stare și istoric (`app/app_state.py`)
* procesarea imaginilor clasice (`app/process/edit`)
* generarea GIF-urilor (`app/process/gif`)
* transfer de stil (`app/process/style_transfer`)
* servicii și utilitare (`app/services`, `app/utils`)
* worker threads pentru task-uri costisitoare (`app/workers`)

### Tehnologii utilizate

* Python 3.x
* PySide6 / Qt
* OpenCV
* NumPy
* Pillow (PIL)
* PyTorch
* torchvision
* QThread pentru procesare în fundal
* Logging pentru urmărirea evenimentelor

### Obiectiv

Scopul aplicației este să ofere un editor desktop ușor de folosit, cu:

* funcționalități de editare rapidă
* generare și previzualizare GIF
* transfer de stil artistic cu preset-uri
* interfață modulară și extensibilă

---

## 2. Instrucțiuni de instalare și rulare

### Cerințe minime

* Windows 10/11
* Python 3.11+ instalat
* Spațiu liber pe disc pentru modele și imagini
* Acces la internet pentru instalarea pachetelor

### 1. Deschide terminalul în proiect

```powershell
cd "D:\Proiect\Image Editor"
```

### 2. Creează un mediu virtual

```powershell
python -m venv .venv
```

### 3. Activează mediul virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Dacă PowerShell blochează rularea scripturilor:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 4. Instalează dependențele

```powershell
pip install -r requirements.txt
```

Dacă `requirements.txt` nu este disponibil, instalează manual:

```powershell
pip install PySide6 opencv-python numpy pillow torch torchvision
```

### 5. Rulează aplicația

```powershell
python main.py
```

---

## 2.1 Training pentru preset-uri de style transfer

Pentru a antrena un model de stil nou sau pentru a genera preset-urile `Mosaic` și `Sketch`, folosește scriptul de training din directorul `training/style_transfer`.

### Exemplu pentru `Mosaic`

```powershell
cd training/style_transfer
python train_style.py --dataset "path\to\content_images" --style-image "training/style_transfer/styles/mosaic.jpg" --output "models/style_transfer/mosaic.pth" --epochs 2
```

### Exemplu pentru `Sketch`

```powershell
cd training/style_transfer
python train_style.py --dataset "path\to\content_images" --style-image "training/style_transfer/styles/sketch.jpg" --output "models/style_transfer/sketch.pth" --epochs 2
```

### Folosind `--preset-name`

Dacă ai fișiere cu numele implicite `mosaic.jpg` și `sketch.jpg` în `training/style_transfer/styles`, poți apela scriptul astfel:

```powershell
python train_style.py --dataset "path\to\content_images" --preset-name "Mosaic" --epochs 2
python train_style.py --dataset "path\to\content_images" --preset-name "Sketch" --epochs 2
```

Modelul va fi salvat implicit la `models/style_transfer/mosaic.pth` sau `models/style_transfer/sketch.pth`.

---

## 3. Structura proiectului

```text
app/
  __init__.py
  app_state.py
  config.py
  constants.py
  logger.py
  process/
    edit/
    gif/
    style_transfer/
  services/
  ui/
  utils/
  workers/
models/
  style_transfer/
training/
main.py
requirements.txt
```

### Directorul `app/`

* `app/ui/` – componentele Qt care construiesc interfața: fereastră principală, panou de control, vizualizator imagine, dialog GIF, sidebar.
* `app/process/edit/` – funcții de editare clasică: resize, rotate, flip, crop, brightness/contrast, blur.
* `app/process/gif/` – generarea cadrelor GIF și salvarea animațiilor.
* `app/process/style_transfer/` – integrarea modelului pentru stiluri presetate.
* `app/services/` – încărcarea imaginilor și validarea formatelor.
* `app/utils/` – conversii între `QPixmap` și NumPy, utilitare generale.
* `app/workers/` – worker thread pentru rularea task-urilor grele fără blocarea UI.

### Directorul `training/`

* conține cod pentru antrenarea propriilor modele de transfer de stil.
* nu este necesar pentru rularea aplicației, dar oferă referință de extensie.

### Directorul `models/`

* conține modelele de style transfer pre-antrenate (`*.pth`).

---

## 4. Funcționalități principale

### Modul Edit

* Redimensionare imagine
* Rotire cu opțiune de extindere canvass
* Flip orizontal/vertical/both
* Decupare (crop)
* Ajustare brightness / contrast
* Blur Gaussian
* Modul desen cu pensulă

### Modul GIF

* Generare GIF dintr-o imagine încărcată
* Efecte disponibile:
  * Zoom Loop
  * Pan Loop
  * Blur Pulse
* Previziualizare GIF într-un dialog
* Salvare GIF în fișier

### Modul Style Transfer

* Aplicare stil presetat (de exemplu `Van Gogh`)
* Slider pentru intensitate stil
* Suport pregătit pentru încărcare imagine de stil personalizată
* Procesare în fundal pentru a nu bloca UI

### Modul Generative AI

* Structura UI existentă pentru integrarea viitoare a generării text→imagini

---

## 5. Detalii tehnice

### Managementul stării

`app/app_state.py` menține:

* imaginea originală
* imaginea curentă
* previzualizările
* stive Undo/Redo

### Task-uri în background

`app/workers/task_worker.py` rulează procesele grele în `QThread`, astfel UI rămâne receptiv.

### Conversii imagine

`app/utils/convert.py` conține funcții pentru conversia între:

* `QPixmap` și `NumPy`
* `NumPy` și `QPixmap`

Acest lucru permite aplicarea rapidă a transformărilor OpenCV și PyTorch.

---

## 6. Extensii posibile

Posibile îmbunătățiri:

* implementare completă `custom style transfer`
* model text-to-image în modul Generative AI
* suport mai bun pentru GIF-uri animate de intrare
* optimizare performanță pentru imagini mari
* integrare de filtre și efecte suplimentare

---

## 7. GitHub

Acest proiect este gestionat cu Git și are remote configurat către GitHub.

```powershell
git add README.md
git commit -m "Add detailed project documentation"
git push origin HEAD
```
